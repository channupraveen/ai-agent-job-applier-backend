"""
Cover Letter Generation API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from .models import get_job_db, UserProfile as User
from .auth import get_current_user
from .services.ai_service import AIService

cover_letter_router = APIRouter(tags=["Cover Letters"])
ai_service = AIService()


@cover_letter_router.post("/cover-letters/generate")
async def generate_cover_letter(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Generate AI-powered cover letter for specific job"""
    try:
        job_id = request_data.get("job_id")
        job_title = request_data.get("job_title", "")
        company = request_data.get("company", "")
        job_description = request_data.get("job_description", "")
        template_id = request_data.get("template_id")

        if not job_title or not company:
            raise HTTPException(
                status_code=400, detail="job_title and company are required"
            )

        # Get job details if job_id provided
        if job_id:
            job_query = """
            SELECT title, company, description, requirements 
            FROM job_applications 
            WHERE id = :job_id
            """
            job_result = db.execute(text(job_query), {"job_id": job_id})
            job_row = job_result.fetchone()

            if job_row:
                job_data = dict(job_row._mapping)
                job_title = job_data["title"]
                company = job_data["company"]
                job_description = job_data.get("description", "")

        # Get user profile data
        user_data = {
            "name": current_user.name or "Job Seeker",
            "skills": json.loads(current_user.skills or "[]"),
            "experience_years": current_user.experience_years or 0,
            "current_title": current_user.current_title or "",
        }

        # Generate cover letter using AI
        cover_letter_content = await ai_service.generate_cover_letter(
            {"title": job_title, "company": company, "description": job_description},
            user_data,
        )

        # Save to database
        insert_query = """
        INSERT INTO cover_letters (
            job_application_id, content, ai_generated, 
            template_used, created_at
        ) VALUES (
            :job_id, :content, true, :template_used, :created_at
        ) RETURNING id, content, created_at
        """

        params = {
            "job_id": job_id,
            "content": cover_letter_content,
            "template_used": (
                f"ai_template_{template_id}" if template_id else "default_ai"
            ),
            "created_at": datetime.utcnow(),
        }

        result = db.execute(text(insert_query), params)
        new_cover_letter = result.fetchone()
        db.commit()

        cover_letter_dict = dict(new_cover_letter._mapping)
        cover_letter_dict["created_at"] = cover_letter_dict["created_at"].isoformat()

        return {
            "success": True,
            "message": "Cover letter generated successfully",
            "cover_letter": cover_letter_dict,
            "job_title": job_title,
            "company": company,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error generating cover letter: {str(e)}"
        )


@cover_letter_router.get("/cover-letters/templates")
async def get_cover_letter_templates(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_job_db)
):
    """Get available cover letter templates"""
    try:
        # Built-in templates
        builtin_templates = [
            {
                "id": "professional",
                "name": "Professional",
                "description": "Formal and professional tone",
                "preview": "Dear Hiring Manager, I am writing to express my strong interest...",
            },
            {
                "id": "creative",
                "name": "Creative",
                "description": "Creative and engaging approach",
                "preview": "Hello [Company] team! I'm excited about the opportunity to...",
            },
            {
                "id": "technical",
                "name": "Technical",
                "description": "Focus on technical skills and experience",
                "preview": "As a software developer with expertise in...",
            },
            {
                "id": "startup",
                "name": "Startup",
                "description": "Casual tone suitable for startups",
                "preview": "Hi there! I came across your job posting and...",
            },
        ]

        return {
            "success": True,
            "templates": builtin_templates,
            "total": len(builtin_templates),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting templates: {str(e)}"
        )


@cover_letter_router.put("/cover-letters/{cover_letter_id}")
async def update_cover_letter(
    cover_letter_id: int,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Update an existing cover letter"""
    try:
        new_content = update_data.get("content")

        if not new_content:
            raise HTTPException(status_code=400, detail="content is required")

        # Check if cover letter exists
        check_query = "SELECT id, content FROM cover_letters WHERE id = :cl_id"
        existing = db.execute(text(check_query), {"cl_id": cover_letter_id}).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Cover letter not found")

        # Update cover letter
        update_query = """
        UPDATE cover_letters 
        SET content = :content, ai_generated = false
        WHERE id = :cl_id
        RETURNING id, content, created_at
        """

        result = db.execute(
            text(update_query), {"cl_id": cover_letter_id, "content": new_content}
        )

        updated_cover_letter = result.fetchone()
        db.commit()

        cover_letter_dict = dict(updated_cover_letter._mapping)
        cover_letter_dict["created_at"] = cover_letter_dict["created_at"].isoformat()

        return {
            "success": True,
            "message": "Cover letter updated successfully",
            "cover_letter": cover_letter_dict,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error updating cover letter: {str(e)}"
        )


@cover_letter_router.get("/cover-letters/{cover_letter_id}")
async def get_cover_letter(
    cover_letter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get a specific cover letter"""
    try:
        query = """
        SELECT cl.id, cl.content, cl.ai_generated, cl.template_used, cl.created_at,
               ja.title as job_title, ja.company
        FROM cover_letters cl
        LEFT JOIN job_applications ja ON cl.job_application_id = ja.id
        WHERE cl.id = :cl_id
        """

        result = db.execute(text(query), {"cl_id": cover_letter_id})
        cover_letter_row = result.fetchone()

        if not cover_letter_row:
            raise HTTPException(status_code=404, detail="Cover letter not found")

        cover_letter_dict = dict(cover_letter_row._mapping)
        cover_letter_dict["created_at"] = cover_letter_dict["created_at"].isoformat()

        return {"success": True, "cover_letter": cover_letter_dict}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting cover letter: {str(e)}"
        )


@cover_letter_router.get("/cover-letters")
async def get_user_cover_letters(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get all cover letters for current user"""
    try:
        query = """
        SELECT cl.id, cl.content, cl.ai_generated, cl.template_used, cl.created_at,
               ja.title as job_title, ja.company
        FROM cover_letters cl
        LEFT JOIN job_applications ja ON cl.job_application_id = ja.id
        ORDER BY cl.created_at DESC
        LIMIT :limit
        """

        result = db.execute(text(query), {"limit": limit})
        cover_letters = []

        for row in result.fetchall():
            cl_dict = dict(row._mapping)
            cl_dict["created_at"] = cl_dict["created_at"].isoformat()
            # Truncate content for list view
            if len(cl_dict["content"]) > 200:
                cl_dict["preview"] = cl_dict["content"][:200] + "..."
            else:
                cl_dict["preview"] = cl_dict["content"]
            cover_letters.append(cl_dict)

        return {
            "success": True,
            "cover_letters": cover_letters,
            "total": len(cover_letters),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting cover letters: {str(e)}"
        )
