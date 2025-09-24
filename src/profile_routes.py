"""
User Profile Management API Routes
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

router = APIRouter(tags=["User Profile Management"])
ai_service = AIService()


class EducationEntry(BaseModel):
    """Education entry model"""
    degree: str
    institution: str
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    current_title: Optional[str] = None
    experience_years: Optional[int] = None
    skills: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    salary_expectations: Optional[str] = None
    current_ctc: Optional[str] = None  # ✅ Added missing field
    expected_ctc: Optional[str] = None  # ✅ Added missing field
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    auto_apply_enabled: Optional[bool] = None
    max_applications_per_day: Optional[int] = None
    preferred_job_types: Optional[List[str]] = None
    education: Optional[List[EducationEntry]] = None  # ✅ Added missing field


class SkillsRequest(BaseModel):
    skills: List[str]
    action: str = "replace"  # replace, add, remove


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_job_db)
):
    """Get current user profile"""
    try:
        profile_data = {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "current_title": current_user.current_title,
            "experience_years": current_user.experience_years,
            "skills": json.loads(current_user.skills or "[]"),
            "preferred_locations": json.loads(current_user.preferred_locations or "[]"),
            "salary_expectations": current_user.salary_expectations,
            "current_ctc": getattr(current_user, 'current_ctc', None),  # ✅ Added missing field
            "expected_ctc": getattr(current_user, 'expected_ctc', None),  # ✅ Added missing field
            "portfolio_url": current_user.portfolio_url,
            "linkedin_url": current_user.linkedin_url,
            "resume_path": current_user.resume_path,
            "profile_picture_url": current_user.profile_picture_url,
            "auto_apply_enabled": current_user.auto_apply_enabled,
            "max_applications_per_day": current_user.max_applications_per_day,
            "preferred_job_types": json.loads(current_user.preferred_job_types or "[]"),
            "auth_provider": current_user.auth_provider,
            "created_at": (
                current_user.created_at.isoformat() if current_user.created_at else None
            ),
            "updated_at": (
                current_user.updated_at.isoformat() if current_user.updated_at else None
            ),
            "last_login": (
                current_user.last_login.isoformat() if current_user.last_login else None
            ),
            "education": json.loads(getattr(current_user, 'education', '[]') or '[]'),  # ✅ Added missing field
        }

        # Calculate profile completion
        completion_score = await calculate_profile_completion(profile_data)
        profile_data["completion_score"] = completion_score

        return {"success": True, "profile": profile_data}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving profile: {str(e)}"
        )


@router.put("/profile")
async def update_user_profile(
    profile_update: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Update user profile information"""
    try:
        update_fields = []
        params = {"user_id": current_user.id, "updated_at": datetime.utcnow()}

        # Build dynamic update query based on provided fields
        if profile_update.name is not None:
            update_fields.append("name = :name")
            params["name"] = profile_update.name

        if profile_update.phone is not None:
            update_fields.append("phone = :phone")
            params["phone"] = profile_update.phone

        if profile_update.current_title is not None:
            update_fields.append("current_title = :current_title")
            params["current_title"] = profile_update.current_title

        if profile_update.experience_years is not None:
            update_fields.append("experience_years = :experience_years")
            params["experience_years"] = profile_update.experience_years

        if profile_update.skills is not None:
            update_fields.append("skills = :skills")
            params["skills"] = json.dumps(profile_update.skills)

        if profile_update.preferred_locations is not None:
            update_fields.append("preferred_locations = :preferred_locations")
            params["preferred_locations"] = json.dumps(
                profile_update.preferred_locations
            )

        if profile_update.salary_expectations is not None:
            update_fields.append("salary_expectations = :salary_expectations")
            params["salary_expectations"] = profile_update.salary_expectations

        # ✅ Added missing CTC fields
        if profile_update.current_ctc is not None:
            update_fields.append("current_ctc = :current_ctc")
            params["current_ctc"] = profile_update.current_ctc

        if profile_update.expected_ctc is not None:
            update_fields.append("expected_ctc = :expected_ctc")
            params["expected_ctc"] = profile_update.expected_ctc

        if profile_update.portfolio_url is not None:
            update_fields.append("portfolio_url = :portfolio_url")
            params["portfolio_url"] = profile_update.portfolio_url

        if profile_update.linkedin_url is not None:
            update_fields.append("linkedin_url = :linkedin_url")
            params["linkedin_url"] = profile_update.linkedin_url

        if profile_update.auto_apply_enabled is not None:
            update_fields.append("auto_apply_enabled = :auto_apply_enabled")
            params["auto_apply_enabled"] = profile_update.auto_apply_enabled

        if profile_update.max_applications_per_day is not None:
            update_fields.append("max_applications_per_day = :max_applications_per_day")
            params["max_applications_per_day"] = profile_update.max_applications_per_day

        if profile_update.preferred_job_types is not None:
            update_fields.append("preferred_job_types = :preferred_job_types")
            params["preferred_job_types"] = json.dumps(
                profile_update.preferred_job_types
            )

        # ✅ Added missing education field
        if profile_update.education is not None:
            update_fields.append("education = :education")
            # Convert EducationEntry objects to dict for JSON serialization
            education_data = [edu.dict() if hasattr(edu, 'dict') else edu for edu in profile_update.education]
            params["education"] = json.dumps(education_data)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        # Always update the updated_at timestamp
        update_fields.append("updated_at = :updated_at")

        update_query = f"""
        UPDATE user_profiles 
        SET {', '.join(update_fields)}
        WHERE id = :user_id
        RETURNING id, name, email, current_title, experience_years
        """

        result = db.execute(text(update_query), params)
        updated_user = result.fetchone()
        db.commit()

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        # ✅ FIXED: Return complete profile data after update
        # Fetch the complete updated user profile
        db.refresh(current_user)
        
        complete_profile = {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "current_title": current_user.current_title,
            "experience_years": current_user.experience_years,
            "skills": json.loads(current_user.skills or "[]"),
            "preferred_locations": json.loads(current_user.preferred_locations or "[]"),
            "salary_expectations": current_user.salary_expectations,
            "current_ctc": getattr(current_user, 'current_ctc', None),
            "expected_ctc": getattr(current_user, 'expected_ctc', None),
            "portfolio_url": current_user.portfolio_url,
            "linkedin_url": current_user.linkedin_url,
            "resume_path": current_user.resume_path,
            "profile_picture_url": current_user.profile_picture_url,
            "auto_apply_enabled": current_user.auto_apply_enabled,
            "max_applications_per_day": current_user.max_applications_per_day,
            "preferred_job_types": json.loads(current_user.preferred_job_types or "[]"),
            "auth_provider": current_user.auth_provider,
            "created_at": (
                current_user.created_at.isoformat() if current_user.created_at else None
            ),
            "updated_at": (
                current_user.updated_at.isoformat() if current_user.updated_at else None
            ),
            "last_login": (
                current_user.last_login.isoformat() if current_user.last_login else None
            ),
            "education": json.loads(getattr(current_user, 'education', '[]') or '[]'),
        }

        return complete_profile

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")


