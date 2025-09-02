"""
Database models for AI Job Application Agent
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
from config import Config

config = Config()
Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    
    # Authentication
    password_hash = Column(String(255))  # For email/password auth
    google_id = Column(String(255), unique=True)  # For Google OAuth
    auth_provider = Column(String(20), default="email")  # email or google
    is_active = Column(Boolean, default=True)
    
    # Professional info
    current_title = Column(String(255))
    experience_years = Column(Integer)
    skills = Column(Text)  # JSON array of skills
    preferred_locations = Column(Text)  # JSON array of locations
    salary_expectations = Column(String(100))
    
    # Files
    resume_path = Column(String(500))
    portfolio_url = Column(String(500))
    linkedin_url = Column(String(500))
    profile_picture_url = Column(String(500))
    
    # Preferences
    auto_apply_enabled = Column(Boolean, default=False)
    max_applications_per_day = Column(Integer, default=10)
    preferred_job_types = Column(Text)  # JSON array: remote, onsite, hybrid
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class JobApplication(Base):
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    url = Column(String, unique=True)
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(String)
    
    # Application status
    status = Column(String, default="found")  # found, analyzed, applied, rejected, interview
    applied_at = Column(DateTime)
    response_received = Column(Boolean, default=False)
    
    # AI analysis
    match_score = Column(Integer)  # 0-100 compatibility score
    ai_decision = Column(String)   # apply, skip, maybe
    ai_reasoning = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CoverLetter(Base):
    __tablename__ = "cover_letters"
    
    id = Column(Integer, primary_key=True, index=True)
    job_application_id = Column(Integer)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ApplicationSession(Base):
    __tablename__ = "application_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    
    jobs_found = Column(Integer, default=0)
    jobs_applied = Column(Integer, default=0)
    jobs_skipped = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    
    keywords = Column(String)
    location = Column(String)
    status = Column(String, default="running")  # running, completed, error

# Database setup
def create_database(database_url: str = None):
    if database_url is None:
        database_url = config.DATABASE_URL
    
    print(f"DEBUG: Using database URL: {database_url}")
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine

def get_session(engine=None):
    if engine is None:
        engine = create_engine(config.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
