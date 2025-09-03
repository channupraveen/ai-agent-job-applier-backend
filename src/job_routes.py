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

from models import get_job_db, UserProfile as User
from auth import get_current_user

router = APIRouter(tags=["Job Search & Discovery"])


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
            ja.ai_reasoning, ja.created_at, ja.updated_at
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


@router.get("/{job_id}")
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
            ja.ai_reasoning, ja.created_at, ja.updated_at
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
                    "requirements": job_data.get("requirements", ""),
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
            ja.status, ja.applied_at, ja.created_at
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
