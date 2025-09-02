#!/usr/bin/env python3
"""
FastAPI server entry point for AI Job Application Agent
"""

from fastapi import FastAPI
import uvicorn
from src.api import router
from src.auth_routes import auth_router
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

# Include API routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(router, prefix="/api/v1", tags=["Job Application"])

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
        "endpoints": {
            "search_jobs": "/api/v1/search-jobs",
            "start_automation": "/api/v1/start-application-process",
            "applications": "/api/v1/applications",
            "status": "/api/v1/status"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )
