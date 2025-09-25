"""
User Preferences & Job Search Criteria API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from .auth import get_current_user
from .models import get_job_db, UserProfile as User

router = APIRouter(tags=["User Preferences & Job Criteria"])


class JobSearchCriteria(BaseModel):
    keywords: str
    excluded_keywords: Optional[str] = None
    excludedKeywords: Optional[str] = None  # Accept camelCase from frontend
    min_salary: Optional[int] = None
    minSalary: Optional[int] = None  # Accept camelCase from frontend
    max_salary: Optional[int] = None
    maxSalary: Optional[int] = None  # Accept camelCase from frontend
    job_types: Optional[List[str]] = None  # full-time, part-time, contract, internship
    jobTypes: Optional[List[str]] = None  # Accept camelCase from frontend
    experience_levels: Optional[List[str]] = None  # entry, mid, senior, executive
    experienceLevels: Optional[List[str]] = None  # Accept camelCase from frontend
    locations: Optional[List[str]] = None
    remote_allowed: bool = True
    remoteAllowed: Optional[bool] = None  # Accept camelCase from frontend
    willing_to_relocate: bool = False
    willingToRelocate: Optional[bool] = None  # Accept camelCase from frontend
    company_sizes: Optional[List[str]] = None  # startup, small, medium, large, enterprise
    companySizes: Optional[List[str]] = None  # Accept camelCase from frontend
    industries: Optional[List[str]] = None
    is_active: Optional[bool] = True
    isActive: Optional[bool] = None  # Accept camelCase from frontend


class BlacklistRequest(BaseModel):
    company_name: str
    reason: Optional[str] = None


@router.post("/preferences/criteria")
async def set_job_search_criteria(
    criteria: JobSearchCriteria,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Set or update job search criteria"""
    try:
        # Check if criteria already exists
        check_query = (
            "SELECT id FROM job_search_criteria WHERE user_profile_id = :user_id"
        )
        existing = db.execute(
            text(check_query), {"user_id": current_user.id}
        ).fetchone()

        if existing:
            # Update existing criteria
            update_query = """
            UPDATE job_search_criteria SET
                keywords = :keywords,
                excluded_keywords = :excluded_keywords,
                min_salary = :min_salary,
                max_salary = :max_salary,
                job_types = :job_types,
                experience_levels = :experience_levels,
                locations = :locations,
                remote_allowed = :remote_allowed,
                willing_to_relocate = :willing_to_relocate,
                company_sizes = :company_sizes,
                industries = :industries,
                is_active = true
            WHERE user_profile_id = :user_id
            RETURNING id
            """

            params = {
                "user_id": current_user.id,
                "keywords": criteria.keywords,
                "excluded_keywords": criteria.excluded_keywords or criteria.excludedKeywords,
                "min_salary": criteria.min_salary or criteria.minSalary,
                "max_salary": criteria.max_salary or criteria.maxSalary,
                "job_types": (
                    json.dumps(criteria.job_types or criteria.jobTypes) 
                    if (criteria.job_types or criteria.jobTypes) else None
                ),
                "experience_levels": (
                    json.dumps(criteria.experience_levels or criteria.experienceLevels)
                    if (criteria.experience_levels or criteria.experienceLevels)
                    else None
                ),
                "locations": (
                    json.dumps(criteria.locations) if criteria.locations else None
                ),
                "remote_allowed": criteria.remote_allowed if criteria.remoteAllowed is None else criteria.remoteAllowed,
                "willing_to_relocate": criteria.willing_to_relocate if criteria.willingToRelocate is None else criteria.willingToRelocate,
                "company_sizes": (
                    json.dumps(criteria.company_sizes or criteria.companySizes)
                    if (criteria.company_sizes or criteria.companySizes)
                    else None
                ),
                "industries": (
                    json.dumps(criteria.industries) if criteria.industries else None
                ),
            }

            result = db.execute(text(update_query), params)
            criteria_id = result.fetchone()[0]
            action = "updated"
        else:
            # Create new criteria
            insert_query = """
            INSERT INTO job_search_criteria (
                user_profile_id, keywords, excluded_keywords, min_salary, max_salary,
                job_types, experience_levels, locations, remote_allowed, willing_to_relocate,
                company_sizes, industries, is_active, created_at
            ) VALUES (
                :user_id, :keywords, :excluded_keywords, :min_salary, :max_salary,
                :job_types, :experience_levels, :locations, :remote_allowed, :willing_to_relocate,
                :company_sizes, :industries, true, :created_at
            ) RETURNING id
            """

            params = {
                "user_id": current_user.id,
                "keywords": criteria.keywords,
                "excluded_keywords": criteria.excluded_keywords or criteria.excludedKeywords,
                "min_salary": criteria.min_salary or criteria.minSalary,
                "max_salary": criteria.max_salary or criteria.maxSalary,
                "job_types": (
                    json.dumps(criteria.job_types or criteria.jobTypes) 
                    if (criteria.job_types or criteria.jobTypes) else None
                ),
                "experience_levels": (
                    json.dumps(criteria.experience_levels or criteria.experienceLevels)
                    if (criteria.experience_levels or criteria.experienceLevels)
                    else None
                ),
                "locations": (
                    json.dumps(criteria.locations) if criteria.locations else None
                ),
                "remote_allowed": criteria.remote_allowed if criteria.remoteAllowed is None else criteria.remoteAllowed,
                "willing_to_relocate": criteria.willing_to_relocate if criteria.willingToRelocate is None else criteria.willingToRelocate,
                "company_sizes": (
                    json.dumps(criteria.company_sizes or criteria.companySizes)
                    if (criteria.company_sizes or criteria.companySizes)
                    else None
                ),
                "industries": (
                    json.dumps(criteria.industries) if criteria.industries else None
                ),
                "created_at": datetime.utcnow(),
            }

            result = db.execute(text(insert_query), params)
            criteria_id = result.fetchone()[0]
            action = "created"

        db.commit()

        return {
            "success": True,
            "message": f"Job search criteria {action} successfully",
            "criteria_id": criteria_id,
            "criteria": criteria.dict(),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error setting job criteria: {str(e)}"
        )


