#!/usr/bin/env python3
"""
FastAPI server entry point for AI Job Application Agent
"""

from fastapi import FastAPI
import uvicorn
from src.api import router
from src.auth_routes import auth_router
from src.job_routes import router as job_router
from src.resume_routes import router as resume_router
from src.cover_letter_routes import cover_letter_router
# New route files
from src.profile_routes import router as profile_router
from src.preferences_routes import router as preferences_router
from src.automation_routes import router as automation_router
from src.website_routes import router as website_router
from src.external_jobs_routes import router as external_jobs_router
from src.browser_automation_routes import router as browser_automation_router
from src.analytics_routes import router as analytics_router
from src.notification_routes import router as notification_router

from src.database import init_database, check_database

# Create FastAPI app
app = FastAPI(
    title="AI Job Application Agent API",
    description="Automate job applications with AI-powered resume customization, intelligent job matching, and cross-platform access. Apply to jobs from any device!",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting AI Job Application Agent API...")
    print("🗄️  Checking database...")
    
    if not check_database():
        print("📦 Setting up database schema...")
        if init_database():
            print("✅ Database initialized successfully!")
        else:
            print("❌ Database initialization failed!")
    else:
        print("✅ Database already configured!")

# Include API routes - Core functionality
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(router, prefix="/api/v1", tags=["Job Application"])
app.include_router(job_router, prefix="/api/v1", tags=["Job Search & Discovery"])
app.include_router(resume_router, prefix="/api/v1", tags=["Resume Management"])
app.include_router(cover_letter_router, prefix="/api/v1", tags=["Cover Letters"])

# Include new API routes - Enhanced functionality  
app.include_router(profile_router, prefix="/api/v1", tags=["User Profile Management"])
app.include_router(preferences_router, prefix="/api/v1", tags=["User Preferences & Job Criteria"])
app.include_router(automation_router, prefix="/api/v1", tags=["Automation Control"])
app.include_router(website_router, prefix="/api/v1", tags=["Website Configuration"])
app.include_router(external_jobs_router, prefix="/api/v1", tags=["External Job Integrations"])
app.include_router(browser_automation_router, prefix="/api/v1", tags=["Browser Automation"])
app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics & Reporting"])
app.include_router(notification_router, prefix="/api/v1", tags=["Notifications"])

@app.get("/")
async def root():
    return {
        "message": "🤖 AI Job Application Agent API",
        "status": "running",
        "docs": "/docs",
        "authentication": {
            "register": "/auth/register",
            "login": "/auth/login",
            "google_login": "/auth/google"
        },
        "core_endpoints": {
            "search_jobs": "/api/v1/search-jobs",
            "start_automation": "/api/v1/start-application-process",
            "applications": "/api/v1/applications",
            "status": "/api/v1/status"
        },
        "enhanced_endpoints": {
            "profile_management": "/api/v1/profile",
            "preferences": "/api/v1/preferences",
            "automation_control": "/api/v1/agent",
            "website_config": "/api/v1/websites",
            "external_jobs": "/api/v1/external-jobs",
            "browser_automation": "/api/v1/browser",
            "analytics": "/api/v1/analytics",
            "notifications": "/api/v1/notifications"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )
