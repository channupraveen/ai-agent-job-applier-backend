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
    current_ctc = Column(String(100))  # ✅ Added missing field
    expected_ctc = Column(String(100))  # ✅ Added missing field
    education = Column(Text)  # ✅ Added missing field - JSON array of education entries
    
    # Files
    resume_path = Column(String(500))
    portfolio_url = Column(String(500))
    linkedin_url = Column(String(500))
    profile_picture_url = Column(String(500))
    
    # Preferences
    auto_apply_enabled = Column(Boolean, default=False)
    max_applications_per_day = Column(Integer, default=10)
    preferred_job_types = Column(Text)  # JSON array: remote, onsite, hybrid
    
    # Integration settings - ✅ Added for integrations component
    job_sources_config = Column(Text)  # JSON config for job sources
    sync_preferences = Column(Text)    # JSON config for sync preferences
    
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
    ai_generated = Column(Boolean, default=True)
    template_used = Column(String(100))
    customization_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class CoverLetterTemplate(Base):
    __tablename__ = "cover_letter_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    content_template = Column(Text, nullable=False)
    category = Column(String(50))  # professional, creative, technical, startup
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ResumeVersion(Base):
    __tablename__ = "resume_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    job_id = Column(Integer)  # If customized for specific job
    version_name = Column(String(100), nullable=False)
    customized_skills = Column(Text)  # JSON array
    customized_experience = Column(Text)  # JSON array
    match_score = Column(Integer)
    file_path = Column(String(500))
    is_base_version = Column(Boolean, default=False)
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

class ApplicationNotes(Base):
    __tablename__ = "application_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    job_application_id = Column(Integer, nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobSearchCriteria(Base):
    """Model for user job search preferences"""
    __tablename__ = "job_search_criteria"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, nullable=False)
    
    # Search parameters
    keywords = Column(Text, nullable=False)
    excluded_keywords = Column(Text)
    min_salary = Column(Integer)
    max_salary = Column(Integer)
    job_types = Column(Text)  # JSON: full-time, part-time, contract, internship
    experience_levels = Column(Text)  # JSON: entry, mid, senior, executive
    
    # Location preferences
    locations = Column(Text)  # JSON array of preferred locations
    remote_allowed = Column(Boolean, default=True)
    willing_to_relocate = Column(Boolean, default=False)
    
    # Company preferences
    company_sizes = Column(Text)  # JSON: startup, small, medium, large, enterprise
    industries = Column(Text)  # JSON array of preferred industries
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompanyBlacklist(Base):
    """Model for blacklisted companies"""
    __tablename__ = "company_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    reason = Column(Text)
    added_at = Column(DateTime, default=datetime.utcnow)


class WebsiteConfiguration(Base):
    """Model for website automation configurations"""
    __tablename__ = "website_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    base_url = Column(String(500), nullable=False)
    job_search_url = Column(String(500), nullable=False)
    login_required = Column(Boolean, default=False)
    login_url = Column(String(500))
    
    # CSS/XPath selectors stored as JSON
    search_selectors = Column(Text)  # JSON: {"keywords": "#search-input", "location": "#location-input"}
    job_selectors = Column(Text)     # JSON: {"job_title": ".job-title", "company": ".company-name"}
    form_selectors = Column(Text)    # JSON: {"apply_button": ".apply-btn", "resume_upload": "input[type='file']"}
    
    # Pagination and scraping settings
    pagination_selector = Column(String(255))
    max_pages = Column(Integer, default=5)
    delay_between_requests = Column(Integer, default=2)  # seconds
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ApplicationLog(Base):
    """Model for detailed application logs"""
    __tablename__ = "application_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer)
    job_application_id = Column(Integer)
    
    # Log details
    action = Column(String(100))  # searched, analyzed, applied, skipped, error
    message = Column(Text)
    details = Column(Text)  # JSON with additional details
    
    # Error tracking
    error_type = Column(String(100))
    error_details = Column(Text)
    
    timestamp = Column(DateTime, default=datetime.utcnow)


class ApiUsage(Base):
    """Model for API usage tracking"""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(255))
    method = Column(String(10))
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(Text)
    ip_address = Column(String(45))


class ExternalJobResult(Base):
    """Model for storing external job search results"""
    __tablename__ = "external_job_results"
    
    id = Column(Integer, primary_key=True, index=True)
    external_job_id = Column(String(255))  # ID from external source
    source = Column(String(50), nullable=False)  # linkedin, indeed, naukri, etc.
    
    # Job details
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    description = Column(Text)
    requirements = Column(Text)
    salary = Column(String(100))
    job_type = Column(String(50))
    url = Column(String(500))
    
    # Metadata
    posted_date = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class BrowserSession(Base):
    """Model for browser automation sessions"""
    __tablename__ = "browser_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    website = Column(String(100))  # linkedin, indeed, etc.
    
    # Session details
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    status = Column(String(50), default="active")  # active, completed, error, timeout
    
    # Automation results
    jobs_processed = Column(Integer, default=0)
    applications_submitted = Column(Integer, default=0)
    errors_encountered = Column(Integer, default=0)
    
    # Session metadata
    browser_type = Column(String(50), default="chrome")
    headless_mode = Column(Boolean, default=True)
    session_notes = Column(Text)


class NotificationSettings(Base):
    """Model for user notification preferences"""
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    
    # Email notifications
    email_enabled = Column(Boolean, default=True)
    email_frequency = Column(String(20), default="daily")  # immediate, hourly, daily, weekly
    
    # Notification types
    notify_new_jobs = Column(Boolean, default=True)
    notify_applications_sent = Column(Boolean, default=True)
    notify_responses_received = Column(Boolean, default=True)
    notify_automation_complete = Column(Boolean, default=True)
    notify_errors = Column(Boolean, default=True)
    
    # SMS notifications (if implemented)
    sms_enabled = Column(Boolean, default=False)
    sms_number = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Analytics(Base):
    """Model for storing analytics data"""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    
    # Metric details
    metric_name = Column(String(100), nullable=False)  # applications_sent, jobs_found, etc.
    metric_value = Column(Integer, nullable=False)
    metric_data = Column(Text)  # JSON for additional data
    
    # Time and context
    date_recorded = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50))  # automation, manual, import
    session_id = Column(Integer)  # Link to automation session if applicable

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

def get_job_db():
    """Get database session for job operations"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
