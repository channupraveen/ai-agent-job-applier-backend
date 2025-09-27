"""
Authentication API routes for AI Job Application Agent
"""

from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import HTTPBearer
from pydantic import BaseModel, field_validator
import re
from typing import Optional
from datetime import datetime, timedelta
# Temporarily commented out OAuth imports
# import httpx
# from authlib.integrations.starlette_client import OAuth
from .auth import (
    verify_password, get_password_hash, create_access_token, 
    get_current_user, generate_random_password
)
from .models import get_session, UserProfile
from config import Config

config = Config()
auth_router = APIRouter()

# Pydantic models for authentication
class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    current_title: Optional[str] = None
    experience_years: Optional[int] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

class UserLogin(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    current_title: Optional[str]
    auth_provider: str
    role: str
    created_at: datetime

@auth_router.post("/register", response_model=Token)
async def register_user(user_data: UserRegister):
    """Register a new user with email and password"""
    
    db_session = get_session()
    
    try:
        # Check if user already exists
        existing_user = db_session.query(UserProfile).filter(
            UserProfile.email == user_data.email
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = UserProfile(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            current_title=user_data.current_title,
            experience_years=user_data.experience_years,
            auth_provider="email",
            created_at=datetime.utcnow()
        )
        
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)
        
        # Create access token with role
        access_token = create_access_token(data={
            "sub": str(new_user.id),
            "role": new_user.role
        })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "current_title": new_user.current_title,
                "auth_provider": new_user.auth_provider,
                "role": new_user.role
            }
        }
        
    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )
    finally:
        db_session.close()

@auth_router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Login with email and password"""
    
    db_session = get_session()
    
    try:
        # Find user by email
        user = db_session.query(UserProfile).filter(
            UserProfile.email == user_credentials.email
        ).first()
        
        if not user or not verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is disabled"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db_session.commit()
        
        # Create access token with role
        access_token = create_access_token(data={
            "sub": str(user.id),
            "role": user.role
        })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "current_title": user.current_title,
                "auth_provider": user.auth_provider,
                "role": user.role
            }
        }
        
    finally:
        db_session.close()

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserProfile = Depends(get_current_user)):
    """Get current authenticated user profile"""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        current_title=current_user.current_title,
        auth_provider=current_user.auth_provider,
        role=current_user.role,
        created_at=current_user.created_at
    )

@auth_router.post("/logout")
async def logout():
    """Logout user (client should delete token)"""
    return {"message": "Successfully logged out"}

@auth_router.get("/google")
async def google_login():
    """Google OAuth temporarily disabled"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth temporarily disabled. Use email/password registration."
    )
