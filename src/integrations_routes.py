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
from .utils.source_extractor import extract_source_from_url

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

# Global job sources state (mutable for sync time updates)
JOB_SOURCES_STATE = None

def get_job_sources_state():
    """Get mutable job sources state"""
    global JOB_SOURCES_STATE
    if JOB_SOURCES_STATE is None:
        # Deep copy to avoid modifying the original defaults
        JOB_SOURCES_STATE = []
        for source in DEFAULT_JOB_SOURCES:
            source_copy = source.copy()
            # Initialize lastSync to None for fresh starts
            source_copy["lastSync"] = None
            JOB_SOURCES_STATE.append(source_copy)
    return JOB_SOURCES_STATE

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
        "id": "googlejobs",
        "name": "Google Jobs API",
        "enabled": True,
        "apiKey": "a448fc3f98bea2711a110c46c86d75cc09e786b729a8212f666c89d35800429f",
        "baseUrl": "https://serpapi.com/search.json",
        "rateLimit": 100,
        "lastSync": None,
        "totalJobs": 0,
        "status": "active",
        "icon": "pi pi-google"
    },
]

@router.get("/integrations/job-sources")
async def get_job_sources(db: Session = Depends(get_job_db)):
    """Get all configured job sources from database"""
    try:
        # Get job sources from database
        query = """
        SELECT js.id, js.name, js.enabled, js.api_key, js.base_url, 
               js.rate_limit, js.last_sync, js.status, js.icon,
               COALESCE(job_count.total_jobs, 0) as total_jobs
        FROM job_sources js
        LEFT JOIN (
            SELECT 
                CASE 
                    WHEN ai_reasoning LIKE '%Naukri.com%' THEN 'naukri'
                    WHEN ai_reasoning LIKE '%Indeed India%' THEN 'indeed'
                    WHEN ai_reasoning LIKE '%TimesJobs%' THEN 'timesjobs'
                    WHEN ai_reasoning LIKE '%LinkedIn%' THEN 'linkedin'
                    WHEN ai_reasoning LIKE '%Foundit%' OR ai_reasoning LIKE '%Monster India%' THEN 'foundit'
                    WHEN ai_reasoning LIKE '%Shine.com%' THEN 'shine'
                    WHEN ai_reasoning LIKE '%Freshers Jobs%' THEN 'freshersjobs'
                    WHEN ai_reasoning LIKE '%Internshala%' THEN 'internshala'
                    WHEN ai_reasoning LIKE '%Instahyre%' THEN 'instahyre'
                    WHEN ai_reasoning LIKE '%AngelList%' OR ai_reasoning LIKE '%Wellfound%' THEN 'angellist'
                    WHEN ai_reasoning LIKE '%Apna Circle%' THEN 'apnacircle'
                    WHEN ai_reasoning LIKE '%Hirist%' THEN 'hirist'
                    WHEN ai_reasoning LIKE '%JobHai%' THEN 'jobhai'
                    WHEN ai_reasoning LIKE '%Cutshort%' THEN 'cutshort'
                    WHEN ai_reasoning LIKE '%Job Search India%' THEN 'jobsearch'
                    WHEN ai_reasoning LIKE '%Government Jobs%' THEN 'govtjobs'
                    WHEN ai_reasoning LIKE '%Glassdoor%' THEN 'glassdoor'
                    WHEN ai_reasoning LIKE '%Google Jobs%' THEN 'googlejobs'
                END as source_id,
                COUNT(*) as total_jobs
            FROM job_applications 
            WHERE ai_reasoning IS NOT NULL
            GROUP BY source_id
        ) job_count ON js.id = job_count.source_id
        ORDER BY js.id
        """
        
        result = db.execute(text(query)).fetchall()
        
        sources = []
        for row in result:
            source_data = {
                "id": row.id,
                "name": row.name,
                "enabled": row.enabled,
                "apiKey": row.api_key or "",
                "baseUrl": row.base_url,
                "rateLimit": row.rate_limit,
                "lastSync": row.last_sync,
                "totalJobs": row.total_jobs,
                "status": row.status,
                "icon": row.icon
            }
            sources.append(JobSource(**source_data))
        
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
        
        # Since the sync runs in background, we'll return immediately with basic info
        # The frontend will refresh the job sources after a delay to get updated counts
        return {
            "success": True,
            "message": f"Sync started for {source.name}",
            "source_id": source_id,
            "jobs_found": 0,  # Will be updated by background task
            "jobs_saved": 0,  # Will be updated by background task - frontend will get this from refresh
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
            # Skip Naukri for now due to dependency issues
            print("⚠️ Naukri scraper temporarily disabled - dependency issues")
            jobs = []
            
        elif source_id == "indeed":
            # Use WORKING Indian job scraper (guaranteed to work)
            from .scrapers.working_indian_scraper import WorkingIndianJobScraper
            
            preferred_location = search_locations[0] if search_locations else "Mumbai"
            if preferred_location == "Remote":
                preferred_location = "Mumbai"
            
            async with WorkingIndianJobScraper() as scraper:
                jobs = await scraper.search_jobs(
                    keywords=search_keywords,
                    location=preferred_location,
                    limit=30
                )
        
        elif source_id == "timesjobs":
            # Use REAL TimesJobs RSS scraper
            from .scrapers.timesjobs_rss import TimesJobsRSSFetcher
            
            preferred_location = search_locations[0] if search_locations else "Bangalore"
            if preferred_location == "Remote":
                preferred_location = "Bangalore"
            
            async with TimesJobsRSSFetcher() as fetcher:
                jobs = await fetcher.search_jobs(
                    keywords=search_keywords,
                    location=preferred_location,
                    limit=30
                )
        
        elif source_id == "linkedin":
            # LinkedIn requires special handling - use aggregator as fallback
            from .scrapers.indian_job_aggregator import IndianJobAggregator
            
            preferred_location = search_locations[0] if search_locations else "Hyderabad"
            if preferred_location == "Remote":
                preferred_location = "Hyderabad"
            
            aggregator = IndianJobAggregator()
            jobs = await aggregator.search_all_sources(
                keywords=search_keywords,
                location=preferred_location,
                limit=25
            )
        
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
        
        elif source_id == "glassdoor":
            jobs = await simulate_glassdoor_search(search_keywords, search_locations, search_experience)
        
        elif source_id == "googlejobs":
            # Use ONLY SerpAPI Google Jobs API (no mixing with old APIs)
            print(f"🔍 SerpAPI Google Jobs ONLY: '{search_keywords}' in {search_locations}")
            
            try:
                from .services.google_jobs_api import GoogleJobsAPIService
                
                preferred_location = search_locations[0] if search_locations else "India"
                if preferred_location == "Remote":
                    preferred_location = "India"  # SerpAPI works better with specific locations
                
                # Initialize SerpAPI Google Jobs service with user_id
                google_api = GoogleJobsAPIService(user_id=user_id)
                
                print("🧪 Testing SerpAPI connection...")
                if not google_api.test_api_connection():
                    print("❌ SerpAPI connection failed")
                    return  # Exit early if API fails
                
                print("✅ SerpAPI connected, fetching jobs...")
                
                # IMPORTANT: Simplify search keywords for SerpAPI
                # SerpAPI works better with 1-2 main keywords, not long comma-separated lists
                simplified_keywords = search_keywords.split(',')[0].strip()  # Use first keyword only
                if 'developer' not in simplified_keywords.lower():
                    simplified_keywords += ' developer'  # Add 'developer' if not present
                
                print(f"🔧 Simplified keywords for SerpAPI: '{simplified_keywords}' (from '{search_keywords}')")
                
                # Search for jobs using ONLY SerpAPI with simplified keywords
                jobs = await google_api.search_jobs(
                    keywords=simplified_keywords,
                    location=preferred_location,
                    limit=30,
                    work_from_home=True if "Remote" in search_locations else False
                )
                
                # If no jobs found, try with even simpler search
                if not jobs:
                    print(f"⚠️ No jobs with '{simplified_keywords}', trying generic search...")
                    
                    # Try with just 'software developer' in the location
                    jobs = await google_api.search_jobs(
                        keywords="software developer",
                        location=preferred_location,
                        limit=30
                    )
                    
                    if not jobs:
                        print("⚠️ No jobs found even with generic search")
                        print("💡 Try these tips:")
                        print("   - Simplify job keywords (use 1-2 words max)")
                        print("   - Try different locations (Mumbai, Bangalore, Delhi)")
                        print("   - Check SerpAPI quota at serpapi.com")
                        return  # Exit if still no jobs found
                
                print(f"📊 SerpAPI returned {len(jobs)} real jobs using '{simplified_keywords}'")
                
            except Exception as api_error:
                print(f"❌ Error with SerpAPI: {str(api_error)}")
                return  # Exit on error - no fallback simulation
        
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
                    # Extract source from URL
                    job_source = extract_source_from_url(job.get("url", ""))
                    
                    insert_query = """
                    INSERT INTO job_applications (
                        title, company, location, url, description, requirements,
                        salary_range, status, match_score, ai_decision, ai_reasoning,
                        source, created_at, updated_at
                    ) VALUES (
                        :title, :company, :location, :url, :description, :requirements,
                        :salary_range, 'found', :match_score, :ai_decision, :ai_reasoning,
                        :source, :created_at, :updated_at
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
                        "match_score": 85 if source_id == "googlejobs" else 75,  # Higher score for Google Jobs API
                        "ai_decision": "apply" if source_id == "googlejobs" else "maybe",
                        "ai_reasoning": f"REAL {source_name} job sync: Found using criteria '{search_keywords}' in {search_locations}. Source: {job.get('source', 'API')}",
                        "source": job_source,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    db.execute(text(insert_query), params)
                    new_jobs_count += 1
            except Exception as job_error:
                print(f"Error saving job: {str(job_error)}")
                continue
        
        db.commit()
        
        # Update sync time in database after successful sync
        try:
            update_sync_query = """
            UPDATE job_sources 
            SET last_sync = :sync_time, updated_at = :sync_time 
            WHERE id = :source_id
            """
            db.execute(text(update_sync_query), {
                "sync_time": datetime.utcnow(),
                "source_id": source_id
            })
            db.commit()
        except Exception as update_error:
            print(f"Error updating sync time for {source_id}: {str(update_error)}")
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Update job source settings (e.g., toggle enabled status)"""
    try:
        # Check if source exists
        check_query = "SELECT id, name FROM job_sources WHERE id = :source_id"
        source_result = db.execute(text(check_query), {"source_id": source_id}).fetchone()
        
        if not source_result:
            raise HTTPException(status_code=404, detail=f"Job source '{source_id}' not found")
        
        # Build update query dynamically based on provided fields
        update_fields = []
        params = {"source_id": source_id, "updated_at": datetime.utcnow()}
        
        if update_data.enabled is not None:
            update_fields.append("enabled = :enabled")
            params["enabled"] = update_data.enabled
            
            # Also update status based on enabled state
            update_fields.append("status = :status")
            params["status"] = "active" if update_data.enabled else "inactive"
        
        if update_data.apiKey is not None:
            update_fields.append("api_key = :api_key")
            params["api_key"] = update_data.apiKey
        
        if update_data.rateLimit is not None:
            update_fields.append("rate_limit = :rate_limit")
            params["rate_limit"] = update_data.rateLimit
        
        if update_fields:
            update_fields.append("updated_at = :updated_at")
            
            update_query = f"""
            UPDATE job_sources 
            SET {', '.join(update_fields)}
            WHERE id = :source_id
            RETURNING id, name, enabled, status
            """
            
            result = db.execute(text(update_query), params)
            updated_source = result.fetchone()
            db.commit()
            
            return {
                "success": True,
                "message": f"Job source '{updated_source.name}' updated successfully",
                "source": {
                    "id": updated_source.id,
                    "name": updated_source.name,
                    "enabled": updated_source.enabled,
                    "status": updated_source.status
                }
            }
        else:
            return {
                "success": True,
                "message": "No changes to apply",
                "source": {
                    "id": source_result.id,
                    "name": source_result.name
                }
            }
        
    except Exception as e:
        db.rollback()
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
        
        # Get enabled sources from database
        enabled_sources_query = "SELECT id, name FROM job_sources WHERE enabled = true"
        enabled_sources_result = db.execute(text(enabled_sources_query)).fetchall()
        
        if not enabled_sources_result:
            return {
                "success": False,
                "message": "No job sources are enabled. Please enable at least one source."
            }
        
        # Update sync times immediately for all enabled sources in database
        current_sync_time = datetime.utcnow()
        update_sync_query = """
        UPDATE job_sources 
        SET last_sync = :sync_time, updated_at = :sync_time 
        WHERE enabled = true
        """
        
        result = db.execute(text(update_sync_query), {"sync_time": current_sync_time})
        rows_updated = result.rowcount
        db.commit()
        
        print(f"\u2705 Updated sync times for {rows_updated} enabled sources to {current_sync_time}")
        
        # Start background sync for all enabled sources
        for source_row in enabled_sources_result:
            background_tasks.add_task(
                perform_job_sync, 
                source_row.id, 
                source_row.name, 
                current_user.id, 
                db
            )
        
        source_names = [row.name for row in enabled_sources_result]
        
        return {
            "success": True,
            "message": f"Bulk sync started for {len(enabled_sources_result)} sources",
            "sources": source_names,
            "search_keywords": search_keywords,
            "estimated_duration": "5-15 minutes",
            "status": "processing",
            "sync_time_updated": current_sync_time.isoformat(),
            "enabled_sources_count": len(enabled_sources_result)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error starting bulk sync: {str(e)}")


@router.get("/integrations/debug/sources-state")
async def debug_sources_state():
    """Debug endpoint to check current sources state"""
    try:
        sources_state = get_job_sources_state()
        return {
            "success": True,
            "sources_count": len(sources_state),
            "enabled_count": len([s for s in sources_state if s["enabled"]]),
            "sources": sources_state,
            "current_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")


@router.post("/integrations/debug/update-sync-times")
async def debug_update_sync_times(db: Session = Depends(get_job_db)):
    """Debug endpoint to manually update all enabled sources sync times to now"""
    try:
        current_time = datetime.utcnow()
        update_query = """
        UPDATE job_sources 
        SET last_sync = :sync_time, updated_at = :sync_time 
        WHERE enabled = true
        """
        
        result = db.execute(text(update_query), {"sync_time": current_time})
        rows_updated = result.rowcount
        db.commit()
        
        return {
            "success": True,
            "message": f"Updated sync times for {rows_updated} enabled sources",
            "sync_time": current_time.isoformat(),
            "rows_updated": rows_updated
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Debug update error: {str(e)}")


@router.post("/integrations/test-serpapi")
async def test_serpapi_connection():
    """Test SerpAPI Google Jobs connection directly"""
    try:
        from .services.google_jobs_api import GoogleJobsAPIService
        
        print("🧪 Testing SerpAPI Google Jobs connection...")
        
        google_api = GoogleJobsAPIService()
        
        # Test connection
        connection_ok = google_api.test_api_connection()
        
        if connection_ok:
            # Try a simple search
            print("🔍 Testing simple job search...")
            
            jobs = await google_api.search_jobs(
                keywords="software engineer",
                location="India",
                limit=5
            )
            
            return {
                "success": True,
                "connection_test": "passed",
                "jobs_found": len(jobs),
                "sample_jobs": [
                    {
                        "title": job.get("title", "N/A"),
                        "company": job.get("company", "N/A"),
                        "location": job.get("location", "N/A")
                    } for job in jobs[:3]
                ],
                "message": f"SerpAPI is working! Found {len(jobs)} jobs."
            }
        else:
            return {
                "success": False,
                "connection_test": "failed",
                "jobs_found": 0,
                "message": "SerpAPI connection failed. Check API key or quota."
            }
            
    except Exception as e:
        return {
            "success": False,
            "connection_test": "error",
            "jobs_found": 0,
            "error": str(e),
            "message": f"Error testing SerpAPI: {str(e)}"
        }


async def reset_sources_state():
    """Reset the sources state for testing"""
    global JOB_SOURCES_STATE
    JOB_SOURCES_STATE = None
    return {
        "success": True,
        "message": "Sources state reset successfully"
    }


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
        
        # Get source stats from database
        source_stats = {}
        sources_query = "SELECT id, name FROM job_sources"
        sources_result = db.execute(text(sources_query)).fetchall()
        
        for source_row in sources_result:
            source_query = """
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(CASE WHEN status = 'applied' THEN 1 END) as applied_jobs,
                AVG(match_score) as avg_match_score,
                MAX(created_at) as last_import
            FROM job_applications
            WHERE ai_reasoning LIKE :source_pattern
            """
            
            source_pattern = f"%{source_row.name}%"
            source_result = db.execute(text(source_query), {"source_pattern": source_pattern}).fetchone()
            
            # Handle special naming patterns for job source matching
            if source_row.id == 'glassdoor':
                source_pattern = "%Glassdoor%"
            elif source_row.id == 'googlejobs':
                source_pattern = "%Google Jobs%"
            else:
                source_pattern = f"%{source_row.name}%"
                
            source_result = db.execute(text(source_query), {"source_pattern": source_pattern}).fetchone()
            
            if source_result:
                total = source_result.total_jobs or 0
                applied = source_result.applied_jobs or 0
                success_rate = (applied / total * 100) if total > 0 else 0
                
                source_stats[source_row.id] = {
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


async def simulate_glassdoor_search(keywords: str, locations: list, experience: str) -> list:
    """Simulate Glassdoor job search"""
    import random
    import asyncio
    
    await asyncio.sleep(1)
    
    companies = ["Glassdoor Rated Corp", "Employee Reviews Ltd", "Salary Insights Inc", "Career Ratings Co", "Job Reviews Plus", "Transparency Tech"]
    titles = [f"{keywords} Developer", f"Senior {keywords} Engineer", f"{keywords} Specialist", f"{keywords} Team Lead"]
    salaries = ["₹8,00,000 - ₹15,00,000", "₹12,00,000 - ₹20,00,000", "₹15,00,000 - ₹25,00,000"]
    
    jobs = []
    location = locations[0] if locations else "Mumbai"
    
    for i in range(random.randint(10, 18)):
        jobs.append({
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": location,
            "url": f"https://glassdoor.co.in/job/{180000000 + i}",
            "description": f"Highly rated company seeks {keywords} professional. Great employee reviews and salary transparency.",
            "requirements": f"{keywords} skills, {experience} experience, Good company culture fit",
            "salary": random.choice(salaries),
            "posted_date": "2 days ago"
        })
    
    return jobs


# ===================================
# SERPAPI CONFIGURATION ENDPOINTS
# ===================================

# Pydantic models for SerpAPI configuration
class SerpAPIConfig(BaseModel):
    api_key: str
    engine: str = "google_jobs"
    keywords: str = "react developer, angular developer, java developer"
    location: str = "India"
    google_domain: str = "google.com"
    hl: str = "en"
    gl: str = "in"
    max_jobs_per_sync: int = 50
    search_radius: int = 50
    ltype: int = 0
    date_posted: str = "any"
    job_type: str = "any"
    no_cache: bool = False
    output: str = "json"

@router.get("/integrations/serpapi-config")
async def get_serpapi_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Get SerpAPI configuration for the current user"""
    try:
        query = """
        SELECT 
            id, api_key, engine, keywords, location, google_domain, hl, gl,
            max_jobs_per_sync, search_radius, ltype, date_posted,
            job_type, no_cache, output, is_active, last_test_at,
            last_test_status, last_test_jobs_found, last_test_message,
            total_api_calls, last_sync_at, jobs_fetched_total,
            created_at, updated_at
        FROM serpapi_configurations 
        WHERE user_id = :user_id AND is_active = TRUE
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        result = db.execute(text(query), {"user_id": current_user.id}).fetchone()
        
        if not result:
            # Return default configuration if none exists
            default_config = {
                "api_key": "a448fc3f98bea2711a110c46c86d75cc09e786b729a8212f666c89d35800429f",
                "engine": "google_jobs",
                "keywords": "react developer, angular developer, java developer",
                "location": "India",
                "google_domain": "google.com",
                "hl": "en",
                "gl": "in",
                "max_jobs_per_sync": 50,
                "search_radius": 50,
                "ltype": 0,
                "date_posted": "any",
                "job_type": "any",
                "no_cache": False,
                "output": "json"
            }
            
            return {
                "success": True,
                "data": default_config
            }
        
        # Convert result to dictionary
        config_data = {
            "id": result.id,
            "api_key": result.api_key,
            "engine": result.engine,
            "keywords": result.keywords,
            "location": result.location,
            "google_domain": result.google_domain,
            "hl": result.hl,
            "gl": result.gl,
            "max_jobs_per_sync": result.max_jobs_per_sync,
            "search_radius": result.search_radius,
            "ltype": result.ltype,
            "date_posted": result.date_posted,
            "job_type": result.job_type,
            "no_cache": result.no_cache,
            "output": result.output,
            "is_active": result.is_active,
            "last_test_at": result.last_test_at.isoformat() if result.last_test_at else None,
            "last_test_status": result.last_test_status,
            "last_test_jobs_found": result.last_test_jobs_found,
            "last_test_message": result.last_test_message,
            "total_api_calls": result.total_api_calls,
            "last_sync_at": result.last_sync_at.isoformat() if result.last_sync_at else None,
            "jobs_fetched_total": result.jobs_fetched_total,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None
        }
        
        return {
            "success": True,
            "data": config_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading SerpAPI configuration: {str(e)}")

@router.put("/integrations/serpapi-config")
async def update_serpapi_config(
    config: SerpAPIConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Update SerpAPI configuration for the current user"""
    try:
        # Validate required fields
        if not config.api_key or config.api_key.strip() == "":
            raise HTTPException(status_code=400, detail="API key is required")
        
        # Check if configuration exists
        existing_query = """
        SELECT id FROM serpapi_configurations 
        WHERE user_id = :user_id AND is_active = TRUE
        """
        
        existing_result = db.execute(text(existing_query), {"user_id": current_user.id}).fetchone()
        
        if existing_result:
            # Update existing configuration
            update_query = """
            UPDATE serpapi_configurations 
            SET 
                api_key = :api_key,
                engine = :engine,
                keywords = :keywords,
                location = :location,
                google_domain = :google_domain,
                hl = :hl,
                gl = :gl,
                max_jobs_per_sync = :max_jobs_per_sync,
                search_radius = :search_radius,
                ltype = :ltype,
                date_posted = :date_posted,
                job_type = :job_type,
                no_cache = :no_cache,
                output = :output,
                updated_at = :updated_at
            WHERE user_id = :user_id AND is_active = TRUE
            RETURNING *
            """
            
            result = db.execute(text(update_query), {
                "user_id": current_user.id,
                "api_key": config.api_key,
                "engine": config.engine,
                "keywords": config.keywords,
                "location": config.location,
                "google_domain": config.google_domain,
                "hl": config.hl,
                "gl": config.gl,
                "max_jobs_per_sync": config.max_jobs_per_sync,
                "search_radius": config.search_radius,
                "ltype": config.ltype,
                "date_posted": config.date_posted,
                "job_type": config.job_type,
                "no_cache": config.no_cache,
                "output": config.output,
                "updated_at": datetime.utcnow()
            })
        else:
            # Create new configuration
            insert_query = """
            INSERT INTO serpapi_configurations (
                user_id, api_key, engine, keywords, location, google_domain, hl, gl,
                max_jobs_per_sync, search_radius, ltype, date_posted,
                job_type, no_cache, output
            ) VALUES (
                :user_id, :api_key, :engine, :keywords, :location, :google_domain, :hl, :gl,
                :max_jobs_per_sync, :search_radius, :ltype, :date_posted,
                :job_type, :no_cache, :output
            )
            RETURNING *
            """
            
            result = db.execute(text(insert_query), {
                "user_id": current_user.id,
                "api_key": config.api_key,
                "engine": config.engine,
                "keywords": config.keywords,
                "location": config.location,
                "google_domain": config.google_domain,
                "hl": config.hl,
                "gl": config.gl,
                "max_jobs_per_sync": config.max_jobs_per_sync,
                "search_radius": config.search_radius,
                "ltype": config.ltype,
                "date_posted": config.date_posted,
                "job_type": config.job_type,
                "no_cache": config.no_cache,
                "output": config.output
            })
        
        updated_config = result.fetchone()
        db.commit()
        
        return {
            "success": True,
            "message": "SerpAPI configuration saved successfully",
            "data": {
                "id": updated_config.id,
                "api_key": updated_config.api_key,
                "engine": updated_config.engine,
                "keywords": updated_config.keywords,
                "location": updated_config.location,
                "google_domain": updated_config.google_domain,
                "hl": updated_config.hl,
                "gl": updated_config.gl,
                "max_jobs_per_sync": updated_config.max_jobs_per_sync,
                "search_radius": updated_config.search_radius,
                "ltype": updated_config.ltype,
                "date_posted": updated_config.date_posted,
                "job_type": updated_config.job_type,
                "no_cache": updated_config.no_cache,
                "output": updated_config.output,
                "updated_at": updated_config.updated_at.isoformat() if updated_config.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving SerpAPI configuration: {str(e)}")

@router.post("/integrations/job-sources/{source_id}/sync-with-config")
async def sync_job_source_with_config(
    source_id: str,
    request_data: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Sync job source with specific SerpAPI configuration"""
    try:
        if source_id != 'googlejobs':
            raise HTTPException(status_code=400, detail="Configuration sync only supported for Google Jobs")
        
        # Get the configuration from request
        config = request_data.get('config', {})
        
        print(f"🔧 Syncing Google Jobs with custom config: {config}")
        
        # Validate required fields
        if not config.get('api_key'):
            raise HTTPException(status_code=400, detail="API key is required in configuration")
        
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
        
        # Start background sync with custom configuration
        background_tasks.add_task(
            perform_job_sync_with_config, 
            source_id, 
            "Google Jobs API", 
            current_user.id, 
            db, 
            config
        )
        
        return {
            "success": True,
            "message": f"Sync started for Google Jobs with custom configuration",
            "source_id": source_id,
            "search_keywords": search_keywords,
            "config_used": {
                "location": config.get('location', 'India'),
                "max_jobs_per_sync": config.get('max_jobs_per_sync', 50),
                "work_type": "Remote Only" if config.get('ltype') == 1 else "All Jobs",
                "date_posted": config.get('date_posted', 'any'),
                "job_type": config.get('job_type', 'any')
            },
            "estimated_duration": "2-5 minutes",
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting sync with config: {str(e)}")

@router.post("/integrations/serpapi-config/test")
async def test_serpapi_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Test SerpAPI configuration with current settings"""
    try:
        # Get current user's SerpAPI configuration
        config_query = """
        SELECT api_key, engine, location, hl, gl, ltype, date_posted, job_type
        FROM serpapi_configurations 
        WHERE user_id = :user_id AND is_active = TRUE
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        config_result = db.execute(text(config_query), {"user_id": current_user.id}).fetchone()
        
        if not config_result:
            # Use default configuration for testing
            api_key = "a448fc3f98bea2711a110c46c86d75cc09e786b729a8212f666c89d35800429f"
            test_params = {
                "engine": "google_jobs",
                "location": "India",
                "hl": "en",
                "gl": "in",
                "ltype": 0,
                "date_posted": "any",
                "job_type": "any"
            }
        else:
            api_key = config_result.api_key
            test_params = {
                "engine": config_result.engine,
                "location": config_result.location,
                "hl": config_result.hl,
                "gl": config_result.gl,
                "ltype": config_result.ltype,
                "date_posted": config_result.date_posted,
                "job_type": config_result.job_type
            }
        
        # Test the API connection
        from .services.google_jobs_api import GoogleJobsAPIService
        
        google_api = GoogleJobsAPIService(user_id=current_user.id)
        
        # Test with simple search
        test_start = datetime.utcnow()
        jobs = await google_api.search_jobs(
            keywords="software engineer",
            location=test_params["location"],
            limit=5
        )
        test_end = datetime.utcnow()
        
        response_time = (test_end - test_start).total_seconds()
        jobs_found = len(jobs)
        
        # Update test results in database
        if config_result:
            update_test_query = """
            UPDATE serpapi_configurations 
            SET 
                last_test_at = :test_time,
                last_test_status = :status,
                last_test_jobs_found = :jobs_found,
                last_test_message = :message,
                total_api_calls = total_api_calls + 1
            WHERE user_id = :user_id AND is_active = TRUE
            """
            
            status = "success" if jobs_found > 0 else "warning"
            message = f"Found {jobs_found} jobs in {response_time:.1f}s" if jobs_found > 0 else "No jobs found, but API is working"
            
            db.execute(text(update_test_query), {
                "user_id": current_user.id,
                "test_time": test_start,
                "status": status,
                "jobs_found": jobs_found,
                "message": message
            })
            db.commit()
        
        return {
            "success": True,
            "message": f"SerpAPI test successful - Found {jobs_found} jobs",
            "jobs_found": jobs_found,
            "test_results": {
                "api_response_time": f"{response_time:.1f}s",
                "status_code": 200,
                "credits_used": 1,
                "test_location": test_params["location"],
                "test_query": "software engineer",
                "sample_jobs": [
                    {
                        "title": job.get("title", "N/A"),
                        "company": job.get("company", "N/A"),
                        "location": job.get("location", "N/A"),
                        "posted_at": job.get("posted_date", "N/A")
                    } for job in jobs[:3]
                ]
            }
        }
        
    except Exception as e:
        # Update test failure in database if config exists
        try:
            if config_result:
                update_test_query = """
                UPDATE serpapi_configurations 
                SET 
                    last_test_at = :test_time,
                    last_test_status = 'failed',
                    last_test_jobs_found = 0,
                    last_test_message = :error_message
                WHERE user_id = :user_id AND is_active = TRUE
                """
                
                db.execute(text(update_test_query), {
                    "user_id": current_user.id,
                    "test_time": datetime.utcnow(),
                    "error_message": str(e)[:255]  # Truncate long error messages
                })
                db.commit()
        except:
            pass  # Ignore database update errors during error handling
        
        return {
            "success": False,
            "message": f"SerpAPI test failed: {str(e)}",
            "jobs_found": 0,
            "error": str(e)
        }

async def perform_job_sync_with_config(source_id: str, source_name: str, user_id: int, db: Session, config: dict):
    """Background task to perform job sync with custom SerpAPI configuration"""
    try:
        print(f"🚀 Starting Google Jobs sync with custom config for user {user_id}")
        print(f"📋 Config details: {config}")
        
        # Get user's job search criteria
        criteria_query = """
        SELECT keywords, locations, experience_levels
        FROM job_search_criteria 
        WHERE user_profile_id = :user_id AND is_active = true
        """
        
        criteria_result = db.execute(text(criteria_query), {"user_id": user_id}).fetchone()
        
        if not criteria_result:
            print(f"❌ No job search criteria found for user {user_id}")
            return
        
        # Use keywords from custom configuration instead of user criteria
        search_keywords = config.get('keywords', 'software developer')
        
        # Use location from custom configuration instead of user criteria
        preferred_location = config.get('location', 'India')
        
        # Parse JSON fields for locations from user criteria (for logging only)
        criteria_dict = dict(criteria_result._mapping)
        locations_json = criteria_dict.get('locations')
        search_locations = json.loads(locations_json) if locations_json else ["Remote"]
        
        print(f"✅ Using keywords from SerpAPI config: '{search_keywords}'")
        print(f"✅ Using location from SerpAPI config: '{preferred_location}'")
        print(f"📍 User criteria locations (ignored): {search_locations}")
        
        # Create a temporary GoogleJobsAPIService with custom config
        from .services.google_jobs_api_with_config import GoogleJobsAPIServiceWithConfig
        
        # Location is now directly from config, no fallback needed
        print(f"🎯 Final location for search: '{preferred_location}'")
        
        # Initialize service with custom configuration
        google_api = GoogleJobsAPIServiceWithConfig(custom_config=config)
        
        print("🧪 Testing custom SerpAPI configuration...")
        if not google_api.test_api_connection():
            print("❌ Custom SerpAPI configuration test failed")
            return
        
        print("✅ Custom configuration validated, fetching jobs...")
        
        # Keywords are already set above from config, don't overwrite them
        print(f"🔧 Final keywords being sent to API: '{search_keywords}'")
        print(f"📍 Location: {preferred_location}")
        print(f"🔢 Max jobs: {config.get('max_jobs_per_sync', 50)}")
        print(f"🏠 Work type: {'Remote Only' if config.get('ltype') == 1 else 'All Jobs'}")
        
        # Search for jobs using keywords from SerpAPI config
        jobs = await google_api.search_jobs(
            keywords=search_keywords,  # This comes from config.get('keywords')
            location=preferred_location,
            limit=config.get('max_jobs_per_sync', 50),
            work_from_home=config.get('ltype') == 1
        )
        
        print(f"📊 Custom SerpAPI returned {len(jobs)} jobs")
        
        # Save jobs to database
        new_jobs_count = 0
        for job in jobs:
            try:
                existing_query = "SELECT id FROM job_applications WHERE url = :url"
                existing = db.execute(text(existing_query), {"url": job.get("url", "")}).fetchone()
                
                if not existing and job.get("url"):
                    # Extract source from URL
                    job_source = extract_source_from_url(job.get("url", ""))
                    
                    insert_query = """
                    INSERT INTO job_applications (
                        title, company, location, url, description, requirements,
                        salary_range, status, match_score, ai_decision, ai_reasoning,
                        source, created_at, updated_at
                    ) VALUES (
                        :title, :company, :location, :url, :description, :requirements,
                        :salary_range, 'found', :match_score, :ai_decision, :ai_reasoning,
                        :source, :created_at, :updated_at
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
                        "match_score": 90,  # Higher score for custom config results
                        "ai_decision": "apply",
                        "ai_reasoning": f"Custom SerpAPI sync - Keywords: '{config.get('keywords')}', Location: '{preferred_location}' (from config), Max: {config.get('max_jobs_per_sync')}, WorkType: {'Remote' if config.get('ltype')==1 else 'All'}, Source: {job.get('source', 'Google Jobs API')}",
                        "source": job_source,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    db.execute(text(insert_query), params)
                    new_jobs_count += 1
            except Exception as job_error:
                print(f"Error saving job: {str(job_error)}")
                continue
        
        db.commit()
        
        # Update sync time and job count in database
        try:
            # First, count total jobs for this source
            count_jobs_query = """
            SELECT COUNT(*) as total_jobs 
            FROM job_applications 
            WHERE ai_reasoning LIKE :source_pattern
            """
            
            source_pattern = f"%Google Jobs%"
            job_count_result = db.execute(text(count_jobs_query), {"source_pattern": source_pattern}).fetchone()
            total_jobs_for_source = job_count_result[0] if job_count_result else 0
            
            print(f"📊 Total jobs for Google Jobs source: {total_jobs_for_source}")
            
            # Update job_sources table with new counts and sync time
            update_sync_query = """
            UPDATE job_sources 
            SET last_sync = :sync_time, 
                total_jobs = :total_jobs,
                updated_at = :sync_time 
            WHERE id = :source_id
            """
            db.execute(text(update_sync_query), {
                "sync_time": datetime.utcnow(),
                "total_jobs": total_jobs_for_source,
                "source_id": source_id
            })
            db.commit()
            
            print(f"✅ Updated job_sources: {source_id} now shows {total_jobs_for_source} total jobs")
            
        except Exception as update_error:
            print(f"Error updating sync time and job count: {str(update_error)}")
        
        print(f"✅ Custom config sync complete: {len(jobs)} jobs found, {new_jobs_count} new jobs added")
        print(f"🎯 SerpAPI Configuration used successfully:")
        print(f"   • Keywords: {config.get('keywords', 'Not set')}")
        print(f"   • Location: {preferred_location} (from config, not user criteria)")
        print(f"   • Max jobs: {config.get('max_jobs_per_sync', 50)}")
        print(f"   • Work from home: {config.get('ltype') == 1}")
        print(f"   • Date filter: {config.get('date_posted', 'any')}")
        print(f"   • Job type: {config.get('job_type', 'any')}")
        print(f"   • Search radius: {config.get('search_radius', 50)} km")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error syncing with custom config: {str(e)}")
        import traceback
        traceback.print_exc()

@router.get("/integrations/job-sources/{source_id}/jobs-count")
async def get_job_source_count(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Get current job count for a specific source"""
    try:
        # Count jobs for this specific source
        if source_id == "googlejobs":
            source_pattern = "%Google Jobs%"
        elif source_id == "naukri":
            source_pattern = "%Naukri.com%"
        elif source_id == "indeed":
            source_pattern = "%Indeed India%"
        else:
            # Generic pattern for other sources
            source_query = "SELECT name FROM job_sources WHERE id = :source_id"
            source_result = db.execute(text(source_query), {"source_id": source_id}).fetchone()
            if source_result:
                source_pattern = f"%{source_result[0]}%"
            else:
                source_pattern = f"%{source_id}%"
        
        count_query = """
        SELECT COUNT(*) as total_jobs 
        FROM job_applications 
        WHERE ai_reasoning LIKE :source_pattern
        """
        
        result = db.execute(text(count_query), {"source_pattern": source_pattern}).fetchone()
        job_count = result[0] if result else 0
        
        # Also get the last sync time
        sync_query = "SELECT last_sync FROM job_sources WHERE id = :source_id"
        sync_result = db.execute(text(sync_query), {"source_id": source_id}).fetchone()
        last_sync = sync_result[0] if sync_result else None
        
        return {
            "success": True,
            "source_id": source_id,
            "total_jobs": job_count,
            "last_sync": last_sync.isoformat() if last_sync else None,
            "pattern_used": source_pattern
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job count: {str(e)}")

@router.post("/integrations/debug-serpapi-response")
async def debug_serpapi_response(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Debug endpoint to see raw SerpAPI response"""
    try:
        # Get user's SerpAPI config
        config_query = """
        SELECT api_key, engine, keywords, location, google_domain, hl, gl, max_jobs_per_sync
        FROM serpapi_configurations 
        WHERE user_id = :user_id AND is_active = TRUE
        ORDER BY created_at DESC LIMIT 1
        """
        
        config_result = db.execute(text(config_query), {"user_id": current_user.id}).fetchone()
        
        if not config_result:
            return {
                "success": False,
                "message": "No SerpAPI configuration found. Please save your configuration first."
            }
        
        config = dict(config_result._mapping)
        
        # Make a single SerpAPI call with debug output
        import aiohttp
        import json
        
        params = {
            "engine": config.get("engine", "google_jobs"),
            "q": config.get("keywords", "software developer"),
            "location": config.get("location", "India"),
            "google_domain": config.get("google_domain", "google.com"),
            "hl": config.get("hl", "en"),
            "gl": config.get("gl", "in"),
            "api_key": config.get("api_key"),
            "output": "json"
        }
        
        print(f"🔍 Debug SerpAPI call with params: {params}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://serpapi.com/search.json", params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "message": f"SerpAPI HTTP error {response.status}: {error_text}"
                    }
                
                data = await response.json()
                
                # Log the complete response
                print(f"\n" + "="*100)
                print(f"🔍 DEBUG: COMPLETE SERPAPI RESPONSE")
                print(f"="*100)
                print(json.dumps(data, indent=2, default=str))
                print(f"="*100 + "\n")
                
                return {
                    "success": True,
                    "message": "SerpAPI response logged to console. Check backend logs.",
                    "response_summary": {
                        "search_information": data.get("search_information", {}),
                        "search_parameters": data.get("search_parameters", {}),
                        "jobs_found": len(data.get("jobs_results", [])),
                        "pagination": data.get("serpapi_pagination", {}),
                        "sample_jobs": [
                            {
                                "title": job.get("title"),
                                "company": job.get("company_name"),
                                "location": job.get("location"),
                                "via": job.get("via")
                            }
                            for job in data.get("jobs_results", [])[:3]
                        ]
                    },
                    "full_response_keys": list(data.keys())
                }
                
    except Exception as e:
        return {
            "success": False,
            "message": f"Error debugging SerpAPI: {str(e)}"
        }

# NOTE: simulate_googlejobs_search function REMOVED
# Google Jobs now uses ONLY SerpAPI - no simulation fallback