@router.get("/preferences/criteria")
async def get_job_search_criteria(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_job_db)
):
    """Get current job search criteria"""
    try:
        query = """
        SELECT 
            keywords, excluded_keywords, min_salary, max_salary,
            job_types, experience_levels, locations, remote_allowed,
            willing_to_relocate, company_sizes, industries, is_active,
            created_at
        FROM job_search_criteria
        WHERE user_profile_id = :user_id AND is_active = true
        """

        result = db.execute(text(query), {"user_id": current_user.id})
        criteria_row = result.fetchone()

        if not criteria_row:
            # Return default criteria
            return {
                "success": True,
                "criteria": {
                    "keywords": "",
                    "excluded_keywords": None,
                    "min_salary": None,
                    "max_salary": None,
                    "job_types": ["full-time"],
                    "experience_levels": ["mid-level"],
                    "locations": ["Remote"],
                    "remote_allowed": True,
                    "willing_to_relocate": False,
                    "company_sizes": [],
                    "industries": [],
                    "is_active": False,
                },
                "message": "No criteria set. Using defaults.",
            }

        criteria_dict = dict(criteria_row._mapping)

        # Parse JSON fields
        for json_field in [
            "job_types",
            "experience_levels",
            "locations",
            "company_sizes",
            "industries",
        ]:
            if criteria_dict[json_field]:
                criteria_dict[json_field] = json.loads(criteria_dict[json_field])

        criteria_dict["created_at"] = criteria_dict["created_at"].isoformat()

        return {"success": True, "criteria": criteria_dict}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting job criteria: {str(e)}"
        )


