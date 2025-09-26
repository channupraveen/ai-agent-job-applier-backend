-- AI Agent Job Applier Database Schema - PostgreSQL Version
-- This file creates all necessary tables and initial data for the job application system
-- ===================================
-- JOB SOURCES TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS job_sources (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    api_key VARCHAR(255),
    base_url VARCHAR(500),
    rate_limit INTEGER DEFAULT 100,
    last_sync TIMESTAMP,
    total_jobs INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'inactive',
    icon VARCHAR(100) DEFAULT 'pi pi-briefcase',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================
-- JOB APPLICATIONS TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS job_applications (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        company VARCHAR(255) NOT NULL,
        location VARCHAR(255),
        url VARCHAR(500) UNIQUE,
        description TEXT,
        requirements TEXT,
        salary_range VARCHAR(100),
        -- Application tracking
        status VARCHAR(50) DEFAULT 'found', -- found, analyzed, applied, rejected, interview, offer
        applied_at TIMESTAMP,
        response_received BOOLEAN DEFAULT FALSE,
        response_date TIMESTAMP,
        -- AI analysis
        match_score INTEGER CHECK (
            match_score >= 0
            AND match_score <= 100
        ),
        ai_decision VARCHAR(20), -- apply, skip, maybe
        ai_reasoning TEXT,
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- Add some default website configurations
INSERT INTO
    website_configurations (
        name,
        base_url,
        job_search_url,
        login_required,
        search_selectors,
        job_selectors
    )
VALUES
    (
        'LinkedIn',
        'https://www.linkedin.com',
        'https://www.linkedin.com/jobs/search',
        TRUE,
        '{"keywords": "input[aria-label=\\"Search by title, skill, or company\\"]", "location": "input[aria-label=\\"City, state, or zip code\\"]"}',
        '{"job_title": ".sr-only", "company": ".hidden-nested-link", "location": ".job-search-card__location", "job_link": ".job-search-card__title-link"}'
    ),
    (
        'Indeed',
        'https://www.indeed.com',
        'https://www.indeed.com/jobs',
        FALSE,
        '{"keywords": "#text-input-what", "location": "#text-input-where"}',
        '{"job_title": ".jobTitle", "company": ".companyName", "location": ".companyLocation", "job_link": ".jobTitle a"}'
    ) ON CONFLICT (name) DO NOTHING;

-- ===================================
-- EXTERNAL JOB RESULTS TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS external_job_results (
        id SERIAL PRIMARY KEY,
        external_job_id VARCHAR(255), -- ID from external source
        source VARCHAR(50) NOT NULL, -- linkedin, indeed, naukri, etc.
        -- Job details
        title VARCHAR(255) NOT NULL,
        company VARCHAR(255) NOT NULL,
        location VARCHAR(255),
        description TEXT,
        requirements TEXT,
        salary VARCHAR(100),
        job_type VARCHAR(50),
        url VARCHAR(500),
        -- Metadata
        posted_date TIMESTAMP,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );

-- ===================================
-- BROWSER SESSIONS TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS browser_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        website VARCHAR(100), -- linkedin, indeed, etc.
        -- Session details
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP,
        status VARCHAR(50) DEFAULT 'active', -- active, completed, error, timeout
        -- Automation results
        jobs_processed INTEGER DEFAULT 0,
        applications_submitted INTEGER DEFAULT 0,
        errors_encountered INTEGER DEFAULT 0,
        -- Session metadata
        browser_type VARCHAR(50) DEFAULT 'chrome',
        headless_mode BOOLEAN DEFAULT TRUE,
        session_notes TEXT
    );

-- ===================================
-- NOTIFICATION SETTINGS TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS notification_settings (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        -- Email notifications
        email_enabled BOOLEAN DEFAULT TRUE,
        email_frequency VARCHAR(20) DEFAULT 'daily', -- immediate, hourly, daily, weekly
        -- Notification types
        notify_new_jobs BOOLEAN DEFAULT TRUE,
        notify_applications_sent BOOLEAN DEFAULT TRUE,
        notify_responses_received BOOLEAN DEFAULT TRUE,
        notify_automation_complete BOOLEAN DEFAULT TRUE,
        notify_errors BOOLEAN DEFAULT TRUE,
        -- SMS notifications (if implemented)
        sms_enabled BOOLEAN DEFAULT FALSE,
        sms_number VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- ===================================
-- ANALYTICS TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS analytics (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        -- Metric details
        metric_name VARCHAR(100) NOT NULL, -- applications_sent, jobs_found, etc.
        metric_value INTEGER NOT NULL,
        metric_data TEXT, -- JSON for additional data
        -- Time and context
        date_recorded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source VARCHAR(50), -- automation, manual, import
        session_id INTEGER -- Link to automation session if applicable
    );

-- ===================================
-- USER PROFILES TABLE (WITH AUTH)
-- ===================================
CREATE TABLE
    IF NOT EXISTS user_profiles (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(255) UNIQUE NOT NULL,
        phone VARCHAR(20),
        -- Authentication fields
        password_hash VARCHAR(255), -- For email/password auth
        google_id VARCHAR(255) UNIQUE, -- For Google OAuth
        auth_provider VARCHAR(20) DEFAULT 'email', -- 'email' or 'google'
        is_active BOOLEAN DEFAULT TRUE,
        -- Professional info
        current_title VARCHAR(255),
        experience_years INTEGER,
        skills TEXT, -- JSON array of skills
        preferred_locations TEXT, -- JSON array of locations
        salary_expectations VARCHAR(100),
        current_ctc VARCHAR(100), -- ✅ NEW: Current salary package
        expected_ctc VARCHAR(100), -- ✅ NEW: Expected salary package
        education TEXT, -- ✅ NEW: JSON array of education entries
        -- Files and URLs
        resume_path VARCHAR(500),
        portfolio_url VARCHAR(500),
        linkedin_url VARCHAR(500),
        profile_picture_url VARCHAR(500),
        -- Preferences
        auto_apply_enabled BOOLEAN DEFAULT FALSE,
        max_applications_per_day INTEGER DEFAULT 10,
        preferred_job_types TEXT, -- JSON array: remote, onsite, hybrid
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );

-- ===================================
-- COVER LETTERS TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS cover_letters (
        id SERIAL PRIMARY KEY,
        job_application_id INTEGER,
        content TEXT NOT NULL,
        ai_generated BOOLEAN DEFAULT TRUE,
        template_used VARCHAR(100),
        customization_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_application_id) REFERENCES job_applications (id) ON DELETE CASCADE
    );

-- ===================================
-- APPLICATION SESSIONS TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS application_sessions (
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
        status VARCHAR(20) DEFAULT 'running', -- running, completed, error, cancelled
        error_message TEXT
    );

-- ===================================
-- JOB SEARCH CRITERIA TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS job_search_criteria (
        id SERIAL PRIMARY KEY,
        user_profile_id INTEGER,
        -- Search parameters
        keywords TEXT NOT NULL,
        excluded_keywords TEXT,
        min_salary INTEGER,
        max_salary INTEGER,
        job_types TEXT, -- JSON: full-time, part-time, contract, internship
        experience_levels TEXT, -- JSON: entry, mid, senior, executive
        -- Location preferences
        locations TEXT, -- JSON array of preferred locations
        remote_allowed BOOLEAN DEFAULT TRUE,
        willing_to_relocate BOOLEAN DEFAULT FALSE,
        -- Company preferences
        company_sizes TEXT, -- JSON: startup, small, medium, large, enterprise
        industries TEXT, -- JSON array of preferred industries
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_profile_id) REFERENCES user_profiles (id) ON DELETE CASCADE
    );

