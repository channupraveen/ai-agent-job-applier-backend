"""
External Job Site Integration API Routes - REAL DATA ONLY
ALL dummy/simulation methods removed. Uses only real Indian job scrapers.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio

from .auth import get_current_user
from .models import get_job_db, UserProfile as User
from .utils.source_extractor import extract_source_from_url

router = APIRouter(tags=["External Job Site Integration"])


class JobSearchRequest(BaseModel):
    keywords: str
    location: Optional[str] = "Delhi"
    experience_level: Optional[str] = "mid-level"
    job_type: Optional[str] = "full-time"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    date_posted: Optional[str] = "week"
    limit: int = 50


class BulkJobSearchRequest(BaseModel):
    sources: List[str] = ["indeed", "naukri", "timesjobs"]
    search_params: JobSearchRequest
    save_to_database: bool = True


@router.get("/jobs/external/sources")
async def get_available_job_sources(current_user: User = Depends(get_current_user)):
    """List available REAL job sources (NO dummy data)"""
    try:
        job_sources = [
            {
                "id": "indeed",
                "name": "Indeed India RSS",
                "description": "REAL jobs from Indeed India RSS feeds",
                "supported_features": [
                    "keyword_search",
                    "location_filter",
                    "rss_feeds",
                ],
                "rate_limit": "No API key needed",
                "requires_auth": False,
                "status": "active",
                "data_type": "REAL",
            },
            {
                "id": "naukri",
                "name": "Naukri.com Scraper",
                "description": "REAL jobs scraped from Naukri.com",
                "supported_features": [
                    "keyword_search",
                    "location_filter",
                    "web_scraping",
                ],
                "rate_limit": "Rate limited scraping",
                "requires_auth": False,
                "status": "active",
                "data_type": "REAL",
            },
            {
                "id": "timesjobs",
                "name": "TimesJobs RSS",
                "description": "REAL jobs from TimesJobs RSS feeds",
                "supported_features": ["keyword_search", "rss_feeds"],
                "rate_limit": "No API key needed",
                "requires_auth": False,
                "status": "active",
                "data_type": "REAL",
            },
            {
                "id": "aggregator",
                "name": "Indian Job Aggregator",
                "description": "Combined REAL data from all Indian sources",
                "supported_features": ["multi_source", "deduplication", "ranking"],
                "rate_limit": "Combined rate limits",
                "requires_auth": False,
                "status": "active",
                "data_type": "REAL",
            },
        ]

        return {
            "success": True,
            "job_sources": job_sources,
            "total_sources": len(job_sources),
            "active_sources": len(job_sources),
            "note": "ALL sources provide REAL job data - NO dummy/simulation data",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting job sources: {str(e)}"
        )


@router.post("/jobs/external/indeed")
async def search_indeed_jobs(
    search_request: JobSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Search REAL Indeed India jobs via RSS"""
    try:
        # Use REAL Indeed India RSS scraper
        from .scrapers.indeed_india_rss import IndeedIndiaRSSFetcher

        async with IndeedIndiaRSSFetcher() as fetcher:
            jobs_found = await fetcher.search_jobs(
                keywords=search_request.keywords,
                location=search_request.location or "Delhi",
                limit=search_request.limit,
            )

        if not jobs_found:
            return {
                "success": False,
                "message": "No REAL jobs found from Indeed RSS",
                "jobs_found": 0,
                "jobs_saved": 0,
                "source": "Indeed RSS",
            }

        # Process and save REAL jobs
        user_skills = json.loads(current_user.skills or "[]")
        saved_jobs = []

        for job in jobs_found:
            try:
                match_score = calculate_job_match_score(job, user_skills)

                # Check if job already exists
                existing_query = "SELECT id FROM job_applications WHERE url = :url"
                existing = db.execute(
                    text(existing_query), {"url": job.get("url", "")}
                ).fetchone()

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
                    ) RETURNING id
                    """

                    params = {
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "url": job.get("url", ""),
                        "description": job.get("description", ""),
                        "requirements": job.get("requirements", ""),
                        "salary_range": job.get("salary", ""),
                        "match_score": match_score,
                        "ai_decision": get_recommendation_from_score(match_score),
                        "ai_reasoning": f"REAL Indeed RSS job: {match_score}% compatibility",
                        "source": job_source,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }

                    result = db.execute(text(insert_query), params)
                    if result.fetchone():
                        saved_jobs.append(job["title"])
            except Exception:
                continue

        db.commit()

        return {
            "success": True,
            "message": f"REAL Indeed search completed. Found {len(jobs_found)} REAL jobs",
            "jobs_found": len(jobs_found),
            "jobs_saved": len(saved_jobs),
            "high_match_jobs": len(
                [
                    j
                    for j in jobs_found
                    if calculate_job_match_score(j, user_skills) >= 80
                ]
            ),
            "source": "Indeed RSS (REAL DATA ONLY)",
            "sample_jobs": jobs_found[:3],
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error searching REAL Indeed jobs: {str(e)}"
        )


@router.post("/jobs/external/naukri")
async def search_naukri_jobs(
    search_request: JobSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Search REAL Naukri.com jobs via web scraping"""
    try:
        # Use REAL Naukri scraper
        from .scrapers.naukri_scraper import NaukriJobScraper

        async with NaukriJobScraper() as scraper:
            jobs_found = await scraper.search_jobs(
                keywords=search_request.keywords,
                location=search_request.location or "Delhi",
                limit=search_request.limit,
            )

        if not jobs_found:
            return {
                "success": False,
                "message": "No REAL jobs found from Naukri scraping",
                "jobs_found": 0,
                "jobs_saved": 0,
                "source": "Naukri Scraper",
            }

        # Process and save REAL jobs
        user_skills = json.loads(current_user.skills or "[]")
        saved_jobs = []

        for job in jobs_found:
            try:
                match_score = calculate_job_match_score(job, user_skills)

                existing_query = "SELECT id FROM job_applications WHERE url = :url"
                existing = db.execute(
                    text(existing_query), {"url": job.get("url", "")}
                ).fetchone()

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
                    ) RETURNING id
                    """

                    params = {
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "url": job.get("url", ""),
                        "description": job.get("description", ""),
                        "requirements": job.get("requirements", ""),
                        "salary_range": job.get("salary", ""),
                        "match_score": match_score,
                        "ai_decision": get_recommendation_from_score(match_score),
                        "ai_reasoning": f"REAL Naukri job: {match_score}% compatibility",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }

                    result = db.execute(text(insert_query), params)
                    if result.fetchone():
                        saved_jobs.append(job["title"])
            except Exception:
                continue

        db.commit()

        return {
            "success": True,
            "message": f"REAL Naukri search completed. Found {len(jobs_found)} REAL jobs",
            "jobs_found": len(jobs_found),
            "jobs_saved": len(saved_jobs),
            "high_match_jobs": len(
                [
                    j
                    for j in jobs_found
                    if calculate_job_match_score(j, user_skills) >= 80
                ]
            ),
            "source": "Naukri Scraper (REAL DATA ONLY)",
            "sample_jobs": jobs_found[:3],
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error searching REAL Naukri jobs: {str(e)}"
        )


@router.post("/jobs/external/timesjobs")
async def search_timesjobs_jobs(
    search_request: JobSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Search REAL TimesJobs via RSS feeds"""
    try:
        # Use REAL TimesJobs RSS scraper
        from .scrapers.timesjobs_rss import TimesJobsRSSFetcher

        async with TimesJobsRSSFetcher() as fetcher:
            jobs_found = await fetcher.search_jobs(
                keywords=search_request.keywords,
                location=search_request.location or "Delhi",
                limit=search_request.limit,
            )

        if not jobs_found:
            return {
                "success": False,
                "message": "No REAL jobs found from TimesJobs RSS",
                "jobs_found": 0,
                "jobs_saved": 0,
                "source": "TimesJobs RSS",
            }

        # Process and save REAL jobs
        user_skills = json.loads(current_user.skills or "[]")
        saved_jobs = []

        for job in jobs_found:
            try:
                match_score = calculate_job_match_score(job, user_skills)

                existing_query = "SELECT id FROM job_applications WHERE url = :url"
                existing = db.execute(
                    text(existing_query), {"url": job.get("url", "")}
                ).fetchone()

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
                    ) RETURNING id
                    """

                    params = {
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "url": job.get("url", ""),
                        "description": job.get("description", ""),
                        "requirements": job.get("requirements", ""),
                        "salary_range": job.get("salary", ""),
                        "match_score": match_score,
                        "ai_decision": get_recommendation_from_score(match_score),
                        "ai_reasoning": f"REAL TimesJobs RSS job: {match_score}% compatibility",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }

                    result = db.execute(text(insert_query), params)
                    if result.fetchone():
                        saved_jobs.append(job["title"])
            except Exception:
                continue

        db.commit()

        return {
            "success": True,
            "message": f"REAL TimesJobs search completed. Found {len(jobs_found)} REAL jobs",
            "jobs_found": len(jobs_found),
            "jobs_saved": len(saved_jobs),
            "high_match_jobs": len(
                [
                    j
                    for j in jobs_found
                    if calculate_job_match_score(j, user_skills) >= 80
                ]
            ),
            "source": "TimesJobs RSS (REAL DATA ONLY)",
            "sample_jobs": jobs_found[:3],
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error searching REAL TimesJobs jobs: {str(e)}"
        )


@router.post("/jobs/external/aggregator")
async def search_all_indian_jobs(
    search_request: JobSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Search ALL REAL Indian job sources simultaneously"""
    try:
        # Use REAL Indian Job Aggregator
        from .scrapers.indian_job_aggregator import IndianJobAggregator

        aggregator = IndianJobAggregator()
        jobs_found = await aggregator.search_all_sources(
            keywords=search_request.keywords,
            location=search_request.location or "Delhi",
            limit=search_request.limit,
        )

        if not jobs_found:
            return {
                "success": False,
                "message": "No REAL jobs found from any Indian source",
                "jobs_found": 0,
                "jobs_saved": 0,
                "source": "Indian Aggregator",
            }

        # Process and save REAL jobs
        user_skills = json.loads(current_user.skills or "[]")
        saved_jobs = []
        source_stats = {}

        for job in jobs_found:
            try:
                match_score = calculate_job_match_score(job, user_skills)
                source = job.get("aggregator_source", "unknown")

                # Track source statistics
                if source not in source_stats:
                    source_stats[source] = 0
                source_stats[source] += 1

                existing_query = "SELECT id FROM job_applications WHERE url = :url"
                existing = db.execute(
                    text(existing_query), {"url": job.get("url", "")}
                ).fetchone()

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
                    ) RETURNING id
                    """

                    params = {
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "url": job.get("url", ""),
                        "description": job.get("description", ""),
                        "requirements": job.get("requirements", ""),
                        "salary_range": job.get("salary", ""),
                        "match_score": match_score,
                        "ai_decision": get_recommendation_from_score(match_score),
                        "ai_reasoning": f"REAL {source} job: {match_score}% compatibility",
                        "source": job_source,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }

                    result = db.execute(text(insert_query), params)
                    if result.fetchone():
                        saved_jobs.append(job["title"])
            except Exception:
                continue

        db.commit()

        return {
            "success": True,
            "message": f"REAL Indian job aggregator completed. Found {len(jobs_found)} REAL jobs",
            "jobs_found": len(jobs_found),
            "jobs_saved": len(saved_jobs),
            "high_match_jobs": len(
                [
                    j
                    for j in jobs_found
                    if calculate_job_match_score(j, user_skills) >= 80
                ]
            ),
            "source_breakdown": source_stats,
            "source": "Indian Job Aggregator (ALL REAL SOURCES)",
            "top_jobs": jobs_found[:5],
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error searching ALL REAL Indian jobs: {str(e)}"
        )


@router.delete("/jobs/external/clear-dummy-data")
async def clear_all_dummy_data(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_job_db)
):
    """Clear all dummy/fake job data from database"""
    try:
        # Delete all jobs that don't have REAL in ai_reasoning
        delete_query = """
        DELETE FROM job_applications 
        WHERE (ai_reasoning NOT LIKE '%REAL%' OR ai_reasoning IS NULL)
        AND (
            url LIKE '%jobs.google.com%'
            OR url LIKE '%glassdoor.com/job/12345%'
            OR url LIKE '%linkedin.com/jobs/12345%'
            OR company IN ('Tech Corp', 'Search Team', 'DeepMind', 'Android', 'YouTube', 'AI Research')
            OR company IN ('Microsoft India', 'Google India', 'Amazon India', 'IBM India', 'Oracle India', 'Adobe India')
            OR url LIKE '%40000000%'
            OR url LIKE '%30000000%'
            OR url LIKE '%50000000%'
            OR url LIKE '%190000000%'
            OR url LIKE '%180000000%'
        )
        """

        result = db.execute(text(delete_query))
        deleted_count = result.rowcount
        db.commit()

        # Count remaining jobs
        count_query = "SELECT COUNT(*) as remaining FROM job_applications"
        remaining_result = db.execute(text(count_query))
        remaining_count = dict(remaining_result.fetchone()._mapping)["remaining"]

        return {
            "success": True,
            "message": f"Cleared {deleted_count} dummy job records",
            "deleted_count": deleted_count,
            "remaining_jobs": remaining_count,
            "note": "Only REAL job data remains in database",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error clearing dummy data: {str(e)}"
        )


# Helper functions - REAL DATA PROCESSING ONLY
def calculate_job_match_score(job: Dict, user_skills: List[str]) -> int:
    """Calculate job match score based on user skills"""
    if not user_skills:
        return 50

    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}".lower()
    matches = sum(1 for skill in user_skills if skill.lower() in job_text)
    score = min(int((matches / len(user_skills)) * 100), 100)

    # Add bonus for exact title matches
    title = job.get("title", "").lower()
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
