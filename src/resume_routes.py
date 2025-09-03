"""
Resume Management API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os

from .auth import get_current_user
from .models import get_job_db, UserProfile as User
from .services.ai_service import AIService

router = APIRouter(tags=["Resume Management"])
ai_service = AIService()


class ResumeData(BaseModel):
    skills: List[str]
    experience: List[dict]
    education: List[dict]
    certifications: Optional[List[str]] = None


@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Upload and parse resume"""
    try:
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, detail="Only PDF and DOC files are allowed"
            )

        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/resumes"
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = f"{upload_dir}/{current_user.id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Update user profile with resume path
        update_query = """
        UPDATE user_profiles 
        SET resume_path = :resume_path, updated_at = :updated_at
        WHERE id = :user_id
        """

        db.execute(
            text(update_query),
            {
                "resume_path": file_path,
                "updated_at": datetime.utcnow(),
                "user_id": current_user.id,
            },
        )
        db.commit()

        return {
            "success": True,
            "message": "Resume uploaded successfully",
            "filename": file.filename,
            "file_path": file_path,
            "user_id": current_user.id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")


@router.post("/resume/generate")
async def generate_custom_resume(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """AI-customize resume for specific job"""
    try:
        job_id = request_data.get("job_id")
        job_description = request_data.get("job_description", "")

        if not job_id and not job_description:
            raise HTTPException(
                status_code=400, detail="job_id or job_description is required"
            )

        # Get job details if job_id provided
        job_data = {}
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
            else:
                raise HTTPException(status_code=404, detail="Job not found")
        else:
            job_data = {"description": job_description, "requirements": ""}

        # Get user resume data
        user_skills = json.loads(current_user.skills or "[]")
        resume_data = {
            "skills": user_skills,
            "experience_years": current_user.experience_years or 0,
            "current_title": current_user.current_title or "",
            "name": current_user.name or "",
        }

        # Use AI to customize resume
        customization = await ai_service.customize_resume(resume_data, job_data)

        # Save customized version (simplified for now)
        version_data = {
            "job_id": job_id,
            "customized_skills": customization.get("customized_skills", []),
            "recommendations": customization.get("recommendations", []),
            "created_at": datetime.utcnow().isoformat(),
        }

        return {
            "success": True,
            "message": "Resume customized successfully",
            "customization": customization,
            "version_data": version_data,
            "job_match_score": customization.get("skill_matches", 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error customizing resume: {str(e)}"
        )


@router.get("/resume/versions")
async def get_resume_versions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_job_db)
):
    """List resume variations"""
    try:
        # For now, return basic info since we don't have resume_versions table
        # In a full implementation, you'd create a resume_versions table

        base_resume = {
            "id": "base",
            "name": "Base Resume",
            "created_at": (
                current_user.created_at.isoformat() if current_user.created_at else None
            ),
            "skills": json.loads(current_user.skills or "[]"),
            "file_path": current_user.resume_path,
            "is_base": True,
        }

        versions = [base_resume]

        return {
            "success": True,
            "message": "Resume versions retrieved",
            "versions": versions,
            "total": len(versions),
            "user_id": current_user.id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting resume versions: {str(e)}"
        )


@router.get("/resume/analyze")
async def analyze_resume_completeness(current_user: User = Depends(get_current_user)):
    """Analyze resume completeness and provide suggestions"""
    try:
        user_data = {
            "name": current_user.name,
            "skills": json.loads(current_user.skills or "[]"),
            "experience_years": current_user.experience_years,
            "current_title": current_user.current_title,
            "resume_path": current_user.resume_path,
            "portfolio_url": current_user.portfolio_url,
            "linkedin_url": current_user.linkedin_url,
        }

        analysis = await ai_service.optimize_profile(user_data)

        return {
            "success": True,
            "message": "Resume analysis completed",
            "analysis": analysis,
            "completion_score": analysis.get("profile_completion", 0),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")


@router.delete("/resume/{file_id}")
async def delete_resume(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Delete a resume file"""
    try:
        if file_id == "base" and current_user.resume_path:
            # Delete the base resume file
            try:
                if os.path.exists(current_user.resume_path):
                    os.remove(current_user.resume_path)
            except:
                pass  # File might not exist

            # Update user profile
            update_query = """
            UPDATE user_profiles 
            SET resume_path = NULL, updated_at = :updated_at
            WHERE id = :user_id
            """

            db.execute(
                text(update_query),
                {"updated_at": datetime.utcnow(), "user_id": current_user.id},
            )
            db.commit()

            return {"success": True, "message": "Resume deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Resume not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting resume: {str(e)}")
