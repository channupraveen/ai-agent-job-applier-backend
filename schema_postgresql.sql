-- AI Agent Job Applier Database Schema - PostgreSQL Version
-- This file creates all necessary tables and initial data for the job application system

-- ===================================
-- JOB APPLICATIONS TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS job_applications (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    url VARCHAR(500) UNIQUE,
    description TEXT,
    requirements TEXT,
    salary_range VARCHAR(100),
    
    -- Application tracking
    status VARCHAR(50) DEFAULT 'found',  -- found, analyzed, applied, rejected, interview, offer
    applied_at TIMESTAMP,
    response_received BOOLEAN DEFAULT FALSE,
    response_date TIMESTAMP,
    
    -- AI analysis
    match_score INTEGER CHECK (match_score >= 0 AND match_score <= 100),
    ai_decision VARCHAR(20),  -- apply, skip, maybe
    ai_reasoning TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================
-- USER PROFILES TABLE (WITH AUTH)
-- ===================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    
    -- Authentication fields
    password_hash VARCHAR(255),  -- For email/password auth
    google_id VARCHAR(255) UNIQUE,  -- For Google OAuth
    auth_provider VARCHAR(20) DEFAULT 'email',  -- 'email' or 'google'
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Professional info
    current_title VARCHAR(255),
    experience_years INTEGER,
    skills TEXT,  -- JSON array of skills
    preferred_locations TEXT,  -- JSON array of locations
    salary_expectations VARCHAR(100),
    
    -- Files and URLs
    resume_path VARCHAR(500),
    portfolio_url VARCHAR(500),
    linkedin_url VARCHAR(500),
    profile_picture_url VARCHAR(500),
    
    -- Preferences
    auto_apply_enabled BOOLEAN DEFAULT FALSE,
    max_applications_per_day INTEGER DEFAULT 10,
    preferred_job_types TEXT,  -- JSON array: remote, onsite, hybrid
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- ===================================
-- COVER LETTERS TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS cover_letters (
    id SERIAL PRIMARY KEY,
    job_application_id INTEGER,
    content TEXT NOT NULL,
    ai_generated BOOLEAN DEFAULT TRUE,
    template_used VARCHAR(100),
    customization_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_application_id) REFERENCES job_applications(id) ON DELETE CASCADE
);

-- ===================================
-- APPLICATION SESSIONS TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS application_sessions (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    
    -- Search parameters
    keywords VARCHAR(500),
    location VARCHAR(255),
    experience_level VARCHAR(50),
    
    -- Results
    jobs_found INTEGER DEFAULT 0,
    jobs_applied INTEGER DEFAULT 0,
    jobs_skipped INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'running',  -- running, completed, error, cancelled
    error_message TEXT
);

-- ===================================
-- JOB SEARCH CRITERIA TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS job_search_criteria (
    id SERIAL PRIMARY KEY,
    user_profile_id INTEGER,
    
    -- Search parameters
    keywords TEXT NOT NULL,
    excluded_keywords TEXT,
    min_salary INTEGER,
    max_salary INTEGER,
    job_types TEXT,  -- JSON: full-time, part-time, contract, internship
    experience_levels TEXT,  -- JSON: entry, mid, senior, executive
    
    -- Location preferences
    locations TEXT,  -- JSON array of preferred locations
    remote_allowed BOOLEAN DEFAULT TRUE,
    willing_to_relocate BOOLEAN DEFAULT FALSE,
    
    -- Company preferences
    company_sizes TEXT,  -- JSON: startup, small, medium, large, enterprise
    industries TEXT,  -- JSON array of preferred industries
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE
);

-- ===================================
-- APPLICATION LOGS TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS application_logs (
    id SERIAL PRIMARY KEY,
    session_id INTEGER,
    job_application_id INTEGER,
    
    -- Log details
    action VARCHAR(100),  -- searched, analyzed, applied, skipped, error
    message TEXT,
    details TEXT,  -- JSON with additional details
    
    -- Error tracking
    error_type VARCHAR(100),
    error_details TEXT,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES application_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (job_application_id) REFERENCES job_applications(id) ON DELETE SET NULL
);

-- ===================================
-- COMPANY BLACKLIST TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS company_blacklist (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    reason TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================
-- API USAGE TRACKING TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address VARCHAR(45)
);

-- ===================================
-- INDEXES FOR PERFORMANCE
-- ===================================
CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications(status);
CREATE INDEX IF NOT EXISTS idx_job_applications_created_at ON job_applications(created_at);
CREATE INDEX IF NOT EXISTS idx_job_applications_company ON job_applications(company);
CREATE INDEX IF NOT EXISTS idx_application_sessions_started_at ON application_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_application_logs_timestamp ON application_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_cover_letters_job_id ON cover_letters(job_application_id);
-- Authentication indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_google_id ON user_profiles(google_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_auth_provider ON user_profiles(auth_provider);

-- ===================================
-- INITIAL DATA
-- ===================================

-- Insert default user profile (with authentication)
INSERT INTO user_profiles (
    id, name, email, password_hash, current_title, experience_years, 
    skills, auto_apply_enabled, max_applications_per_day, auth_provider
) VALUES (
    1, 
    'Demo User', 
    'demo@example.com', 
    '$2b$12$dummy.hash.for.demo.user.only',
    'Software Developer', 
    3,
    '["Python", "JavaScript", "React", "FastAPI", "Machine Learning", "SQL"]',
    FALSE,
    10,
    'email'
) ON CONFLICT (email) DO NOTHING;

-- Insert default search criteria
INSERT INTO job_search_criteria (
    id, user_profile_id, keywords, job_types, experience_levels, 
    locations, remote_allowed
) VALUES (
    1,
    1,
    'python developer, software engineer, backend developer, full stack developer',
    '["full-time", "contract"]',
    '["mid-level", "senior"]',
    '["Remote", "Hyderabad", "Bangalore", "Mumbai", "Delhi"]',
    TRUE
) ON CONFLICT DO NOTHING;

-- Insert some common companies to avoid (optional)
INSERT INTO company_blacklist (company_name, reason) VALUES 
('Scam Corp', 'Known for fake job postings'),
('No Pay Inc', 'Poor payment history')
ON CONFLICT DO NOTHING;