@router.post("/profile/skills")
async def manage_user_skills(
    skills_request: SkillsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Add, remove, or replace user skills"""
    try:
        current_skills = json.loads(current_user.skills or "[]")

        if skills_request.action == "replace":
            new_skills = skills_request.skills
        elif skills_request.action == "add":
            new_skills = list(set(current_skills + skills_request.skills))
        elif skills_request.action == "remove":
            new_skills = [
                skill for skill in current_skills if skill not in skills_request.skills
            ]
        else:
            raise HTTPException(
                status_code=400, detail="Invalid action. Use: replace, add, or remove"
            )

        # Update skills in database
        update_query = """
        UPDATE user_profiles 
        SET skills = :skills, updated_at = :updated_at
        WHERE id = :user_id
        RETURNING skills
        """

        params = {
            "skills": json.dumps(new_skills),
            "updated_at": datetime.utcnow(),
            "user_id": current_user.id,
        }

        result = db.execute(text(update_query), params)
        updated_skills_row = result.fetchone()
        db.commit()

        updated_skills = json.loads(updated_skills_row[0])

        return {
            "success": True,
            "message": f"Skills {skills_request.action}d successfully",
            "skills": updated_skills,
            "total_skills": len(updated_skills),
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error managing skills: {str(e)}")


@router.get("/profile/completeness")
async def get_profile_completeness(current_user: User = Depends(get_current_user)):
    """Get profile completion score and suggestions"""
    try:
        profile_data = {
            "name": current_user.name,
            "phone": current_user.phone,
            "current_title": current_user.current_title,
            "experience_years": current_user.experience_years,
            "skills": json.loads(current_user.skills or "[]"),
            "resume_path": current_user.resume_path,
            "portfolio_url": current_user.portfolio_url,
            "linkedin_url": current_user.linkedin_url,
        }

        completion_score = await calculate_profile_completion(profile_data)
        suggestions = generate_profile_suggestions(profile_data)

        return {
            "success": True,
            "completion_score": completion_score,
            "suggestions": suggestions,
            "profile_strength": get_profile_strength(completion_score),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating completeness: {str(e)}"
        )


@router.post("/profile/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Upload profile picture"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, detail="Only JPEG and PNG images are allowed"
            )

        # Create uploads directory
        upload_dir = "uploads/profile_pictures"
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = f"{upload_dir}/{current_user.id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Update database
        update_query = """
        UPDATE user_profiles 
        SET profile_picture_url = :picture_url, updated_at = :updated_at
        WHERE id = :user_id
        """

        db.execute(
            text(update_query),
            {
                "picture_url": file_path,
                "updated_at": datetime.utcnow(),
                "user_id": current_user.id,
            },
        )
        db.commit()

        return {
            "success": True,
            "message": "Profile picture uploaded successfully",
            "file_path": file_path,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error uploading picture: {str(e)}"
        )


# Helper functions
async def calculate_profile_completion(profile_data: Dict) -> int:
    """Calculate profile completion percentage"""
    required_fields = [
        "name",
        "current_title",
        "experience_years",
        "skills",
        "resume_path",
        "portfolio_url",
        "linkedin_url",
    ]

    completed = 0
    for field in required_fields:
        value = profile_data.get(field)
        if field == "skills":
            if value and len(value) > 0:
                completed += 1
        elif value:
            completed += 1

    return int((completed / len(required_fields)) * 100)


def generate_profile_suggestions(profile_data: Dict) -> List[str]:
    """Generate profile improvement suggestions"""
    suggestions = []

    if not profile_data.get("name"):
        suggestions.append("Add your full name")

    if not profile_data.get("current_title"):
        suggestions.append("Add your current job title")

    if not profile_data.get("experience_years"):
        suggestions.append("Add years of experience")

    skills = profile_data.get("skills", [])
    if len(skills) < 5:
        suggestions.append(
            f"Add more skills (currently {len(skills)}, recommended: 5+)"
        )

    if not profile_data.get("resume_path"):
        suggestions.append("Upload your resume")

    if not profile_data.get("portfolio_url"):
        suggestions.append("Add portfolio URL to showcase your work")

    if not profile_data.get("linkedin_url"):
        suggestions.append("Add LinkedIn profile for better networking")

    if not profile_data.get("phone"):
        suggestions.append("Add phone number for contact")

    return suggestions


def get_profile_strength(completion_score: int) -> str:
    """Get profile strength based on completion score"""
    if completion_score >= 90:
        return "Excellent"
    elif completion_score >= 70:
        return "Good"
    elif completion_score >= 50:
        return "Fair"
    else:
        return "Needs Improvement"