-- ===================================
-- APPLICATION LOGS TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS application_logs (
        id SERIAL PRIMARY KEY,
        session_id INTEGER,
        job_application_id INTEGER,
        -- Log details
        action VARCHAR(100), -- searched, analyzed, applied, skipped, error
        message TEXT,
        details TEXT, -- JSON with additional details
        -- Error tracking
        error_type VARCHAR(100),
        error_details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES application_sessions (id) ON DELETE CASCADE,
        FOREIGN KEY (job_application_id) REFERENCES job_applications (id) ON DELETE SET NULL
    );

-- ===================================
-- COMPANY BLACKLIST TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS company_blacklist (
        id SERIAL PRIMARY KEY,
        company_name VARCHAR(255) NOT NULL,
        reason TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- ===================================
-- WEBSITE CONFIGURATIONS TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS website_configurations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        base_url VARCHAR(500) NOT NULL,
        job_search_url VARCHAR(500) NOT NULL,
        login_required BOOLEAN DEFAULT FALSE,
        login_url VARCHAR(500),
        -- CSS/XPath selectors stored as JSON
        search_selectors TEXT, -- JSON: {"keywords": "#search-input", "location": "#location-input"}
        job_selectors TEXT, -- JSON: {"job_title": ".job-title", "company": ".company-name"}
        form_selectors TEXT, -- JSON: {"apply_button": ".apply-btn", "resume_upload": "input[type='file']"}
        -- Pagination and scraping settings
        pagination_selector VARCHAR(255),
        max_pages INTEGER DEFAULT 5,
        delay_between_requests INTEGER DEFAULT 2, -- seconds
        -- Status and metadata
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- ===================================
-- API USAGE TRACKING TABLE
-- ===================================
CREATE TABLE
    IF NOT EXISTS api_usage (
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
CREATE INDEX IF NOT EXISTS idx_job_applications_status ON job_applications (status);

CREATE INDEX IF NOT EXISTS idx_job_applications_created_at ON job_applications (created_at);

CREATE INDEX IF NOT EXISTS idx_job_applications_company ON job_applications (company);

CREATE INDEX IF NOT EXISTS idx_application_sessions_started_at ON application_sessions (started_at);

CREATE INDEX IF NOT EXISTS idx_application_logs_timestamp ON application_logs (timestamp);

CREATE INDEX IF NOT EXISTS idx_cover_letters_job_id ON cover_letters (job_application_id);

-- Authentication indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles (email);

CREATE INDEX IF NOT EXISTS idx_user_profiles_google_id ON user_profiles (google_id);

CREATE INDEX IF NOT EXISTS idx_user_profiles_auth_provider ON user_profiles (auth_provider);

-- Job Sources indexes
CREATE INDEX IF NOT EXISTS idx_job_sources_enabled ON job_sources(enabled);
CREATE INDEX IF NOT EXISTS idx_job_sources_last_sync ON job_sources(last_sync);

-- ===================================
-- INITIAL DATA
-- ===================================
-- Insert default user profile (with authentication) - let ID auto-increment
INSERT INTO
    user_profiles (
        name,
        email,
        password_hash,
        current_title,
        experience_years,
        skills,
        auto_apply_enabled,
        max_applications_per_day,
        auth_provider
    )
VALUES
    (
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

-- Insert default search criteria - reference the demo user by email
INSERT INTO
    job_search_criteria (
        user_profile_id,
        keywords,
        job_types,
        experience_levels,
        locations,
        remote_allowed
    )
SELECT
    up.id,
    'python developer, software engineer, backend developer, full stack developer',
    '["full-time", "contract"]',
    '["mid-level", "senior"]',
    '["Remote", "Hyderabad", "Bangalore", "Mumbai", "Delhi"]',
    TRUE
FROM
    user_profiles up
WHERE
    up.email = 'demo@example.com'
    AND NOT EXISTS (
        SELECT
            1
        FROM
            job_search_criteria
        WHERE
            user_profile_id = up.id
    );

-- Insert some common companies to avoid (optional)
INSERT INTO
    company_blacklist (company_name, reason)
VALUES
    ('Scam Corp', 'Known for fake job postings'),
    ('No Pay Inc', 'Poor payment history') ON CONFLICT DO NOTHING;

-- Insert default job sources
INSERT INTO job_sources (id, name, enabled, base_url, rate_limit, status, icon) VALUES 
('naukri', 'Naukri.com', true, 'https://www.naukri.com', 500, 'active', 'pi pi-briefcase'),
('indeed', 'Indeed India', true, 'https://in.indeed.com/rss', 1000, 'active', 'pi pi-search'),
('timesjobs', 'TimesJobs', true, 'https://www.timesjobs.com/rss', 400, 'active', 'pi pi-clock'),
('linkedin', 'LinkedIn Jobs', false, 'https://api.linkedin.com/v2/jobSearch', 100, 'inactive', 'pi pi-linkedin'),
('foundit', 'Foundit (Monster India)', true, 'https://www.foundit.in', 300, 'active', 'pi pi-star'),
('shine', 'Shine.com', true, 'https://www.shine.com', 250, 'active', 'pi pi-sun'),
('freshersjobs', 'Freshers Jobs', true, 'https://www.freshersworld.com', 200, 'active', 'pi pi-users'),
('internshala', 'Internshala', true, 'https://internshala.com', 150, 'active', 'pi pi-book'),
('instahyre', 'Instahyre', true, 'https://www.instahyre.com', 200, 'active', 'pi pi-bolt'),
('angellist', 'AngelList (Wellfound)', true, 'https://wellfound.com', 100, 'active', 'pi pi-heart'),
('apnacircle', 'Apna Circle', true, 'https://apnacircle.com', 150, 'active', 'pi pi-users'),
('hirist', 'Hirist (Tech Jobs)', true, 'https://www.hirist.com', 200, 'active', 'pi pi-desktop'),
('jobhai', 'JobHai', true, 'https://www.jobhai.com', 150, 'active', 'pi pi-map'),
('cutshort', 'Cutshort', true, 'https://cutshort.io', 100, 'active', 'pi pi-filter'),
('jobsearch', 'Job Search India', false, 'https://www.jobsearchindia.com', 100, 'inactive', 'pi pi-compass'),
('govtjobs', 'Government Jobs India', false, 'https://www.sarkariresult.com', 50, 'inactive', 'pi pi-building')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    base_url = EXCLUDED.base_url,
    rate_limit = EXCLUDED.rate_limit,
    status = EXCLUDED.status,
    icon = EXCLUDED.icon;