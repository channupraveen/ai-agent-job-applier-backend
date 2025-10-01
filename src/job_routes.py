"""
Job Search & Discovery APIs for AI Job Application Agent
Handles job searching, recommendations, and job data management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import re
from urllib.parse import urlparse

from .models import get_job_db, UserProfile as User
from .auth import get_current_user

router = APIRouter(tags=["Job Search & Discovery"])


def extract_requirements_from_description(description: str, existing_requirements: str) -> str:
    """Extract job requirements from description when structured requirements are empty"""
    if existing_requirements and existing_requirements.strip():
        return existing_requirements
    
    if not description:
        return "Requirements not specified"
    
    # Look for requirement patterns in the description
    requirement_patterns = [
        r'(?i)(?:requirements?|qualifications?|skills?)[:\s]*([^.]*(?:\.[^.]*){0,3})',
        r'(?i)(?:must have|should have|required)[:\s]*([^.]*(?:\.[^.]*){0,2})',
        r'(?i)(?:experience with|knowledge of|proficiency in)[:\s]*([^.]*(?:\.[^.]*){0,2})',
        r'(?i)(?:minimum|preferred)[:\s]+(?:qualifications?|requirements?)[:\s]*([^.]*(?:\.[^.]*){0,2})'
    ]
    
    extracted_requirements = []
    
    for pattern in requirement_patterns:
        matches = re.findall(pattern, description)
        for match in matches:
            if match and len(match.strip()) > 10:  # Only meaningful requirements
                cleaned = match.strip().replace('\n', ' ').replace('  ', ' ')
                if cleaned not in extracted_requirements:
                    extracted_requirements.append(cleaned)
    
    if extracted_requirements:
        return ' | '.join(extracted_requirements[:3])  # Limit to first 3 matches
    
    # Fallback: Look for common tech skills
    tech_skills = [
        'Python', 'JavaScript', 'React', 'Angular', 'Java', 'Node.js', 'SQL',
        'Docker', 'AWS', 'Azure', 'Git', 'TypeScript', 'HTML', 'CSS', 'MongoDB'
    ]
    
    found_skills = []
    desc_lower = description.lower()
    for skill in tech_skills:
        if skill.lower() in desc_lower:
            found_skills.append(skill)
    
    if found_skills:
        return f"Skills: {', '.join(found_skills[:5])}"
    
    return "See job description for requirements"


def calculate_match_score(
    job_description: str, job_requirements: str, user_skills: List[str]
) -> int:
    """Calculate job match score based on user skills and job requirements"""
    if not user_skills:
        return 0

    job_text = f"{job_description} {job_requirements}".lower()
    matches = sum(1 for skill in user_skills if skill.lower() in job_text)
    match_percentage = min(int((matches / len(user_skills)) * 100), 100)

    # Bonus for exact matches in requirements
    bonus = 0
    if job_requirements:
        req_text = job_requirements.lower()
        bonus = sum(
            10 for skill in user_skills if f" {skill.lower()} " in f" {req_text} "
        )


# ===================================
# APPLICATION MANAGEMENT APIs
# ===================================

@router.put("/applications/{application_id}/status")
async def update_application_status(
    application_id: int,
    status_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Update job application status (applied/rejected/interview/offer)"""
    try:
        new_status = status_data.get("status")
        notes = status_data.get("notes", "")
        
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status is required"
            )
        
        # Validate status
        valid_statuses = ["found", "analyzed", "applied", "rejected", "interview", "offer"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Check if job exists
        check_query = "SELECT id, title, company FROM job_applications WHERE id = :job_id"
        existing = db.execute(text(check_query), {"job_id": application_id}).fetchone()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job application not found"
            )
        
        # Update job status
        update_fields = ["status = :status", "updated_at = :updated_at"]
        params = {
            "job_id": application_id,
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        # Set applied_at timestamp if status is 'applied'
        if new_status == "applied":
            update_fields.append("applied_at = :applied_at")
            params["applied_at"] = datetime.utcnow()
        
        # Set response_date if status indicates response
        if new_status in ["rejected", "interview", "offer"]:
            update_fields.append("response_received = true")
        
        update_query = f"""
        UPDATE job_applications 
        SET {', '.join(update_fields)}
        WHERE id = :job_id
        RETURNING id, title, company, status, applied_at
        """
        
        result = db.execute(text(update_query), params)
        updated_job = result.fetchone()
        db.commit()
        
        # Add note if provided
        if notes:
            note_query = """
            INSERT INTO application_notes (job_application_id, note, created_at)
            VALUES (:job_id, :note, :created_at)
            """
            
            note_params = {
                "job_id": application_id,
                "note": f"Status changed to {new_status}: {notes}",
                "created_at": datetime.utcnow()
            }
            
            db.execute(text(note_query), note_params)
            db.commit()
        
        job_dict = dict(updated_job._mapping)
        if job_dict.get("applied_at"):
            job_dict["applied_at"] = job_dict["applied_at"].isoformat()
        
        return {
            "success": True,
            "message": f"Application status updated to {new_status}",
            "application": job_dict
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating application status: {str(e)}"
        )


@router.post("/applications/{application_id}/notes")
async def add_application_note(
    application_id: int,
    note_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Add a note to a job application"""
    try:
        note_text = note_data.get("note")
        
        if not note_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Note text is required"
            )
        
        # Check if job exists
        check_query = "SELECT id, title, company FROM job_applications WHERE id = :job_id"
        existing = db.execute(text(check_query), {"job_id": application_id}).fetchone()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job application not found"
            )
        
        # Insert note
        insert_query = """
        INSERT INTO application_notes (job_application_id, note, created_at, updated_at)
        VALUES (:job_id, :note, :created_at, :updated_at)
        RETURNING id, note, created_at
        """
        
        params = {
            "job_id": application_id,
            "note": note_text,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.execute(text(insert_query), params)
        new_note = result.fetchone()
        db.commit()
        
        note_dict = dict(new_note._mapping)
        note_dict["created_at"] = note_dict["created_at"].isoformat()
        
        return {
            "success": True,
            "message": "Note added successfully",
            "note": note_dict
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding note: {str(e)}"
        )


@router.get("/applications/analytics")
async def get_application_analytics(
    days_back: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get application success metrics and analytics"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Overall application statistics
        stats_query = """
        SELECT 
            COUNT(*) as total_applications,
            COUNT(CASE WHEN status = 'applied' THEN 1 END) as applied_count,
            COUNT(CASE WHEN status = 'interview' THEN 1 END) as interview_count,
            COUNT(CASE WHEN status = 'offer' THEN 1 END) as offer_count,
            COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count,
            COUNT(CASE WHEN response_received = true THEN 1 END) as responses_received,
            AVG(match_score) as avg_match_score
        FROM job_applications
        WHERE created_at >= :start_date
        """
        
        stats_result = db.execute(text(stats_query), {"start_date": start_date})
        overall_stats = dict(stats_result.fetchone()._mapping)
        
        # Success rates calculation
        total_apps = overall_stats.get("total_applications", 0)
        applied_count = overall_stats.get("applied_count", 0)
        interview_count = overall_stats.get("interview_count", 0)
        offer_count = overall_stats.get("offer_count", 0)
        responses = overall_stats.get("responses_received", 0)
        
        success_rates = {
            "application_rate": round((applied_count / max(total_apps, 1)) * 100, 2),
            "response_rate": round((responses / max(applied_count, 1)) * 100, 2),
            "interview_rate": round((interview_count / max(applied_count, 1)) * 100, 2),
            "offer_rate": round((offer_count / max(interview_count, 1)) * 100, 2)
        }
        
        # Daily application trend
        trend_query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as jobs_found,
            COUNT(CASE WHEN applied_at IS NOT NULL THEN 1 END) as jobs_applied,
            COUNT(CASE WHEN status = 'interview' THEN 1 END) as interviews,
            COUNT(CASE WHEN status = 'offer' THEN 1 END) as offers
        FROM job_applications
        WHERE created_at >= :start_date
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
        """
        
        trend_result = db.execute(text(trend_query), {"start_date": start_date})
        daily_trend = [dict(row._mapping) for row in trend_result.fetchall()]
        
        # Top performing companies
        company_query = """
        SELECT 
            company,
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status = 'applied' THEN 1 END) as applied,
            COUNT(CASE WHEN status = 'interview' THEN 1 END) as interviews,
            AVG(match_score) as avg_match_score
        FROM job_applications
        WHERE created_at >= :start_date
        GROUP BY company
        HAVING COUNT(CASE WHEN status = 'applied' THEN 1 END) > 0
        ORDER BY interviews DESC, applied DESC
        LIMIT 10
        """
        
        company_result = db.execute(text(company_query), {"start_date": start_date})
        top_companies = [dict(row._mapping) for row in company_result.fetchall()]
        
        return {
            "success": True,
            "message": f"Analytics for last {days_back} days",
            "period": {
                "days_back": days_back,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            "overall_stats": overall_stats,
            "success_rates": success_rates,
            "daily_trend": daily_trend,
            "top_companies": top_companies,
            "insights": {
                "total_applications": total_apps,
                "best_performing_company": top_companies[0]["company"] if top_companies else None,
                "avg_match_score": round(overall_stats.get("avg_match_score", 0) or 0, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analytics: {str(e)}"
        )


@router.delete("/applications/{application_id}")
async def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Remove a job application record"""
    try:
        # Check if job exists
        check_query = "SELECT id, title, company FROM job_applications WHERE id = :job_id"
        existing = db.execute(text(check_query), {"job_id": application_id}).fetchone()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job application not found"
            )
        
        job_info = dict(existing._mapping)
        
        # Delete associated notes first
        delete_notes_query = "DELETE FROM application_notes WHERE job_application_id = :job_id"
        db.execute(text(delete_notes_query), {"job_id": application_id})
        
        # Delete job application
        delete_query = "DELETE FROM job_applications WHERE id = :job_id"
        db.execute(text(delete_query), {"job_id": application_id})
        db.commit()
        
        return {
            "success": True,
            "message": f"Application '{job_info['title']}' at {job_info['company']} deleted successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting application: {str(e)}"
        )

    return min(match_percentage + bonus, 100)


def get_ai_decision(match_score: int, user_preferences: Dict) -> tuple:
    """AI decision logic for whether to apply to a job"""
    if match_score >= 80:
        return (
            "apply",
            f"Excellent match ({match_score}% compatibility) - strongly recommended",
        )
    elif match_score >= 60:
        return "maybe", f"Good match ({match_score}% compatibility) - worth considering"
    elif match_score >= 40:
        return (
            "maybe",
            f"Moderate match ({match_score}% compatibility) - review carefully",
        )
    else:
        return "skip", f"Low match ({match_score}% compatibility) - not recommended"


@router.post("/search")
async def search_jobs(
    search_request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Advanced job search with AI filtering and recommendations"""
    try:
        # Extract search parameters
        keywords = search_request.get("keywords", "")
        company = search_request.get("company", "")
        location = search_request.get("location", "")
        status_filter = search_request.get("status", "")
        min_match_score = search_request.get("min_match_score", 0)
        applied_only = search_request.get("applied_only", False)
        skip = search_request.get("skip", 0)
        limit = search_request.get("limit", 50)

        # Build search query
        base_query = """
        SELECT 
            ja.id, ja.title, ja.company, ja.location, ja.url, ja.description,
            ja.requirements, ja.salary_range, ja.status, ja.applied_at,
            ja.response_received, ja.response_date, ja.match_score, ja.ai_decision,
            ja.ai_reasoning, ja.created_at, ja.updated_at, ja.source
        FROM job_applications ja
        WHERE 1=1
        """

        params = {}
        conditions = []

        # Apply filters
        if keywords:
            keywords_condition = """
            (LOWER(ja.title) LIKE LOWER(:keywords) 
             OR LOWER(ja.description) LIKE LOWER(:keywords)
             OR LOWER(ja.requirements) LIKE LOWER(:keywords))
            """
            conditions.append(keywords_condition)
            params["keywords"] = f"%{keywords}%"

        if company:
            conditions.append("LOWER(ja.company) LIKE LOWER(:company)")
            params["company"] = f"%{company}%"

        if location:
            conditions.append("LOWER(ja.location) LIKE LOWER(:location)")
            params["location"] = f"%{location}%"

        if status_filter:
            conditions.append("ja.status = :status")
            params["status"] = status_filter

        if min_match_score:
            conditions.append("ja.match_score >= :min_match_score")
            params["min_match_score"] = min_match_score

        if applied_only:
            conditions.append("ja.applied_at IS NOT NULL")

        # Add conditions to query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as count_subquery"
        count_result = db.execute(text(count_query), params).fetchone()
        total = count_result[0] if count_result else 0

        # Add pagination
        final_query = f"""
        {base_query}
        ORDER BY ja.created_at DESC
        LIMIT :limit OFFSET :skip
        """

        params.update({"limit": limit, "skip": skip})

        # Execute search
        result = db.execute(text(final_query), params)
        jobs_data = result.fetchall()

        # Convert to job objects
        jobs = []
        for row in jobs_data:
            job_dict = dict(row._mapping)
            
            # Improve requirements field
            job_dict['requirements'] = extract_requirements_from_description(
                job_dict.get('description', ''), 
                job_dict.get('requirements', '')
            )
            
            # Format datetime fields
            for date_field in [
                "applied_at",
                "response_date",
                "created_at",
                "updated_at",
            ]:
                if job_dict.get(date_field):
                    job_dict[date_field] = job_dict[date_field].isoformat()
            jobs.append(job_dict)

        # Calculate stats
        stats = {
            "total_found": total,
            "applied_count": len([j for j in jobs if j.get("applied_at")]),
            "high_match_count": len([j for j in jobs if j.get("match_score", 0) >= 80]),
            "recommended_count": len(
                [j for j in jobs if j.get("ai_decision") == "apply"]
            ),
        }

        return {
            "jobs": jobs,
            "total": total,
            "skip": skip,
            "limit": limit,
            "stats": stats,
            "success": True,
            "message": f"Found {len(jobs)} jobs matching your criteria",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching jobs: {str(e)}",
        )


@router.get("/jobs/{job_id}")
async def get_job_details(
    job_id: int,
    include_similar: bool = Query(
        False, description="Include similar job recommendations"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get detailed information about a specific job"""
    try:
        # Get job details
        job_query = """
        SELECT 
            ja.id, ja.title, ja.company, ja.location, ja.url, ja.description,
            ja.requirements, ja.salary_range, ja.status, ja.applied_at,
            ja.response_received, ja.response_date, ja.match_score, ja.ai_decision,
            ja.ai_reasoning, ja.created_at, ja.updated_at, ja.source
        FROM job_applications ja
        WHERE ja.id = :job_id
        """

        result = db.execute(text(job_query), {"job_id": job_id})
        job_row = result.fetchone()

        if not job_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )

        job_dict = dict(job_row._mapping)

        # Format datetime fields
        for date_field in ["applied_at", "response_date", "created_at", "updated_at"]:
            if job_dict.get(date_field):
                job_dict[date_field] = job_dict[date_field].isoformat()

        # Get cover letter if exists
        cover_letter_query = """
        SELECT content, ai_generated, template_used, created_at
        FROM cover_letters
        WHERE job_application_id = :job_id
        ORDER BY created_at DESC
        LIMIT 1
        """

        cover_result = db.execute(text(cover_letter_query), {"job_id": job_id})
        cover_row = cover_result.fetchone()

        cover_letter = None
        if cover_row:
            cover_dict = dict(cover_row._mapping)
            cover_dict["created_at"] = cover_dict["created_at"].isoformat()
            cover_letter = cover_dict

        # Get similar jobs if requested
        similar_jobs = []
        if include_similar and job_dict.get("company"):
            similar_query = """
            SELECT id, title, company, match_score, ai_decision
            FROM job_applications
            WHERE company = :company AND id != :job_id
            ORDER BY match_score DESC
            LIMIT 5
            """

            similar_result = db.execute(
                text(similar_query), {"company": job_dict["company"], "job_id": job_id}
            )
            similar_jobs = [dict(row._mapping) for row in similar_result.fetchall()]

        return {
            "job": job_dict,
            "cover_letter": cover_letter,
            "similar_jobs": similar_jobs,
            "success": True,
            "message": "Job details retrieved successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job details: {str(e)}",
        )


@router.post("/bulk-import")


async def bulk_import_jobs(
    import_request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Import jobs from multiple sources (CSV, API, web scraping)"""
    try:
        jobs_data = import_request.get("jobs", [])
        source_info = import_request.get("source_info", {})

        if not jobs_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No jobs provided for import",
            )

        # Get user skills for match scoring
        user_skills = [
            "Python",
            "JavaScript",
            "React",
            "FastAPI",
            "PostgreSQL",
        ]  # Default skills

        imported_jobs = []
        errors = []

        # Process each job
        for job_data in jobs_data:
            try:
                # Check if job already exists
                if job_data.get("url"):
                    existing_query = "SELECT id FROM job_applications WHERE url = :url"
                    existing = db.execute(
                        text(existing_query), {"url": job_data["url"]}
                    ).fetchone()
                    if existing:
                        errors.append(
                            f"Job already exists: {job_data.get('title', 'Unknown')}"
                        )
                        continue

                # Calculate match score
                match_score = calculate_match_score(
                    job_data.get("description", ""),
                    job_data.get("requirements", ""),
                    user_skills,
                )

                # Get AI decision
                ai_decision, ai_reasoning = get_ai_decision(match_score, {})
                
                # Extract enhanced requirements
                enhanced_requirements = extract_requirements_from_description(
                    job_data.get("description", ""),
                    job_data.get("requirements", "")
                )

                # Insert job
                insert_query = """
                INSERT INTO job_applications (
                    title, company, location, url, description, requirements,
                    salary_range, status, match_score, ai_decision, ai_reasoning,
                    created_at, updated_at
                ) VALUES (
                    :title, :company, :location, :url, :description, :requirements,
                    :salary_range, 'found', :match_score, :ai_decision, :ai_reasoning,
                    :created_at, :updated_at
                ) RETURNING id, title, company, match_score, ai_decision
                """

                params = {
                    "title": job_data.get("title", ""),
                    "company": job_data.get("company", ""),
                    "location": job_data.get("location", ""),
                    "url": job_data.get("url"),
                    "description": job_data.get("description", ""),
                    "requirements": enhanced_requirements,  # Use enhanced requirements
                    "salary_range": job_data.get("salary_range", ""),
                    "match_score": match_score,
                    "ai_decision": ai_decision,
                    "ai_reasoning": ai_reasoning,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }

                result = db.execute(text(insert_query), params)
                job_row = result.fetchone()

                if job_row:
                    imported_jobs.append(dict(job_row._mapping))

            except Exception as job_error:
                errors.append(
                    f"Error importing job '{job_data.get('title', 'Unknown')}': {str(job_error)}"
                )

        db.commit()

        return {
            "success": True,
            "message": f"Successfully imported {len(imported_jobs)} jobs",
            "imported_count": len(imported_jobs),
            "error_count": len(errors),
            "imported_jobs": imported_jobs,
            "errors": errors,
            "source_info": source_info,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing jobs: {str(e)}",
        )


@router.get("/recommendations")
async def get_job_recommendations(
    limit: int = Query(20, ge=1, le=100),
    match_threshold: int = Query(60, ge=0, le=100),
    exclude_applied: bool = Query(True, description="Exclude already applied jobs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get AI-powered job recommendations based on user profile"""
    try:
        # Build recommendation query
        base_query = """
        SELECT 
            ja.id, ja.title, ja.company, ja.location, ja.url,
            ja.description, ja.requirements, ja.salary_range,
            ja.match_score, ja.ai_decision, ja.ai_reasoning,
            ja.status, ja.applied_at, ja.created_at, ja.is_saved,
            ja.job_type, ja.experience_level, ja.company_logo, ja.source
        FROM job_applications ja
        WHERE ja.match_score >= :match_threshold
        """

        params = {"match_threshold": match_threshold}
        conditions = []

        # Exclude applied jobs if requested
        if exclude_applied:
            conditions.append("ja.applied_at IS NULL")

        # Add conditions
        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        # Add sorting and limit
        final_query = f"""
        {base_query}
        ORDER BY ja.match_score DESC, ja.created_at DESC
        LIMIT :limit
        """

        params["limit"] = limit

        # Execute query
        result = db.execute(text(final_query), params)
        jobs_data = result.fetchall()

        # Convert to recommendations
        recommendations = []
        for row in jobs_data:
            job_dict = dict(row._mapping)

            # Format datetime fields
            for date_field in ["applied_at", "created_at"]:
                if job_dict.get(date_field):
                    job_dict[date_field] = job_dict[date_field].isoformat()

            # Add recommendation reason
            match_score = job_dict.get("match_score", 0)
            if match_score >= 90:
                reason = "🎯 Perfect match for your skills and experience"
            elif match_score >= 80:
                reason = "✨ Excellent match - highly recommended"
            elif match_score >= 70:
                reason = "👍 Very good match for your profile"
            else:
                reason = "📋 Good match worth considering"

            job_dict["recommendation_reason"] = reason
            job_dict["priority"] = (
                "high"
                if match_score >= 80
                else "medium" if match_score >= 60 else "low"
            )

            recommendations.append(job_dict)

        return {
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "success": True,
            "message": f"Generated {len(recommendations)} personalized job recommendations",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}",
        )


@router.get("/recommendations/detailed")
async def get_detailed_recommendations(
    limit: int = Query(20, ge=1, le=100),
    match_threshold: int = Query(60, ge=0, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get detailed job recommendations with match reasons and skill analysis"""
    try:
        # Get user skills from profile
        user_query = "SELECT skills FROM user_profiles WHERE id = :user_id"
        user_result = db.execute(text(user_query), {"user_id": current_user.id})
        user_row = user_result.fetchone()
        
        user_skills = []
        if user_row and user_row[0]:
            try:
                import json
                user_skills = json.loads(user_row[0]) if isinstance(user_row[0], str) else user_row[0]
            except:
                user_skills = []
        
        # Get recommendations
        jobs_query = """
        SELECT 
            id, title, company, location, url, description, requirements,
            salary_range, match_score, ai_decision, ai_reasoning,
            status, created_at, is_saved, job_type, experience_level, company_logo, source
        FROM job_applications
        WHERE match_score >= :match_threshold
        AND applied_at IS NULL
        ORDER BY match_score DESC, created_at DESC
        LIMIT :limit
        """
        
        result = db.execute(text(jobs_query), {
            "match_threshold": match_threshold,
            "limit": limit
        })
        jobs_data = result.fetchall()
        
        detailed_recommendations = []
        for row in jobs_data:
            job = dict(row._mapping)
            
            # Analyze skills match
            job_requirements = (job.get("requirements") or "").lower()
            skills_matched = []
            skills_missing = []
            
            # Common tech skills to check
            all_skills = set(user_skills + [
                "Python", "JavaScript", "React", "Node.js", "Java", "C++",
                "SQL", "AWS", "Docker", "Kubernetes", "Git", "TypeScript",
                "Angular", "Vue", "MongoDB", "PostgreSQL", "Redis",
                "GraphQL", "REST API", "Microservices"
            ])
            
            for skill in all_skills:
                if skill.lower() in job_requirements:
                    if skill in user_skills:
                        skills_matched.append(skill)
                    else:
                        skills_missing.append(skill)
            
            # Generate match reasons
            match_reasons = []
            match_score = job.get("match_score", 0)
            
            if match_score >= 90:
                match_reasons.append("Exceptional match - Top 10% of all opportunities")
            elif match_score >= 80:
                match_reasons.append("Excellent alignment with your profile")
            elif match_score >= 70:
                match_reasons.append("Strong match with your skills and experience")
            
            if len(skills_matched) >= 5:
                match_reasons.append(f"{len(skills_matched)} of your skills match job requirements")
            elif len(skills_matched) >= 3:
                match_reasons.append(f"{len(skills_matched)} key skills aligned")
            
            if job.get("location") and "remote" in job.get("location", "").lower():
                match_reasons.append("Remote work opportunity")
            
            if job.get("salary_range"):
                match_reasons.append("Salary range specified")
            
            # Format response
            detailed_job = {
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job.get("location"),
                "url": job.get("url"),
                "description": job.get("description"),
                "requirements": job.get("requirements"),
                "salary_range": job.get("salary_range"),
                "match_score": match_score,
                "ai_reasoning": job.get("ai_reasoning"),
                "posted_date": job["created_at"].isoformat() if job.get("created_at") else None,
                "company_logo": job.get("company_logo"),
                "job_type": job.get("job_type"),
                "experience_level": job.get("experience_level"),
                "source": job.get("source"),
                "skills_matched": skills_matched[:10],  # Limit to top 10
                "skills_missing": skills_missing[:5],   # Limit to top 5
                "match_reasons": match_reasons,
                "is_saved": job.get("is_saved", False),
                "is_applied": job.get("status") == "applied"
            }
            
            detailed_recommendations.append(detailed_job)
        
        return {
            "success": True,
            "recommendations": detailed_recommendations,
            "total_recommendations": len(detailed_recommendations),
            "message": f"Found {len(detailed_recommendations)} detailed recommendations"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating detailed recommendations: {str(e)}"
        )


@router.get("/recommendations/stats")
async def get_recommendation_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get recommendation statistics and insights"""
    try:
        # Get user skills
        user_query = "SELECT skills FROM user_profiles WHERE id = :user_id"
        user_result = db.execute(text(user_query), {"user_id": current_user.id})
        user_row = user_result.fetchone()
        
        user_skills = []
        if user_row and user_row[0]:
            try:
                import json
                user_skills = json.loads(user_row[0]) if isinstance(user_row[0], str) else user_row[0]
            except:
                user_skills = []
        
        # Get recommendation stats
        stats_query = """
        SELECT 
            COUNT(*) as total_recommendations,
            COUNT(CASE WHEN match_score >= 85 THEN 1 END) as excellent_matches,
            COUNT(CASE WHEN match_score >= 70 AND match_score < 85 THEN 1 END) as good_matches,
            AVG(match_score) as average_match_score,
            COUNT(CASE WHEN applied_at IS NULL THEN 1 END) as unapplied_count
        FROM job_applications
        WHERE match_score >= 60
        """
        
        result = db.execute(text(stats_query))
        stats = dict(result.fetchone()._mapping)
        
        # Get top skill matches from job requirements
        skills_query = """
        SELECT requirements
        FROM job_applications
        WHERE match_score >= 70
        AND requirements IS NOT NULL
        LIMIT 50
        """
        
        skills_result = db.execute(text(skills_query))
        all_requirements = [row[0] for row in skills_result.fetchall() if row[0]]
        
        # Count skill occurrences
        skill_counts = {}
        for skill in user_skills:
            count = sum(1 for req in all_requirements if skill.lower() in req.lower())
            if count > 0:
                skill_counts[skill] = count
        
        # Get top 5 most demanded skills from user's skillset
        top_skill_matches = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_skills = [skill for skill, count in top_skill_matches]
        
        return {
            "success": True,
            "stats": {
                "total_recommendations": stats.get("total_recommendations", 0),
                "excellent_matches": stats.get("excellent_matches", 0),
                "good_matches": stats.get("good_matches", 0),
                "average_match_score": round(stats.get("average_match_score", 0) or 0, 1),
                "unapplied_count": stats.get("unapplied_count", 0),
                "top_skill_matches": top_skills
            },
            "message": "Recommendation statistics retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving recommendation stats: {str(e)}"
        )


@router.post("/analyze")
async def analyze_job_market(
    analysis_request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Analyze job market trends and opportunities"""
    try:
        days_back = analysis_request.get("days_back", 30)
        start_date = datetime.utcnow() - timedelta(days=days_back)

        # Market analysis query
        market_query = """
        SELECT 
            company,
            COUNT(*) as job_count,
            AVG(match_score) as avg_match_score,
            COUNT(CASE WHEN ai_decision = 'apply' THEN 1 END) as recommended_jobs,
            COUNT(CASE WHEN applied_at IS NOT NULL THEN 1 END) as applied_jobs
        FROM job_applications
        WHERE created_at >= :start_date
        GROUP BY company
        ORDER BY job_count DESC
        LIMIT 20
        """

        market_result = db.execute(text(market_query), {"start_date": start_date})
        company_analysis = [dict(row._mapping) for row in market_result.fetchall()]

        # Overall statistics
        stats_query = """
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN ai_decision = 'apply' THEN 1 END) as recommended_jobs,
            COUNT(CASE WHEN applied_at IS NOT NULL THEN 1 END) as applied_jobs,
            AVG(match_score) as avg_match_score,
            MAX(match_score) as best_match_score
        FROM job_applications
        WHERE created_at >= :start_date
        """

        stats_result = db.execute(text(stats_query), {"start_date": start_date})
        overall_stats = dict(stats_result.fetchone()._mapping)

        return {
            "success": True,
            "message": f"Market analysis completed for last {days_back} days",
            "analysis_period": {
                "days_back": days_back,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
            },
            "company_analysis": company_analysis,
            "overall_stats": overall_stats,
            "insights": {
                "most_active_company": (
                    company_analysis[0]["company"] if company_analysis else None
                ),
                "recommendation_rate": round(
                    (
                        overall_stats.get("recommended_jobs", 0)
                        / max(overall_stats.get("total_jobs", 1), 1)
                    )
                    * 100,
                    1,
                ),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing job market: {str(e)}",
        )


# ===================================
# NEW APIS FOR JOB LIST COMPONENT
# ===================================

@router.get("/jobs/stats")
async def get_job_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get job statistics for dashboard cards"""
    try:
        stats_query = """
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status = 'found' THEN 1 END) as found_jobs,
            COUNT(CASE WHEN status = 'applied' THEN 1 END) as applied_jobs,
            COUNT(CASE WHEN status = 'interview' THEN 1 END) as interview_jobs,
            COUNT(CASE WHEN status = 'offer' THEN 1 END) as offer_jobs,
            COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_jobs,
            COUNT(CASE WHEN is_saved = true THEN 1 END) as saved_jobs,
            AVG(match_score) as avg_match_score
        FROM job_applications
        """
        
        result = db.execute(text(stats_query))
        stats = dict(result.fetchone()._mapping)
        
        return {
            "success": True,
            "stats": {
                "total_jobs": stats.get("total_jobs", 0),
                "found_jobs": stats.get("found_jobs", 0),
                "applied_jobs": stats.get("applied_jobs", 0),
                "interview_jobs": stats.get("interview_jobs", 0),
                "offer_jobs": stats.get("offer_jobs", 0),
                "rejected_jobs": stats.get("rejected_jobs", 0),
                "saved_jobs": stats.get("saved_jobs", 0),
                "avg_match_score": round(stats.get("avg_match_score", 0) or 0, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job statistics: {str(e)}"
        )


@router.post("/jobs/{job_id}/save")
async def toggle_save_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Toggle save/bookmark status of a job"""
    try:
        # Check if job exists and get current save status
        check_query = "SELECT id, title, company, is_saved FROM job_applications WHERE id = :job_id"
        existing = db.execute(text(check_query), {"job_id": job_id}).fetchone()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job_info = dict(existing._mapping)
        current_save_status = job_info.get("is_saved", False)
        new_save_status = not current_save_status
        
        # Update save status
        update_query = """
        UPDATE job_applications 
        SET is_saved = :is_saved, updated_at = :updated_at
        WHERE id = :job_id
        RETURNING id, title, company, is_saved
        """
        
        params = {
            "job_id": job_id,
            "is_saved": new_save_status,
            "updated_at": datetime.utcnow()
        }
        
        result = db.execute(text(update_query), params)
        updated_job = result.fetchone()
        db.commit()
        
        job_dict = dict(updated_job._mapping)
        
        return {
            "success": True,
            "message": f"Job {'saved' if new_save_status else 'unsaved'} successfully",
            "job": job_dict,
            "is_saved": new_save_status
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling save status: {str(e)}"
        )


@router.get("/jobs")
async def list_all_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    is_saved: Optional[bool] = Query(None),
    min_match_score: Optional[int] = Query(None, ge=0, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|match_score|title|company)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """List all jobs with optional filters and pagination"""
    try:
        # Build query
        base_query = """
        SELECT 
            id, title, company, location, url, description, requirements,
            salary_range, status, applied_at, response_received, response_date,
            match_score, ai_decision, ai_reasoning, is_saved, created_at, updated_at, source
        FROM job_applications
        WHERE 1=1
        """
        
        params = {}
        conditions = []
        
        # Apply filters
        if status:
            conditions.append("status = :status")
            params["status"] = status
        
        if is_saved is not None:
            conditions.append("is_saved = :is_saved")
            params["is_saved"] = is_saved
        
        if min_match_score is not None:
            conditions.append("match_score >= :min_match_score")
            params["min_match_score"] = min_match_score
        
        # Add conditions to query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as count_subquery"
        count_result = db.execute(text(count_query), params).fetchone()
        total = count_result[0] if count_result else 0
        
        # Add sorting and pagination
        final_query = f"""
        {base_query}
        ORDER BY {sort_by} {sort_order}
        LIMIT :limit OFFSET :skip
        """
        
        params.update({"limit": limit, "skip": skip})
        
        # Execute query
        result = db.execute(text(final_query), params)
        jobs_data = result.fetchall()
        
        # Convert to job objects
        jobs = []
        for row in jobs_data:
            job_dict = dict(row._mapping)
            
            # Format datetime fields
            for date_field in ["applied_at", "response_date", "created_at", "updated_at"]:
                if job_dict.get(date_field):
                    job_dict[date_field] = job_dict[date_field].isoformat()
            
            jobs.append(job_dict)
        
        return {
            "success": True,
            "jobs": jobs,
            "total": total,
            "skip": skip,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "message": f"Retrieved {len(jobs)} jobs"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing jobs: {str(e)}"
        )


@router.post("/jobs/{job_id}/apply")
async def quick_apply_to_job(
    job_id: int,
    apply_data: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Quick apply to a job - updates status to 'applied'"""
    try:
        # Check if job exists
        check_query = "SELECT id, title, company, status FROM job_applications WHERE id = :job_id"
        existing = db.execute(text(check_query), {"job_id": job_id}).fetchone()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job_info = dict(existing._mapping)
        
        # Check if already applied
        if job_info.get("status") == "applied":
            return {
                "success": True,
                "message": f"Already applied to {job_info['title']} at {job_info['company']}",
                "already_applied": True
            }
        
        # Update to applied status
        update_query = """
        UPDATE job_applications 
        SET status = 'applied', applied_at = :applied_at, updated_at = :updated_at
        WHERE id = :job_id
        RETURNING id, title, company, status, applied_at
        """
        
        params = {
            "job_id": job_id,
            "applied_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.execute(text(update_query), params)
        updated_job = result.fetchone()
        db.commit()
        
        # Add application note if provided
        note = apply_data.get("note")
        if note:
            note_query = """
            INSERT INTO application_notes (job_application_id, note, created_at, updated_at)
            VALUES (:job_id, :note, :created_at, :updated_at)
            """
            
            note_params = {
                "job_id": job_id,
                "note": note,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            db.execute(text(note_query), note_params)
            db.commit()
        
        job_dict = dict(updated_job._mapping)
        if job_dict.get("applied_at"):
            job_dict["applied_at"] = job_dict["applied_at"].isoformat()
        
        return {
            "success": True,
            "message": f"Successfully applied to {job_dict['title']} at {job_dict['company']}",
            "job": job_dict,
            "already_applied": False
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying to job: {str(e)}"
        )


# ===================================
# APPLICATIONS ENDPOINT (NEW)
# ===================================

@router.get("/applications")
async def list_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    min_match_score: Optional[int] = Query(None, ge=0, le=100),
    sort_by: str = Query("applied_at", regex="^(applied_at|created_at|match_score|title|company)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None),
    response_received: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """List job applications - ONLY jobs where user has applied"""
    try:
        # Build query - filter for ACTUAL APPLICATIONS
        base_query = """
        SELECT 
            id, title, company, location, url, description, requirements,
            salary_range, status, applied_at, response_received, response_date,
            match_score, ai_decision, ai_reasoning, is_saved, created_at, updated_at, source
        FROM job_applications
        WHERE (status IN ('applied', 'interview', 'offer', 'rejected') OR applied_at IS NOT NULL)
        """
        
        params = {}
        conditions = []
        
        # Additional filters
        if status:
            conditions.append("status = :status")
            params["status"] = status
        
        if min_match_score is not None:
            conditions.append("match_score >= :min_match_score")
            params["min_match_score"] = min_match_score
        
        if response_received is not None:
            conditions.append("response_received = :response_received")
            params["response_received"] = response_received
        
        if search:
            conditions.append(
                "(LOWER(title) LIKE LOWER(:search) OR LOWER(company) LIKE LOWER(:search))"
            )
            params["search"] = f"%{search}%"
        
        # Add conditions to query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as count_subquery"
        count_result = db.execute(text(count_query), params).fetchone()
        total = count_result[0] if count_result else 0
        
        # Add sorting and pagination
        final_query = f"""
        {base_query}
        ORDER BY {sort_by} {sort_order}
        LIMIT :limit OFFSET :skip
        """
        
        params.update({"limit": limit, "skip": skip})
        
        # Execute query
        result = db.execute(text(final_query), params)
        applications_data = result.fetchall()
        
        # Convert to application objects
        applications = []
        for row in applications_data:
            app_dict = dict(row._mapping)
            
            # Format datetime fields
            for date_field in ["applied_at", "response_date", "created_at", "updated_at"]:
                if app_dict.get(date_field):
                    app_dict[date_field] = app_dict[date_field].isoformat()
            
            applications.append(app_dict)
        
        return {
            "success": True,
            "applications": applications,
            "total": total,
            "skip": skip,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "message": f"Retrieved {len(applications)} applications"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing applications: {str(e)}"
        )