@router.post("/preferences/blacklist")
async def add_company_to_blacklist(
    blacklist_request: BlacklistRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Add company to blacklist"""
    try:
        # Check if company already blacklisted
        check_query = "SELECT id FROM company_blacklist WHERE LOWER(company_name) = LOWER(:company_name)"
        existing = db.execute(
            text(check_query), {"company_name": blacklist_request.company_name}
        ).fetchone()

        if existing:
            return {
                "success": False,
                "message": f"{blacklist_request.company_name} is already blacklisted",
            }

        # Add to blacklist
        insert_query = """
        INSERT INTO company_blacklist (company_name, reason, added_at)
        VALUES (:company_name, :reason, :added_at)
        RETURNING id, company_name, reason
        """

        params = {
            "company_name": blacklist_request.company_name,
            "reason": blacklist_request.reason or "User preference",
            "added_at": datetime.utcnow(),
        }

        result = db.execute(text(insert_query), params)
        blacklisted_company = result.fetchone()
        db.commit()

        company_dict = dict(blacklisted_company._mapping)

        return {
            "success": True,
            "message": f"{blacklist_request.company_name} added to blacklist",
            "blacklisted_company": company_dict,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error adding to blacklist: {str(e)}"
        )


@router.get("/preferences/blacklist")
async def get_blacklisted_companies(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get list of blacklisted companies"""
    try:
        query = """
        SELECT id, company_name, reason, added_at
        FROM company_blacklist
        ORDER BY added_at DESC
        LIMIT :limit
        """

        result = db.execute(text(query), {"limit": limit})
        blacklisted_companies = []

        for row in result.fetchall():
            company_dict = dict(row._mapping)
            company_dict["added_at"] = company_dict["added_at"].isoformat()
            blacklisted_companies.append(company_dict)

        return {
            "success": True,
            "blacklisted_companies": blacklisted_companies,
            "total": len(blacklisted_companies),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting blacklist: {str(e)}"
        )


@router.delete("/preferences/blacklist/{company_id}")
async def remove_company_from_blacklist(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Remove company from blacklist"""
    try:
        # Check if company exists in blacklist
        check_query = (
            "SELECT company_name FROM company_blacklist WHERE id = :company_id"
        )
        existing = db.execute(text(check_query), {"company_id": company_id}).fetchone()

        if not existing:
            raise HTTPException(
                status_code=404, detail="Company not found in blacklist"
            )

        company_name = existing[0]

        # Remove from blacklist
        delete_query = "DELETE FROM company_blacklist WHERE id = :company_id"
        db.execute(text(delete_query), {"company_id": company_id})
        db.commit()

        return {"success": True, "message": f"{company_name} removed from blacklist"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error removing from blacklist: {str(e)}"
        )


@router.get("/preferences/summary")
async def get_preferences_summary(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_job_db)
):
    """Get summary of all user preferences"""
    try:
        # Get job criteria
        criteria_query = """
        SELECT keywords, job_types, locations, remote_allowed, is_active
        FROM job_search_criteria
        WHERE user_profile_id = :user_id AND is_active = true
        """

        criteria_result = db.execute(text(criteria_query), {"user_id": current_user.id})
        criteria_row = criteria_result.fetchone()

        # Get blacklist count
        blacklist_query = "SELECT COUNT(*) FROM company_blacklist"
        blacklist_result = db.execute(text(blacklist_query))
        blacklist_count = blacklist_result.fetchone()[0]

        # Get user profile preferences
        profile_prefs = {
            "auto_apply_enabled": current_user.auto_apply_enabled,
            "max_applications_per_day": current_user.max_applications_per_day,
            "preferred_job_types": json.loads(current_user.preferred_job_types or "[]"),
        }

        summary = {
            "job_criteria_set": bool(criteria_row),
            "blacklisted_companies": blacklist_count,
            "profile_preferences": profile_prefs,
        }

        if criteria_row:
            criteria_dict = dict(criteria_row._mapping)
            if criteria_dict["job_types"]:
                criteria_dict["job_types"] = json.loads(criteria_dict["job_types"])
            if criteria_dict["locations"]:
                criteria_dict["locations"] = json.loads(criteria_dict["locations"])
            summary["current_criteria"] = criteria_dict

        return {"success": True, "preferences_summary": summary}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting preferences summary: {str(e)}"
        )
