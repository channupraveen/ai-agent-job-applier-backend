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
    },
    {
        "id": "foundit",
        "name": "Foundit (Monster India)",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://www.foundit.in",
        "rateLimit": 300,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-star"
    },
    {
        "id": "shine",
        "name": "Shine.com",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://www.shine.com",
        "rateLimit": 250,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-sun"
    },
    {
        "id": "freshersjobs",
        "name": "Freshers Jobs",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://www.freshersworld.com",
        "rateLimit": 200,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-users"
    },
    {
        "id": "internshala",
        "name": "Internshala",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://internshala.com",
        "rateLimit": 150,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-book"
    },
    {
        "id": "instahyre",
        "name": "Instahyre",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://www.instahyre.com",
        "rateLimit": 200,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-bolt"
    },
    {
        "id": "angellist",
        "name": "AngelList (Wellfound)",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://wellfound.com",
        "rateLimit": 100,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-heart"
    },
    {
        "id": "apnacircle",
        "name": "Apna Circle",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://apnacircle.com",
        "rateLimit": 150,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-users"
    },
    {
        "id": "hirist",
        "name": "Hirist (Tech Jobs)",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://www.hirist.com",
        "rateLimit": 200,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-desktop"
    },
    {
        "id": "jobhai",
        "name": "JobHai",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://www.jobhai.com",
        "rateLimit": 150,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-map"
    },
    {
        "id": "cutshort",
        "name": "Cutshort",
        "enabled": True,
        "apiKey": "",
        "baseUrl": "https://cutshort.io",
        "rateLimit": 100,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-filter"
    },
    {
        "id": "jobsearch",
        "name": "Job Search India",
        "enabled": False,
        "apiKey": "",
        "baseUrl": "https://www.jobsearchindia.com",
        "rateLimit": 100,
        "lastSync": None,
        "totalJobs": 0,
        "status": "inactive",
        "icon": "pi pi-compass"
    },
    {
        "id": "govtjobs",
        "name": "Government Jobs India",
        "enabled": False,
        "apiKey": "",
        "baseUrl": "https://www.sarkariresult.com",
        "rateLimit": 50,
        "lastSync": None,
        "totalJobs": 0,
        "status": "inactive",
        "icon": "pi pi-building"
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
        
        # New job sources - Add simulation functions for each
        elif source_id == "foundit":
            jobs = await simulate_foundit_search(search_keywords, search_locations, search_experience)
        
        elif source_id == "shine":
            jobs = await simulate_shine_search(search_keywords, search_locations, search_experience)
            
        elif source_id == "freshersjobs":
            jobs = await simulate_freshers_search(search_keywords, search_locations, search_experience)
            
        elif source_id == "internshala":
            jobs = await simulate_internshala_search(search_keywords, search_locations, search_experience)
            
        elif source_id == "instahyre":
            jobs = await simulate_instahyre_search(search_keywords, search_locations, search_experience)
            
        elif source_id == "angellist":
            jobs = await simulate_angellist_search(search_keywords, search_locations, search_experience)
            
        elif source_id == "apnacircle":
            jobs = await simulate_apnacircle_search(search_keywords, search_locations, search_experience)
            
        elif source_id == "hirist":
            jobs = await simulate_hirist_search(search_keywords, search_locations, search_experience)
            
        elif source_id == "jobhai":
            jobs = await simulate_jobhai_search(search_keywords, search_locations, search_experience)
            
        elif source_id == "cutshort":
            jobs = await simulate_cutshort_search(search_keywords, search_locations, search_experience)
            
        elif source_id == "jobsearch":
            jobs = await simulate_jobsearch_search(search_keywords, search_locations, search_experience)
            
        elif source_id == "govtjobs":
            jobs = await simulate_govtjobs_search(search_keywords, search_locations, search_experience)
        
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


# ===================================
# SIMULATION FUNCTIONS FOR NEW JOB SOURCES
# ===================================

async def simulate_foundit_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Foundit (Monster India) job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Monster India", "Randstad India", "ManpowerGroup India", "Kelly Services", "ABC Consultants", "TeamLease Services", "Adecco India"]
    titles = [f"Senior {keywords} Developer", f"{keywords} Engineer", f"{keywords} Consultant", f"Lead {keywords} Specialist"]
    salaries = ["₹8,00,000 - ₹15,00,000", "₹10,00,000 - ₹18,00,000", "₹12,00,000 - ₹22,00,000"]
    
    jobs = []
    location = locations[0] if locations else "Mumbai"
    
    for i in range(random.randint(10, 18)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://foundit.in/jobs/{60000000 + i}",
            "description": f"Exciting {keywords} opportunity with growth potential.",
            "requirements": f"{keywords}, {experience} level experience, Team collaboration",
            "salary": random.choice(salaries),
            "posted_date": "2 days ago"
        })
    
    return jobs


