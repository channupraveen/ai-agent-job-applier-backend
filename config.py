"""
Configuration settings for the AI Agent Job Applier
"""

import os
from pathlib import Path

class Config:
    """Application configuration"""
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost/job_applier_db")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Authentication
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Google OAuth (if using)
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # Browser Automation
    BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
    BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "30"))
    
    # File Uploads
    UPLOAD_DIR = Path("uploads")
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_RESUME_TYPES = [".pdf", ".docx", ".doc", ".txt"]
    
    # Application Settings
    MAX_APPLICATIONS_PER_DAY = int(os.getenv("MAX_APPLICATIONS_PER_DAY", "50"))
    DEFAULT_DELAY_BETWEEN_APPLICATIONS = int(os.getenv("DEFAULT_DELAY", "30"))  # seconds
    
    # Job Sources
    SUPPORTED_JOB_SITES = [
        "linkedin",
        "indeed", 
        "naukri",
        "glassdoor",
        "monster",
        "shine"
    ]
    
    # Email Settings (for notifications)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/application.log")
    
    # Rate Limiting
    REQUESTS_PER_MINUTE = int(os.getenv("REQUESTS_PER_MINUTE", "60"))
    
    # Cache Settings
    CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT", "300"))  # 5 minutes
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        directories = [
            cls.UPLOAD_DIR,
            cls.UPLOAD_DIR / "resumes",
            cls.UPLOAD_DIR / "profile_pictures", 
            cls.UPLOAD_DIR / "cover_letters",
            Path("logs"),
            Path("screenshots"),
            Path("exports")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls):
        """Validate critical configuration"""
        errors = []
        
        if not cls.SECRET_KEY or cls.SECRET_KEY == "your-secret-key-change-in-production":
            errors.append("SECRET_KEY must be set to a secure value")
        
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL must be configured")
            
        return errors

# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    BROWSER_HEADLESS = False
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    BROWSER_HEADLESS = True
    LOG_LEVEL = "INFO"

class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    DATABASE_URL = "postgresql://test:test@localhost/test_job_applier_db"
    BROWSER_HEADLESS = True
    MAX_APPLICATIONS_PER_DAY = 5

# Configuration factory
def get_config():
    """Get configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()
