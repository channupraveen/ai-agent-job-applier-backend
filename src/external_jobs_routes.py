"""
External Job Site Integration API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import requests
import asyncio

from .auth import get_current_user
from .models import get_job_db, UserProfile as User

router = APIRouter(tags=["External Job Site Integration"])

class JobSearchRequest(BaseModel):
    keywords: str
    location: Optional[str] = "Remote"
    experience_level: Optional[str] = "mid-level"
    job_type: Optional[str] = "full-time"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    date_posted: Optional[str] = "week"  # day, 3days, week, month
    limit: int = 50

class BulkJobSearchRequest(BaseModel):
    sources: List[str] = ["linkedin", "indeed", "naukri"]
    search_params: JobSearchRequest
    save_to_database: bool = True

@router.get("/jobs/external/sources")
async def get_available_job_sources(
    current_user: User = Depends(get_current_user)
):
    """List available external job sources"""
    try:
        job_sources = [
            {
                "id": "linkedin",
                "name": "LinkedIn Jobs",
                "description": "Professional networking platform with job listings",
                "supported_features": ["keyword_search", "location_filter", "experience_filter", "salary_filter"],
                "rate_limit": "100 requests per hour",
                "requires_auth": True,
                "status": "active"
            },
            {
                "id": "indeed",
                "name": "Indeed",
                "description": "Global job search engine",
                "supported_features": ["keyword_search", "location_filter", "salary_filter", "date_posted"],
                "rate_limit": "200 requests per hour",
                "requires_auth": False,
                "status": "active"
            },
            {
                "id": "naukri",
                "name": "Naukri.com",
                "description": "Leading job portal in India",
                "supported_features": ["keyword_search", "location_filter", "experience_filter", "industry_filter"],
                "rate_limit": "150 requests per hour",
                "requires_auth": False,
                "status": "active"
            },
            {
                "id": "glassdoor",
                "name": "Glassdoor",
                "description": "Job search with company reviews and salary insights",
                "supported_features": ["keyword_search", "location_filter", "company_ratings", "salary_insights"],
                "rate_limit": "50 requests per hour",
                "requires_auth": True,
                "status": "beta"
            },
            {
                "id": "monster",
                "name": "Monster.com",
                "description": "Global job board",
                "supported_features": ["keyword_search", "location_filter", "experience_filter"],
                "rate_limit": "100 requests per hour",
                "requires_auth": False,
                "status": "maintenance"
            }
        ]
        
        return {
            "success": True,
            "job_sources": job_sources,
            "total_sources": len(job_sources),
            "active_sources": len([s for s in job_sources if s["status"] == "active"])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job sources: {str(e)}")

@router.post("/jobs/external/linkedin")
async def search_linkedin_jobs(
    search_request: JobSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Search LinkedIn jobs"""
    try:
        # Simulate LinkedIn job search (in real implementation, use LinkedIn API)
        jobs_found = await simulate_linkedin_search(search_request)
        
        # Calculate match scores for user
        user_skills = json.loads(current_user.skills or "[]")
        processed_jobs = []
        
        for job in jobs_found:
            # Calculate compatibility score
            match_score = calculate_job_match_score(job, user_skills)
            job["match_score"] = match_score
            job["ai_decision"] = get_recommendation_from_score(match_score)
            job["source"] = "linkedin"
            processed_jobs.append(job)
        
        # Save to database if requested
        saved_jobs = []
        for job_data in processed_jobs:
            try:
                # Check if job already exists
                existing_query = "SELECT id FROM job_applications WHERE url = :url"
                existing = db.execute(text(existing_query), {"url": job_data.get("url", "")}).fetchone()
                
                if not existing and job_data.get("url"):
                    insert_query = """
                    INSERT INTO job_applications (
                        title, company, location, url, description, requirements,
                        salary_range, status, match_score, ai_decision, ai_reasoning,
                        created_at, updated_at
                    ) VALUES (
                        :title, :company, :location, :url, :description, :requirements,
                        :salary_range, 'found', :match_score, :ai_decision, :ai_reasoning,
                        :created_at, :updated_at
                    ) RETURNING id, title, company
                    """
                    
                    params = {
                        "title": job_data.get("title", ""),
                        "company": job_data.get("company", ""),
                        "location": job_data.get("location", ""),
                        "url": job_data.get("url", ""),
                        "description": job_data.get("description", ""),
                        "requirements": job_data.get("requirements", ""),
                        "salary_range": job_data.get("salary", ""),
                        "match_score": job_data["match_score"],
                        "ai_decision": job_data["ai_decision"],
                        "ai_reasoning": f"LinkedIn job match: {job_data['match_score']}% compatibility",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    result = db.execute(text(insert_query), params)
                    saved_job = result.fetchone()
                    if saved_job:
                        saved_jobs.append(dict(saved_job._mapping))
            except Exception as job_error:
                continue  # Skip problematic jobs
        
        db.commit()
        
        return {
            "success": True,
            "message": f"LinkedIn search completed. Found {len(jobs_found)} jobs",
            "search_params": search_request.dict(),
            "jobs_found": len(jobs_found),
            "jobs_saved": len(saved_jobs),
            "high_match_jobs": len([j for j in processed_jobs if j["match_score"] >= 80]),
            "jobs": processed_jobs[:10],  # Return first 10 for preview
            "source": "LinkedIn"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error searching LinkedIn jobs: {str(e)}")

@router.post("/jobs/external/indeed")
async def search_indeed_jobs(
    search_request: JobSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Search Indeed jobs"""
    try:
        # Simulate Indeed job search
        jobs_found = await simulate_indeed_search(search_request)
        
        user_skills = json.loads(current_user.skills or "[]")
        processed_jobs = []
        
        for job in jobs_found:
            match_score = calculate_job_match_score(job, user_skills)
            job["match_score"] = match_score
            job["ai_decision"] = get_recommendation_from_score(match_score)
            job["source"] = "indeed"
            processed_jobs.append(job)
        
        # Save to database
        saved_jobs = []
        for job_data in processed_jobs:
            try:
                existing_query = "SELECT id FROM job_applications WHERE url = :url"
                existing = db.execute(text(existing_query), {"url": job_data.get("url", "")}).fetchone()
                
                if not existing and job_data.get("url"):
                    insert_query = """
                    INSERT INTO job_applications (
                        title, company, location, url, description, requirements,
                        salary_range, status, match_score, ai_decision, ai_reasoning,
                        created_at, updated_at
                    ) VALUES (
                        :title, :company, :location, :url, :description, :requirements,
                        :salary_range, 'found', :match_score, :ai_decision, :ai_reasoning,
                        :created_at, :updated_at
                    ) RETURNING id
                    """
                    
                    params = {
                        "title": job_data.get("title", ""),
                        "company": job_data.get("company", ""),
                        "location": job_data.get("location", ""),
                        "url": job_data.get("url", ""),
                        "description": job_data.get("description", ""),
                        "requirements": job_data.get("requirements", ""),
                        "salary_range": job_data.get("salary", ""),
                        "match_score": job_data["match_score"],
                        "ai_decision": job_data["ai_decision"],
                        "ai_reasoning": f"Indeed job match: {job_data['match_score']}% compatibility",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    result = db.execute(text(insert_query), params)
                    if result.fetchone():
                        saved_jobs.append(job_data["title"])
            except Exception:
                continue
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Indeed search completed. Found {len(jobs_found)} jobs",
            "jobs_found": len(jobs_found),
            "jobs_saved": len(saved_jobs),
            "high_match_jobs": len([j for j in processed_jobs if j["match_score"] >= 80]),
            "jobs": processed_jobs[:10],
            "source": "Indeed"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error searching Indeed jobs: {str(e)}")

@router.post("/jobs/external/naukri")
async def search_naukri_jobs(
    search_request: JobSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db)
):
    """Search Naukri.com jobs"""
    try:
        # Simulate Naukri job search
        jobs_found = await simulate_naukri_search(search_request)
        
        user_skills = json.loads(current_user.skills or "[]")
        processed_jobs = []
        
        for job in jobs_found:
            match_score = calculate_job_match_score(job, user_skills)
            job["match_score"] = match_score
            job["ai_decision"] = get_recommendation_from_score(match_score)
            job["source"] = "naukri"
            processed_jobs.append(job)

        # Save to database
        saved_jobs = []
        for job_data in processed_jobs:
            try:
                existing_query = "SELECT id FROM job_applications WHERE url = :url"
                existing = db.execute(text(existing_query), {"url": job_data.get("url", "")}).fetchone()

                if not existing and job_data.get("url"):
                    insert_query = """
                    INSERT INTO job_applications (
                        title, company, location, url, description, requirements,
                        salary_range, status, match_score, ai_decision, ai_reasoning,
                        created_at, updated_at
                    ) VALUES (
                        :title, :company, :location, :url, :description, :requirements,
                        :salary_range, 'found', :match_score, :ai_decision, :ai_reasoning,
                        :created_at, :updated_at
                    ) RETURNING id
                    """

                    params = {
                        "title": job_data.get("title", ""),
                        "company": job_data.get("company", ""),
                        "location": job_data.get("location", ""),
                        "url": job_data.get("url", ""),
                        "description": job_data.get("description", ""),
                        "requirements": job_data.get("requirements", ""),
                        "salary_range": job_data.get("salary", ""),
                        "match_score": job_data["match_score"],
                        "ai_decision": job_data["ai_decision"],
                        "ai_reasoning": f"Naukri job match: {job_data['match_score']}% compatibility",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }

                    result = db.execute(text(insert_query), params)
                    if result.fetchone():
                        saved_jobs.append(job_data["title"])
            except Exception:
                continue

        db.commit()

        return {
            "success": True,
            "message": f"Naukri search completed. Found {len(jobs_found)} jobs",
            "jobs_found": len(jobs_found),
            "jobs_saved": len(saved_jobs),
            "high_match_jobs": len([j for j in processed_jobs if j["match_score"] >= 80]),
            "jobs": processed_jobs[:10],
            "source": "Naukri.com"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error searching Naukri jobs: {str(e)}")

@router.post("/jobs/external/glassdoor")
async def search_glassdoor_jobs(
   search_request: JobSearchRequest,
   background_tasks: BackgroundTasks,
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_job_db)
):
   """Search Glassdoor jobs with company ratings"""
   try:
       # Simulate Glassdoor job search
       jobs_found = await simulate_glassdoor_search(search_request)
       
       user_skills = json.loads(current_user.skills or "[]")
       processed_jobs = []
       
       for job in jobs_found:
           match_score = calculate_job_match_score(job, user_skills)
           job["match_score"] = match_score
           job["ai_decision"] = get_recommendation_from_score(match_score)
           job["source"] = "glassdoor"
           # Add Glassdoor-specific data
           job["company_rating"] = job.get("company_rating", 4.0)
           job["salary_estimate"] = job.get("salary_estimate", "Competitive")
           processed_jobs.append(job)
       
       return {
           "success": True,
           "message": f"Glassdoor search completed. Found {len(jobs_found)} jobs",
           "jobs_found": len(jobs_found),
           "average_company_rating": sum(j.get("company_rating", 0) for j in processed_jobs) / max(len(processed_jobs), 1),
           "jobs": processed_jobs[:10],
           "source": "Glassdoor"
       }
       
   except Exception as e:
       raise HTTPException(status_code=500, detail=f"Error searching Glassdoor jobs: {str(e)}")

@router.post("/jobs/external/bulk-search")
async def bulk_search_all_sources(
   bulk_request: BulkJobSearchRequest,
   background_tasks: BackgroundTasks,
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_job_db)
):
   """Search jobs from multiple sources simultaneously"""
   try:
       results = {}
       total_jobs_found = 0
       total_jobs_saved = 0
       
       # Search each source
       for source in bulk_request.sources:
           try:
               if source == "linkedin":
                   source_jobs = await simulate_linkedin_search(bulk_request.search_params)
               elif source == "indeed":
                   source_jobs = await simulate_indeed_search(bulk_request.search_params)
               elif source == "naukri":
                   source_jobs = await simulate_naukri_search(bulk_request.search_params)
               elif source == "glassdoor":
                   source_jobs = await simulate_glassdoor_search(bulk_request.search_params)
               else:
                   continue
               
               # Process jobs for this source
               user_skills = json.loads(current_user.skills or "[]")
               processed_jobs = []
               
               for job in source_jobs:
                   match_score = calculate_job_match_score(job, user_skills)
                   job["match_score"] = match_score
                   job["ai_decision"] = get_recommendation_from_score(match_score)
                   job["source"] = source
                   processed_jobs.append(job)
               
               # Save to database if requested
               saved_count = 0
               if bulk_request.save_to_database:
                   for job_data in processed_jobs:
                       try:
                           existing_query = "SELECT id FROM job_applications WHERE url = :url"
                           existing = db.execute(text(existing_query), {"url": job_data.get("url", "")}).fetchone()
                           
                           if not existing and job_data.get("url"):
                               insert_query = """
                               INSERT INTO job_applications (
                                   title, company, location, url, description, requirements,
                                   salary_range, status, match_score, ai_decision, ai_reasoning,
                                   created_at, updated_at
                               ) VALUES (
                                   :title, :company, :location, :url, :description, :requirements,
                                   :salary_range, 'found', :match_score, :ai_decision, :ai_reasoning,
                                   :created_at, :updated_at
                               ) RETURNING id
                               """
                               
                               params = {
                                   "title": job_data.get("title", ""),
                                   "company": job_data.get("company", ""),
                                   "location": job_data.get("location", ""),
                                   "url": job_data.get("url", ""),
                                   "description": job_data.get("description", ""),
                                   "requirements": job_data.get("requirements", ""),
                                   "salary_range": job_data.get("salary", ""),
                                   "match_score": job_data["match_score"],
                                   "ai_decision": job_data["ai_decision"],
                                   "ai_reasoning": f"{source.title()} job match: {job_data['match_score']}% compatibility",
                                   "created_at": datetime.utcnow(),
                                   "updated_at": datetime.utcnow()
                               }
                               
                               result = db.execute(text(insert_query), params)
                               if result.fetchone():
                                   saved_count += 1
                       except Exception:
                           continue
               
               results[source] = {
                   "jobs_found": len(source_jobs),
                   "jobs_saved": saved_count,
                   "high_match_jobs": len([j for j in processed_jobs if j["match_score"] >= 80]),
                   "average_match_score": sum(j["match_score"] for j in processed_jobs) / max(len(processed_jobs), 1),
                   "top_jobs": processed_jobs[:3]  # Top 3 jobs from this source
               }
               
               total_jobs_found += len(source_jobs)
               total_jobs_saved += saved_count
               
           except Exception as source_error:
               results[source] = {
                   "error": str(source_error),
                   "jobs_found": 0,
                   "jobs_saved": 0
               }
       
       if bulk_request.save_to_database:
           db.commit()
       
       return {
           "success": True,
           "message": f"Bulk search completed across {len(bulk_request.sources)} sources",
           "summary": {
               "total_jobs_found": total_jobs_found,
               "total_jobs_saved": total_jobs_saved,
               "sources_searched": len(bulk_request.sources),
               "search_duration": "2-5 minutes"
           },
           "source_results": results,
           "search_params": bulk_request.search_params.dict()
       }
       
   except Exception as e:
       if bulk_request.save_to_database:
           db.rollback()
       raise HTTPException(status_code=500, detail=f"Error in bulk search: {str(e)}")

@router.get("/jobs/external/stats")
async def get_external_job_stats(
   days_back: int = Query(7, ge=1, le=90),
   current_user: User = Depends(get_current_user),
   db: Session = Depends(get_job_db)
):
   """Get statistics on externally sourced jobs"""
   try:
       start_date = datetime.utcnow() - timedelta(days=days_back)
       
       # This would require adding a 'source' column to job_applications table
       stats_query = """
       SELECT 
           COUNT(*) as total_external_jobs,
           COUNT(CASE WHEN ai_reasoning LIKE '%LinkedIn%' THEN 1 END) as linkedin_jobs,
           COUNT(CASE WHEN ai_reasoning LIKE '%Indeed%' THEN 1 END) as indeed_jobs,
           COUNT(CASE WHEN ai_reasoning LIKE '%Naukri%' THEN 1 END) as naukri_jobs,
           COUNT(CASE WHEN ai_reasoning LIKE '%Glassdoor%' THEN 1 END) as glassdoor_jobs,
           AVG(match_score) as avg_match_score,
           COUNT(CASE WHEN applied_at IS NOT NULL THEN 1 END) as applied_count
       FROM job_applications
       WHERE created_at >= :start_date
       AND ai_reasoning IS NOT NULL
       """
       
       result = db.execute(text(stats_query), {"start_date": start_date})
       stats = dict(result.fetchone()._mapping)
       
       # Calculate source distribution
       total_external = stats["total_external_jobs"] or 1
       source_distribution = {
           "linkedin": round((stats["linkedin_jobs"] / total_external) * 100, 1),
           "indeed": round((stats["indeed_jobs"] / total_external) * 100, 1),
           "naukri": round((stats["naukri_jobs"] / total_external) * 100, 1),
           "glassdoor": round((stats["glassdoor_jobs"] / total_external) * 100, 1)
       }
       
       return {
           "success": True,
           "period": f"Last {days_back} days",
           "external_job_stats": stats,
           "source_distribution": source_distribution,
           "insights": {
               "most_productive_source": max(source_distribution, key=source_distribution.get),
               "application_rate": round((stats["applied_count"] / max(total_external, 1)) * 100, 1)
           }
       }
       
   except Exception as e:
       raise HTTPException(status_code=500, detail=f"Error getting external job stats: {str(e)}")

# Helper functions
async def simulate_linkedin_search(search_request: JobSearchRequest) -> List[Dict]:
   """Simulate LinkedIn job search"""
   await asyncio.sleep(1)  # Simulate API call delay
   
   jobs = [
       {
           "title": f"Senior {search_request.keywords} Developer",
           "company": "Tech Corp",
           "location": search_request.location,
           "url": "https://linkedin.com/jobs/12345",
           "description": f"We're looking for an experienced {search_request.keywords} developer to join our team.",
           "requirements": f"{search_request.keywords}, REST APIs, Database design, Problem solving",
           "salary": "₹15,00,000 - ₹25,00,000",
           "posted_date": "2 days ago",
           "job_type": search_request.job_type
       },
       {
           "title": f"{search_request.keywords} Engineer",
           "company": "Innovation Labs",
           "location": search_request.location,
           "url": "https://linkedin.com/jobs/12346",
           "description": f"Join our dynamic team working with {search_request.keywords} technologies.",
           "requirements": f"{search_request.keywords}, Agile, Team collaboration, Git",
           "salary": "₹12,00,000 - ₹18,00,000",
           "posted_date": "1 week ago",
           "job_type": search_request.job_type
       }
   ]
   
   return jobs

async def simulate_indeed_search(search_request: JobSearchRequest) -> List[Dict]:
   """Simulate Indeed job search"""
   await asyncio.sleep(1)
   
   jobs = [
       {
           "title": f"{search_request.keywords} Specialist",
           "company": "Global Solutions Inc",
           "location": search_request.location,
           "url": "https://indeed.com/viewjob?jk=abc123",
           "description": f"Exciting opportunity for {search_request.keywords} professionals.",
           "requirements": f"3+ years {search_request.keywords}, Strong analytical skills",
           "salary": "Competitive salary",
           "posted_date": "3 days ago",
           "job_type": search_request.job_type
       }
   ]
   
   return jobs

async def simulate_naukri_search(search_request: JobSearchRequest) -> List[Dict]:
   """Simulate Naukri job search"""
   await asyncio.sleep(1)
   
   jobs = [
       {
           "title": f"{search_request.keywords} Professional",
           "company": "Indian Tech Hub",
           "location": search_request.location or "Mumbai",
           "url": "https://naukri.com/job-listings/12345",
           "description": f"Looking for skilled {search_request.keywords} professional.",
           "requirements": f"{search_request.keywords}, Good communication, Team player",
           "salary": "₹8,00,000 - ₹15,00,000",
           "posted_date": "1 day ago",
           "job_type": search_request.job_type
       }
   ]
   
   return jobs

async def simulate_glassdoor_search(search_request: JobSearchRequest) -> List[Dict]:
   """Simulate Glassdoor job search"""
   await asyncio.sleep(1)
   
   jobs = [
       {
           "title": f"Senior {search_request.keywords} Role",
           "company": "Top Rated Company",
           "location": search_request.location,
           "url": "https://glassdoor.com/job/12345",
           "description": f"Great opportunity for {search_request.keywords} experts.",
           "requirements": f"Advanced {search_request.keywords}, Leadership skills",
           "salary": "₹20,00,000 - ₹30,00,000",
           "posted_date": "5 days ago",
           "job_type": search_request.job_type,
           "company_rating": 4.5,
           "salary_estimate": "Above average"
       }
   ]
   
   return jobs

def calculate_job_match_score(job: Dict, user_skills: List[str]) -> int:
   """Calculate job match score based on user skills"""
   if not user_skills:
       return 50
   
   job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}".lower()
   matches = sum(1 for skill in user_skills if skill.lower() in job_text)
   score = min(int((matches / len(user_skills)) * 100), 100)
   
   # Add bonus for exact title matches
   title = job.get('title', '').lower()
   for skill in user_skills:
       if skill.lower() in title:
           score += 10
   
   return min(score, 100)

def get_recommendation_from_score(score: int) -> str:
   """Get recommendation based on match score"""
   if score >= 80:
       return "apply"
   elif score >= 60:
       return "maybe"
   else:
       return "skip"