async def simulate_shine_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Shine.com job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Shine Solutions", "Tech Shine", "Bright Careers", "Shine Tech", "Global Shine", "Shine Innovations", "Next Shine"]
    titles = [f"{keywords} Developer", f"Senior {keywords} Engineer", f"{keywords} Architect", f"{keywords} Lead"]
    salaries = ["₹6,00,000 - ₹12,00,000", "₹8,00,000 - ₹14,00,000", "₹10,00,000 - ₹16,00,000"]
    
    jobs = []
    location = locations[0] if locations else "Chennai"
    
    for i in range(random.randint(8, 15)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://shine.com/job/{70000000 + i}",
            "description": f"Great opportunity for {keywords} professionals to shine.",
            "requirements": f"Strong {keywords} skills, {experience} experience, Problem-solving",
            "salary": random.choice(salaries),
            "posted_date": "1 day ago"
        })
    
    return jobs


async def simulate_freshers_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Freshers Jobs search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Fresher Opportunities", "New Grad Tech", "Entry Level Corp", "Campus Connect", "Graduate Hub", "Fresher Focus"]
    titles = [f"Junior {keywords} Developer", f"Trainee {keywords} Engineer", f"Associate {keywords} Consultant", f"Entry Level {keywords}"]
    salaries = ["₹3,00,000 - ₹6,00,000", "₹4,00,000 - ₹7,00,000", "₹5,00,000 - ₹8,00,000"]
    
    jobs = []
    location = locations[0] if locations else "Pune"
    
    for i in range(random.randint(12, 20)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://freshersworld.com/job/{80000000 + i}",
            "description": f"Perfect entry-level opportunity for fresh {keywords} graduates.",
            "requirements": f"Basic {keywords} knowledge, Willingness to learn, Fresh graduate",
            "salary": random.choice(salaries),
            "posted_date": "3 days ago"
        })
    
    return jobs


async def simulate_internshala_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Internshala job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Internshala", "Student Connect", "Campus Jobs", "Intern Hub", "Learning Lab", "Skill Builder"]
    titles = [f"{keywords} Intern", f"{keywords} Trainee", f"Junior {keywords} Associate", f"{keywords} Graduate Trainee"]
    salaries = ["₹15,000 - ₹25,000 per month", "₹20,000 - ₹30,000 per month", "₹25,000 - ₹35,000 per month"]
    
    jobs = []
    location = locations[0] if locations else "Bangalore"
    
    for i in range(random.randint(6, 12)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://internshala.com/internship/{90000000 + i}",
            "description": f"Learn and grow with this {keywords} internship opportunity.",
            "requirements": f"{keywords} basics, Student/Recent graduate, Eagerness to learn",
            "salary": random.choice(salaries),
            "posted_date": "5 days ago"
        })
    
    return jobs


async def simulate_instahyre_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Instahyre job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Instahyre Tech", "Quick Hire Solutions", "Rapid Recruitment", "Fast Track Careers", "Instant Opportunities", "Speed Hire"]
    titles = [f"Senior {keywords} Developer", f"{keywords} Tech Lead", f"Principal {keywords} Engineer", f"{keywords} Solution Architect"]
    salaries = ["₹12,00,000 - ₹20,00,000", "₹15,00,000 - ₹25,00,000", "₹18,00,000 - ₹30,00,000"]
    
    jobs = []
    location = locations[0] if locations else "Gurgaon"
    
    for i in range(random.randint(8, 14)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://instahyre.com/job/{100000000 + i}",
            "description": f"Fast-track your {keywords} career with top companies.",
            "requirements": f"Advanced {keywords} skills, {experience} experience, Leadership potential",
            "salary": random.choice(salaries),
            "posted_date": "1 day ago"
        })
    
    return jobs


async def simulate_angellist_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate AngelList (Wellfound) job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Startup Angel", "Innovation Labs", "Venture Tech", "Growth Co", "Disrupt Inc", "Scale Up"]
    titles = [f"Senior {keywords} Engineer", f"{keywords} Tech Lead", f"Full Stack {keywords} Developer", f"{keywords} Product Engineer"]
    salaries = ["₹10,00,000 - ₹18,00,000 + Equity", "₹14,00,000 - ₹22,00,000 + Equity", "₹16,00,000 - ₹26,00,000 + Equity"]
    
    jobs = []
    location = locations[0] if locations else "Bangalore"
    
    for i in range(random.randint(5, 10)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://wellfound.com/job/{110000000 + i}",
            "description": f"Join an exciting startup as a {keywords} professional with equity opportunities.",
            "requirements": f"{keywords} expertise, Startup experience preferred, Equity-minded",
            "salary": random.choice(salaries),
            "posted_date": "2 days ago"
        })
    
    return jobs


async def simulate_apnacircle_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Apna Circle job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Apna Solutions", "Circle Tech", "Local Jobs Hub", "Community Work", "Neighborhood Opportunities", "Local Connect"]
    titles = [f"{keywords} Specialist", f"Local {keywords} Expert", f"{keywords} Community Leader", f"Regional {keywords} Manager"]
    salaries = ["₹5,00,000 - ₹10,00,000", "₹6,00,000 - ₹12,00,000", "₹8,00,000 - ₹14,00,000"]
    
    jobs = []
    location = locations[0] if locations else "Delhi"
    
    for i in range(random.randint(6, 12)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://apnacircle.com/job/{120000000 + i}",
            "description": f"Local {keywords} opportunity with community impact.",
            "requirements": f"{keywords} skills, Local market knowledge, Community engagement",
            "salary": random.choice(salaries),
            "posted_date": "4 days ago"
        })
    
    return jobs


