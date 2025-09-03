"""
FastAPI routes for AI Job Application Agent
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from .app import JobApplierAgent
from .auth import get_current_user
from .models import UserProfile

router = APIRouter()

# Pydantic models for API requests/responses
class JobSearchRequest(BaseModel):
    keywords: str = "python developer"
    location: str = "remote"
    experience_level: str = "mid-level"
    max_applications: int = 5

class JobApplicationResponse(BaseModel):
    id: Optional[int] = None
    title: str
    company: str
    location: str
    url: str
    status: str = "pending"
    applied_at: Optional[str] = None

class ApplicationStatus(BaseModel):
    total_found: int
    applied: int
    skipped: int
    errors: int
    status: str

# Global agent instance - will be initialized later
agent = None

def get_agent():
    """Get or create the global agent instance"""
    global agent
    if agent is None:
        agent = JobApplierAgent()
    return agent

@router.post("/search-jobs")
async def search_jobs(
    request: JobSearchRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Search for job opportunities based on criteria"""
    try:
        agent = get_agent()
        jobs = await agent.search_jobs_async(
            keywords=request.keywords,
            location=request.location,
            experience_level=request.experience_level
        )
        return {
            "message": "Job search completed",
            "jobs_found": len(jobs),
            "jobs": jobs[:10],  # Return first 10 jobs
            "user": current_user.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-application-process")
async def start_application_process(
    background_tasks: BackgroundTasks, 
    request: JobSearchRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Start the automated job application process"""
    try:
        agent = get_agent()
        # Run job application process in background
        background_tasks.add_task(
            agent.run_application_process,
            request.keywords,
            request.location,
            request.max_applications
        )
        
        return {
            "message": "Job application process started",
            "status": "running",
            "max_applications": request.max_applications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/applications")
async def get_applications(current_user: UserProfile = Depends(get_current_user)):
    """Get all job applications history"""
    try:
        agent = get_agent()
        applications = agent.get_applications_history()
        return {
            "applications": applications,
            "total": len(applications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_application_status(current_user: UserProfile = Depends(get_current_user)):
    """Get current application process status"""
    try:
        agent = get_agent()
        status = agent.get_current_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-cover-letter")
async def generate_cover_letter(
    job_title: str,
    company: str,
    job_description: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Generate AI-powered cover letter for specific job"""
    try:
        agent = get_agent()
        cover_letter = await agent.generate_cover_letter_async(
            job_title, company, job_description
        )
        return {
            "cover_letter": cover_letter,
            "job_title": job_title,
            "company": company
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_config(current_user: UserProfile = Depends(get_current_user)):
    """Get current agent configuration"""
    agent = get_agent()
    return {
        "keywords": getattr(agent.config, 'KEYWORDS', 'python developer'),
        "location": getattr(agent.config, 'LOCATION', 'remote'),
        "max_applications_per_day": agent.config.MAX_APPLICATIONS_PER_DAY,
        "auto_apply": getattr(agent.config, 'AUTO_APPLY', False)
    }

@router.post("/config")
async def update_config(
    keywords: Optional[str] = None,
    location: Optional[str] = None,
    max_applications: Optional[int] = None,
    current_user: UserProfile = Depends(get_current_user)
):
    """Update agent configuration"""
    agent = get_agent()
    if keywords:
        agent.config.KEYWORDS = keywords
    if location:
        agent.config.LOCATION = location
    if max_applications:
        agent.config.MAX_APPLICATIONS_PER_DAY = max_applications
    
    return {"message": "Configuration updated successfully"}
