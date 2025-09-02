"""
Configuration file for AI Job Application Agent
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Authentication Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
    ALGORITHM = os.getenv('ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')
    
    # Job Search Configuration
    KEYWORDS = os.getenv('JOB_KEYWORDS', 'python developer,software engineer,data scientist')
    LOCATION = os.getenv('JOB_LOCATION', 'remote')
    EXPERIENCE_LEVEL = os.getenv('EXPERIENCE_LEVEL', 'mid-level')
    
    # AI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # Database configuration - PostgreSQL for production
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/job_applier_db')
    
    # Automation settings
    AUTO_APPLY = os.getenv('AUTO_APPLY', 'False').lower() == 'true'
    MAX_APPLICATIONS_PER_DAY = int(os.getenv('MAX_APPLICATIONS_PER_DAY', '10'))
    
    # Browser settings for Selenium
    HEADLESS_BROWSER = os.getenv('HEADLESS_BROWSER', 'True').lower() == 'true'
    BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', '30'))
    
    # File paths
    RESUME_PATH = os.getenv('RESUME_PATH', 'resume.pdf')
    COVER_LETTER_TEMPLATE = os.getenv('COVER_LETTER_TEMPLATE', 'cover_letter_template.txt')

# Development configuration
class DevelopmentConfig(Config):
    AUTO_APPLY = False
    HEADLESS_BROWSER = False
    MAX_APPLICATIONS_PER_DAY = 3

# Production configuration  
class ProductionConfig(Config):
    AUTO_APPLY = True
    HEADLESS_BROWSER = True