async def simulate_hirist_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Hirist (Tech Jobs) job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Tech Hirist", "IT Solutions Pro", "Code Experts", "Dev Masters", "Tech Innovators", "Digital Pioneers"]
    titles = [f"{keywords} Software Engineer", f"Senior {keywords} Developer", f"{keywords} Technical Lead", f"{keywords} System Architect"]
    salaries = ["₹8,00,000 - ₹16,00,000", "₹12,00,000 - ₹20,00,000", "₹15,00,000 - ₹25,00,000"]
    
    jobs = []
    location = locations[0] if locations else "Hyderabad"
    
    for i in range(random.randint(10, 16)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://hirist.com/job/{130000000 + i}",
            "description": f"Technical excellence opportunity for {keywords} professionals.",
            "requirements": f"Strong {keywords} background, Technical expertise, Innovation mindset",
            "salary": random.choice(salaries),
            "posted_date": "2 days ago"
        })
    
    return jobs


async def simulate_jobhai_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate JobHai job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["JobHai Solutions", "Career Hub", "Employment Plus", "Job Connect", "Work Opportunities", "Career Bridge"]
    titles = [f"{keywords} Professional", f"{keywords} Associate", f"Senior {keywords} Analyst", f"{keywords} Team Lead"]
    salaries = ["₹6,00,000 - ₹11,00,000", "₹7,00,000 - ₹13,00,000", "₹9,00,000 - ₹15,00,000"]
    
    jobs = []
    location = locations[0] if locations else "Mumbai"
    
    for i in range(random.randint(8, 14)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://jobhai.com/job/{140000000 + i}",
            "description": f"Advance your {keywords} career with established companies.",
            "requirements": f"{keywords} experience, Professional growth mindset, Team player",
            "salary": random.choice(salaries),
            "posted_date": "3 days ago"
        })
    
    return jobs


async def simulate_cutshort_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Cutshort job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Cutshort Tech", "Quick Match Solutions", "Talent Bridge", "Skill Connect", "Direct Hire", "Smart Recruiting"]
    titles = [f"{keywords} Engineer", f"Full Stack {keywords} Developer", f"{keywords} Product Engineer", f"Senior {keywords} Consultant"]
    salaries = ["₹10,00,000 - ₹18,00,000", "₹13,00,000 - ₹21,00,000", "₹15,00,000 - ₹24,00,000"]
    
    jobs = []
    location = locations[0] if locations else "Bangalore"
    
    for i in range(random.randint(6, 12)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://cutshort.io/job/{150000000 + i}",
            "description": f"Direct hiring opportunity for {keywords} experts.",
            "requirements": f"Expert {keywords} skills, Direct communication, Results-driven",
            "salary": random.choice(salaries),
            "posted_date": "1 day ago"
        })
    
    return jobs


async def simulate_jobsearch_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Job Search India job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Search Solutions", "Job Portal India", "Career Search Hub", "Employment Search", "Job Finder India", "Search Connect"]
    titles = [f"{keywords} Specialist", f"{keywords} Expert", f"Senior {keywords} Professional", f"{keywords} Consultant"]
    salaries = ["₹5,00,000 - ₹9,00,000", "₹6,00,000 - ₹11,00,000", "₹8,00,000 - ₹13,00,000"]
    
    jobs = []
    location = locations[0] if locations else "Kolkata"
    
    for i in range(random.randint(7, 13)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://jobsearchindia.com/job/{160000000 + i}",
            "description": f"Search and find the perfect {keywords} role for your career.",
            "requirements": f"{keywords} knowledge, Search skills, Analytical thinking",
            "salary": random.choice(salaries),
            "posted_date": "4 days ago"
        })
    
    return jobs


async def simulate_govtjobs_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Government Jobs India job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Central Govt", "State Govt", "Public Sector", "Government Agency", "Ministry Office", "Public Service Commission"]
    titles = [f"Government {keywords} Officer", f"Public Sector {keywords} Engineer", f"{keywords} Technical Assistant", f"Govt {keywords} Specialist"]
    salaries = ["₹4,00,000 - ₹8,00,000", "₹5,00,000 - ₹9,00,000", "₹6,00,000 - ₹10,00,000"]
    
    jobs = []
    location = locations[0] if locations else "New Delhi"
    
    for i in range(random.randint(4, 8)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://sarkariresult.com/job/{170000000 + i}",
            "description": f"Government opportunity for {keywords} professionals with job security.",
            "requirements": f"{keywords} qualification, Government exam, Indian citizen",
            "salary": random.choice(salaries),
            "posted_date": "1 week ago"
        })
    
    return jobs
