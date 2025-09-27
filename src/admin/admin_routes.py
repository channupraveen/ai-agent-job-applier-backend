"""
Admin-only routes for AI Job Application Agent
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..auth import get_current_admin_user
from ..models import get_session, UserProfile, JobApplication
from datetime import datetime

admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.get("/users")
async def get_all_users(admin_user: UserProfile = Depends(get_current_admin_user)):
    """Get all users - Admin only"""
    db_session = get_session()
    try:
        users = db_session.query(UserProfile).all()
        return [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "current_title": user.current_title,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": user.last_login
            }
            for user in users
        ]
    finally:
        db_session.close()

@admin_router.get("/stats")
async def get_admin_stats(admin_user: UserProfile = Depends(get_current_admin_user)):
    """Get system statistics - Admin only"""
    db_session = get_session()
    try:
        total_users = db_session.query(UserProfile).count()
        active_users = db_session.query(UserProfile).filter(UserProfile.is_active == True).count()
        admin_users = db_session.query(UserProfile).filter(UserProfile.role == "admin").count()
        total_jobs = db_session.query(JobApplication).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "admin_users": admin_users,
            "total_jobs": total_jobs,
            "generated_at": datetime.utcnow()
        }
    finally:
        db_session.close()

@admin_router.post("/users/{user_id}/toggle-role")
async def toggle_user_role(
    user_id: int,
    admin_user: UserProfile = Depends(get_current_admin_user)
):
    """Toggle user role between user and admin - Admin only"""
    if admin_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    db_session = get_session()
    try:
        user = db_session.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Toggle role
        user.role = "admin" if user.role == "user" else "user"
        user.updated_at = datetime.utcnow()
        db_session.commit()
        
        return {
            "message": f"User role changed to {user.role}",
            "user_id": user.id,
            "new_role": user.role
        }
    finally:
        db_session.close()

@admin_router.get("/system-health")
async def get_system_health(admin_user: UserProfile = Depends(get_current_admin_user)):
    """Get system health status - Admin only"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "admin_user": admin_user.email,
        "services": {
            "database": "connected",
            "auth": "active",
            "job_scrapers": "configured"
        }
    }
