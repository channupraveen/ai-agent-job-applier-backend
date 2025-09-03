-- Missing Tables Creation Script for AI Job Applier
-- Run this in your PostgreSQL database: job_applier_db

-- Create website_configurations table
CREATE TABLE IF NOT EXISTS website_configurations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    job_search_url VARCHAR(500) NOT NULL,
    login_required BOOLEAN DEFAULT FALSE,
    login_url VARCHAR(500),
    search_selectors TEXT,
    job_selectors TEXT,
    form_selectors TEXT,
    pagination_selector VARCHAR(255),
    max_pages INTEGER DEFAULT 5,
    delay_between_requests INTEGER DEFAULT 2,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create external_job_results table
CREATE TABLE IF NOT EXISTS external_job_results (
    id SERIAL PRIMARY KEY,
    external_job_id VARCHAR(255),
    source VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    description TEXT,
    requirements TEXT,
    salary VARCHAR(100),
    job_type VARCHAR(50),
    url VARCHAR(500),
    posted_date TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create browser_sessions table
CREATE TABLE IF NOT EXISTS browser_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    website VARCHAR(100),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    jobs_processed INTEGER DEFAULT 0,
    applications_submitted INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    browser_type VARCHAR(50) DEFAULT 'chrome',
    headless_mode BOOLEAN DEFAULT TRUE,
    session_notes TEXT
);

-- Create notification_settings table
CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    email_enabled BOOLEAN DEFAULT TRUE,
    email_frequency VARCHAR(20) DEFAULT 'daily',
    notify_new_jobs BOOLEAN DEFAULT TRUE,
    notify_applications_sent BOOLEAN DEFAULT TRUE,
    notify_responses_received BOOLEAN DEFAULT TRUE,
    notify_automation_complete BOOLEAN DEFAULT TRUE,
    notify_errors BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    sms_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create analytics table
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    metric_name VARCHAR(100) NOT NULL,
    metric_value INTEGER NOT NULL,
    metric_data TEXT,
    date_recorded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50),
    session_id INTEGER
);

-- Insert default website configurations
INSERT INTO website_configurations (
    name, base_url, job_search_url, login_required, search_selectors, job_selectors
) VALUES 
(
    'LinkedIn',
    'https://www.linkedin.com',
    'https://www.linkedin.com/jobs/search',
    TRUE,
    '{"keywords": "input[aria-label=\"Search by title, skill, or company\"]", "location": "input[aria-label=\"City, state, or zip code\"]"}',
    '{"job_title": ".sr-only", "company": ".hidden-nested-link", "location": ".job-search-card__location", "job_link": ".job-search-card__title-link"}'
),
(
    'Indeed',
    'https://www.indeed.com',
    'https://www.indeed.com/jobs',
    FALSE,
    '{"keywords": "#text-input-what", "location": "#text-input-where"}',
    '{"job_title": ".jobTitle", "company": ".companyName", "location": ".companyLocation", "job_link": ".jobTitle a"}'
)
ON CONFLICT (name) DO NOTHING;

-- Show created tables
SELECT 'Tables created successfully!' as status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
