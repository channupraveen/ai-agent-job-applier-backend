"""
Job Source Integration Management API Routes - FIXED VERSION
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio

from .auth import get_current_user
from .models import get_job_db, UserProfile as User

router = APIRouter(tags=["Integration Management"])

# Pydantic models for sync preferences
class SyncPreferences(BaseModel):
    autoSync: bool = True
    syncFrequency: int = 120  # in minutes (0 when autoSync is disabled)
    maxJobsPerSync: int = 50  # (0 when autoSync is disabled)
    enableNotifications: bool = True

# Pydantic models for API requests/responses
class JobSource(BaseModel):
    id: str
    name: str
    enabled: bool
    apiKey: Optional[str] = None
    baseUrl: Optional[str] = None
    rateLimit: int = 100
    lastSync: Optional[datetime] = None
    totalJobs: int = 0
    status: str = "inactive"  # active, inactive, error
    icon: str = "pi pi-briefcase"

class JobSourceUpdate(BaseModel):
    enabled: Optional[bool] = None
    apiKey: Optional[str] = None
    rateLimit: Optional[int] = None

# Default job sources configuration - Indian Job Market Focus
DEFAULT_JOB_SOURCES = [
    {
        "id": "naukri",
        "name": "Naukri.com",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://www.naukri.com",
        "rateLimit": 500,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-briefcase"
    },
    {
        "id": "indeed",
        "name": "Indeed India",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://in.indeed.com/rss",
        "rateLimit": 1000,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-search"
    },
    {
        "id": "timesjobs",
        "name": "TimesJobs",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://www.timesjobs.com/rss",
        "rateLimit": 400,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-clock"
    },
    {
        "id": "linkedin",
        "name": "LinkedIn Jobs",
        "enabled": False,
        "apiKey": "",
        "baseUrl": "https://api.linkedin.com/v2/jobSearch",
        "rateLimit": 100,
        "lastSync": None,
        "totalJobs": 0,
        "status": "inactive",
        "icon": "pi pi-linkedin"
    }
]

@router.get("/integrations/job-sources")
async def get_job_sources(db: Session = Depends(get_job_db)):
    """Get all configured job sources"""
    try:
        sources = []
        for source_config in DEFAULT_JOB_SOURCES:
            try:
                count_query = """
                SELECT COUNT(*) as job_count,
                       MAX(created_at) as last_sync
                FROM job_applications 
                WHERE ai_reasoning LIKE :source_pattern
                """
                
                source_pattern = f"%{source_config['name']}%"
                count_result = db.execute(text(count_query), {"source_pattern": source_pattern}).fetchone()
                
                if count_result:
                    source_config = source_config.copy()
                    source_config["totalJobs"] = count_result.job_count or 0
                    source_config["lastSync"] = count_result.last_sync
            except Exception as db_error:
                print(f"DB error for {source_config['name']}: {str(db_error)}")
            
            sources.append(JobSource(**source_config))
        
        return sources
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job sources: {str(e)}")

@router.post("/integrations/job-sources/{source_id}/sync")
async def sync_job_source(
    source_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Manually sync jobs from a specific source using user's job preferences"""
    try:
        sources = await get_job_sources(db)
        source = next((s for s in sources if s.id == source_id), None)
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Job source '{source_id}' not found")
        
        if not source.enabled:
            raise HTTPException(status_code=400, detail=f"{source.name} is disabled")
        
        # Check if user has job search criteria
        criteria_query = """
        SELECT keywords FROM job_search_criteria 
        WHERE user_profile_id = :user_id AND is_active = true
        """
        
        criteria_result = db.execute(text(criteria_query), {"user_id": current_user.id}).fetchone()
        
        if not criteria_result:
            return {
                "success": False,
                "message": "Please set your job search criteria in Job Preferences before syncing"
            }
        
        search_keywords = criteria_result[0]
        if not search_keywords or search_keywords.strip() == "":
            return {
                "success": False,
                "message": "Please add keywords to your job search criteria before syncing"
            }
        
        background_tasks.add_task(perform_job_sync, source_id, source.name, current_user.id, db)
        
        return {
            "success": True,
            "message": f"Sync completed for {source.name}",
            "source_id": source_id,
            "jobs_found": 0,  # Will be updated by background task
            "new_jobs": 0,    # Will be updated by background task
            "search_keywords": search_keywords,
            "estimated_duration": "2-5 minutes",
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting sync: {str(e)}")

# Background task functions
async def perform_job_sync(source_id: str, source_name: str, user_id: int, db: Session):
    """Background task to perform job sync for a specific source using user's job preferences"""
    try:
        # Get user's job search criteria from preferences
        criteria_query = """
        SELECT keywords, locations, experience_levels, excluded_keywords
        FROM job_search_criteria 
        WHERE user_profile_id = :user_id AND is_active = true
        """
        
        criteria_result = db.execute(text(criteria_query), {"user_id": user_id}).fetchone()
        
        if not criteria_result:
            print(f"❌ No job search criteria found for user {user_id}. Using defaults.")
            search_keywords = "software developer"
            search_locations = ["Remote"]
            search_experience = "mid"
        else:
            criteria_dict = dict(criteria_result._mapping)
            search_keywords = criteria_dict.get('keywords', 'software developer')
            
            # Parse JSON fields
            locations_json = criteria_dict.get('locations')
            search_locations = json.loads(locations_json) if locations_json else ["Remote"]
            
            experience_levels_json = criteria_dict.get('experience_levels') 
            experience_levels = json.loads(experience_levels_json) if experience_levels_json else ["mid"]
            search_experience = experience_levels[0] if experience_levels else "mid"
            
            print(f"✅ Using user criteria: keywords='{search_keywords}', locations={search_locations}, experience='{search_experience}'")
        
        jobs = []
        
        if source_id == "naukri":
            from .external_jobs_routes import simulate_naukri_search
            
            class MockRequest:
                def __init__(self, keywords, location, experience):
                    self.keywords = keywords
                    self.location = location if location != "Remote" else "Delhi"
                    self.job_type = "full-time"
                    self.experience_level = experience
                    self.limit = 30
            
            preferred_location = search_locations[0] if search_locations else "Remote"
            mock_request = MockRequest(search_keywords, preferred_location, search_experience)
            jobs = await simulate_naukri_search(mock_request)
        
        elif source_id == "indeed":
            from .external_jobs_routes import simulate_indeed_search
            
            class MockRequest:
                def __init__(self, keywords, location, experience):
                    self.keywords = keywords
                    self.location = location if location != "Remote" else "Mumbai"
                    self.job_type = "full-time"
                    self.experience_level = experience
                    self.limit = 30
            
            preferred_location = search_locations[0] if search_locations else "Remote"
            mock_request = MockRequest(search_keywords, preferred_location, search_experience)
            jobs = await simulate_indeed_search(mock_request)
        
        elif source_id == "timesjobs":
            from .external_jobs_routes import simulate_timesjobs_search
            
            class MockRequest:
                def __init__(self, keywords, location, experience):
                    self.keywords = keywords
                    self.location = location if location != "Remote" else "Bangalore"
                    self.job_type = "full-time"
                    self.experience_level = experience
                    self.limit = 30
            
            preferred_location = search_locations[0] if search_locations else "Remote"
            mock_request = MockRequest(search_keywords, preferred_location, search_experience)
            jobs = await simulate_timesjobs_search(mock_request)
        
        elif source_id == "linkedin":
            from .external_jobs_routes import simulate_linkedin_search
            
            class MockRequest:
                def __init__(self, keywords, location, experience):
                    self.keywords = keywords
                    self.location = location if location != "Remote" else "Hyderabad"
                    self.job_type = "full-time"
                    self.experience_level = experience
                    self.limit = 25
            
            preferred_location = search_locations[0] if search_locations else "Remote"
            mock_request = MockRequest(search_keywords, preferred_location, search_experience)
            jobs = await simulate_linkedin_search(mock_request)
        
        else:
            print(f"Unknown source: {source_id}")
            return
        
        # Save jobs to database
        new_jobs_count = 0
        for job in jobs:
            try:
                existing_query = "SELECT id FROM job_applications WHERE url = :url"
                existing = db.execute(text(existing_query), {"url": job.get("url", "")}).fetchone()
                
                if not existing and job.get("url"):
                    insert_query = """
                    INSERT INTO job_applications (
                        title, company, location, url, description, requirements,
                        salary_range, status, match_score, ai_decision, ai_reasoning,
                        created_at, updated_at
                    ) VALUES (
                        :title, :company, :location, :url, :description, :requirements,
                        :salary_range, 'found', :match_score, :ai_decision, :ai_reasoning,
                        :created_at, :updated_at
                    )
                    """
                    
                    params = {
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "url": job.get("url", ""),
                        "description": job.get("description", ""),
                        "requirements": job.get("requirements", ""),
                        "salary_range": job.get("salary", ""),
                        "match_score": 75,
                        "ai_decision": "maybe",
                        "ai_reasoning": f"{source_name} job sync: Found using criteria '{search_keywords}' in {search_locations}",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    db.execute(text(insert_query), params)
                    new_jobs_count += 1
            except Exception as job_error:
                print(f"Error saving job: {str(job_error)}")
                continue
        
        db.commit()
        
        # Enhanced logging with both metrics
        if new_jobs_count > 0:
            print(f"✅ Synced {new_jobs_count} new jobs from {source_name} using criteria: '{search_keywords}' ({len(jobs)} total found)")
        else:
            print(f"✅ Found {len(jobs)} jobs from {source_name} using criteria: '{search_keywords}' (0 new - all were duplicates)")
        
        print(f"📊 Summary: {len(jobs)} jobs found, {new_jobs_count} new jobs added to database")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error syncing {source_name}: {str(e)}")
        import traceback
        traceback.print_exc()


# ===================================
# SYNC PREFERENCES ENDPOINTS
# ===================================

@router.get("/integrations/preferences")
async def get_sync_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Get sync preferences for the current user"""
    try:
        # Check if user has custom sync preferences stored
        query = """
        SELECT auto_apply_enabled, max_applications_per_day 
        FROM user_profiles 
        WHERE id = :user_id
        """
        
        result = db.execute(text(query), {"user_id": current_user.id}).fetchone()
        
        if result:
            auto_apply = result.auto_apply_enabled or False
            max_apps = result.max_applications_per_day or 10
            
            # Convert to sync preferences format
            preferences = {
                "autoSync": auto_apply,
                "syncFrequency": 120 if auto_apply else 0,  # Set to 0 when autoSync is disabled
                "maxJobsPerSync": (max_apps * 5) if auto_apply else 0,  # Set to 0 when autoSync is disabled
                "enableNotifications": True
            }
        else:
            # Return default preferences
            preferences = {
                "autoSync": True,
                "syncFrequency": 120,
                "maxJobsPerSync": 50,
                "enableNotifications": True
            }
        
        return preferences
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync preferences: {str(e)}")


@router.put("/integrations/preferences")
async def update_sync_preferences(
    preferences: SyncPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Update sync preferences for the current user"""
    try:
        # If autoSync is disabled, set syncFrequency to 0
        sync_frequency = preferences.syncFrequency if preferences.autoSync else 0
        max_jobs_per_sync = preferences.maxJobsPerSync if preferences.autoSync else 0
        
        # Update user profile with sync preferences
        update_query = """
        UPDATE user_profiles SET
            auto_apply_enabled = :auto_sync,
            max_applications_per_day = :max_daily_apps,
            updated_at = :updated_at
        WHERE id = :user_id
        RETURNING id
        """
        
        # Calculate daily applications from sync preferences
        max_daily_apps = min(max_jobs_per_sync // 5, 20) if max_jobs_per_sync > 0 else 0
        
        params = {
            "user_id": current_user.id,
            "auto_sync": preferences.autoSync,
            "max_daily_apps": max_daily_apps,
            "updated_at": datetime.utcnow()
        }
        
        result = db.execute(text(update_query), params)
        updated_user = result.fetchone()
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.commit()
        
        # Return the processed preferences (with syncFrequency set to 0 if disabled)
        processed_preferences = {
            "autoSync": preferences.autoSync,
            "syncFrequency": sync_frequency,
            "maxJobsPerSync": max_jobs_per_sync,
            "enableNotifications": preferences.enableNotifications
        }
        
        return {
            "success": True,
            "message": "Sync preferences updated successfully",
            "preferences": processed_preferences
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating sync preferences: {str(e)}")


@router.put("/integrations/job-sources/{source_id}")
async def update_job_source(
    source_id: str,
    update_data: JobSourceUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update job source settings (e.g., toggle enabled status)"""
    try:
        # For now, we'll just return success since job sources are hardcoded
        # In a real implementation, you'd store this in the database
        
        sources = DEFAULT_JOB_SOURCES.copy()
        source = next((s for s in sources if s["id"] == source_id), None)
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Job source '{source_id}' not found")
        
        if update_data.enabled is not None:
            source["enabled"] = update_data.enabled
            source["status"] = "active" if update_data.enabled else "inactive"
        
        return {
            "success": True,
            "message": f"Job source '{source['name']}' updated successfully",
            "source": source
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating job source: {str(e)}")


@router.post("/integrations/job-sources/sync-all")
async def sync_all_sources(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Sync jobs from all enabled sources"""
    try:
        # Check if user has job search criteria
        criteria_query = """
        SELECT keywords FROM job_search_criteria 
        WHERE user_profile_id = :user_id AND is_active = true
        """
        
        criteria_result = db.execute(text(criteria_query), {"user_id": current_user.id}).fetchone()
        
        if not criteria_result:
            return {
                "success": False,
                "message": "Please set your job search criteria in Job Preferences before syncing"
            }
        
        search_keywords = criteria_result[0]
        if not search_keywords or search_keywords.strip() == "":
            return {
                "success": False,
                "message": "Please add keywords to your job search criteria before syncing"
            }
        
        # Get enabled sources
        enabled_sources = [source for source in DEFAULT_JOB_SOURCES if source["enabled"]]
        
        if not enabled_sources:
            return {
                "success": False,
                "message": "No job sources are enabled. Please enable at least one source."
            }
        
        # Start background sync for all enabled sources
        for source in enabled_sources:
            background_tasks.add_task(
                perform_job_sync, 
                source["id"], 
                source["name"], 
                current_user.id, 
                db
            )
        
        source_names = [source["name"] for source in enabled_sources]
        
        return {
            "success": True,
            "message": f"Bulk sync started for {len(enabled_sources)} sources",
            "sources": source_names,
            "search_keywords": search_keywords,
            "estimated_duration": "5-15 minutes",
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting bulk sync: {str(e)}")


@router.get("/integrations/stats")
async def get_integration_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Get integration statistics"""
    try:
        # Get overall stats
        overall_query = """
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status = 'applied' THEN 1 END) as applied_jobs,
            AVG(match_score) as avg_match_score
        FROM job_applications
        """
        
        overall_result = db.execute(text(overall_query)).fetchone()
        
        # Get source-specific stats
        source_stats = {}
        for source in DEFAULT_JOB_SOURCES:
            source_query = """
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(CASE WHEN status = 'applied' THEN 1 END) as applied_jobs,
                AVG(match_score) as avg_match_score,
                MAX(created_at) as last_import
            FROM job_applications
            WHERE ai_reasoning LIKE :source_pattern
            """
            
            source_pattern = f"%{source['name']}%"
            source_result = db.execute(text(source_query), {"source_pattern": source_pattern}).fetchone()
            
            if source_result:
                total = source_result.total_jobs or 0
                applied = source_result.applied_jobs or 0
                success_rate = (applied / total * 100) if total > 0 else 0
                
                source_stats[source["id"]] = {
                    "total_jobs": total,
                    "applied_jobs": applied,
                    "avg_match_score": round(source_result.avg_match_score or 0, 1),
                    "last_import": source_result.last_import.isoformat() if source_result.last_import else None,
                    "success_rate": round(success_rate, 1)
                }
        
        total_jobs = overall_result.total_jobs or 0
        applied_jobs = overall_result.applied_jobs or 0
        overall_success_rate = (applied_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        return {
            "success": True,
            "overall_stats": {
                "total_external_jobs": total_jobs,
                "total_applications": applied_jobs,
                "overall_success_rate": round(overall_success_rate, 1)
            },
            "source_stats": source_stats,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting integration stats: {str(e)}")


@router.post("/integrations/reset")
async def reset_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Reset all integration settings to defaults"""
    try:
        # Reset user profile preferences to defaults
        reset_query = """
        UPDATE user_profiles SET
            auto_apply_enabled = false,
            max_applications_per_day = 10,
            updated_at = :updated_at
        WHERE id = :user_id
        RETURNING id
        """
        
        params = {
            "user_id": current_user.id,
            "updated_at": datetime.utcnow()
        }
        
        result = db.execute(text(reset_query), params)
        updated_user = result.fetchone()
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.commit()
        
        return {
            "success": True,
            "message": "Integration settings reset to defaults successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting integrations: {str(e)}")
