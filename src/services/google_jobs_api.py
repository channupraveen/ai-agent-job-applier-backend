"""
Google Jobs API Service using SerpAPI
Fetches real job data from Google Jobs search results
Now integrated with user's SerpAPI configuration from database
"""

import requests
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import get_job_db


class GoogleJobsAPIService:
    """Service for fetching jobs from Google Jobs API via SerpAPI using user configuration"""
    
    def __init__(self, user_id: int = None):
        self.base_url = "https://serpapi.com/search.json"
        self.rate_limit_delay = 1  # 1 second between requests
        self.user_id = user_id
        self.config = None
        
    def _load_user_config(self) -> Dict[str, Any]:
        """Load SerpAPI configuration from database for the user"""
        if self.config:
            return self.config
            
        try:
            from ..database import get_job_db
            db = get_job_db()
            
            # Get user's SerpAPI configuration
            query = """
            SELECT 
                api_key, engine, location, google_domain, hl, gl,
                max_jobs_per_sync, search_radius, ltype, date_posted,
                job_type, no_cache, output
            FROM serpapi_configurations 
            WHERE user_id = :user_id AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
            """
            
            if self.user_id:
                result = db.execute(text(query), {"user_id": self.user_id}).fetchone()
                
                if result:
                    self.config = {
                        "api_key": result.api_key,
                        "engine": result.engine,
                        "location": result.location,
                        "google_domain": result.google_domain,
                        "hl": result.hl,
                        "gl": result.gl,
                        "max_jobs_per_sync": result.max_jobs_per_sync,
                        "search_radius": result.search_radius,
                        "ltype": result.ltype,
                        "date_posted": result.date_posted,
                        "job_type": result.job_type,
                        "no_cache": result.no_cache,
                        "output": result.output
                    }
                    print(f"✅ Loaded SerpAPI config for user {self.user_id}")
                    return self.config
            
            # Fallback to default configuration
            self.config = {
                "api_key": "a448fc3f98bea2711a110c46c86d75cc09e786b729a8212f666c89d35800429f",
                "engine": "google_jobs",
                "location": "India",
                "google_domain": "google.com",
                "hl": "en",
                "gl": "in",
                "max_jobs_per_sync": 50,
                "search_radius": 50,
                "ltype": 0,
                "date_posted": "any",
                "job_type": "any",
                "no_cache": False,
                "output": "json"
            }
            print("ℹ️ Using default SerpAPI configuration")
            return self.config
            
        except Exception as e:
            print(f"⚠️ Error loading SerpAPI config: {str(e)}")
            # Return default config on error
            self.config = {
                "api_key": "a448fc3f98bea2711a110c46c86d75cc09e786b729a8212f666c89d35800429f",
                "engine": "google_jobs",
                "location": "India",
                "google_domain": "google.com",
                "hl": "en",
                "gl": "in",
                "max_jobs_per_sync": 50,
                "search_radius": 50,
                "ltype": 0,
                "date_posted": "any",
                "job_type": "any",
                "no_cache": False,
                "output": "json"
            }
            return self.config
        
    async def search_jobs(
        self, 
        keywords: str, 
        location: str = None,
        limit: int = None,
        work_from_home: bool = None,
        job_type: str = None,
        date_posted: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs using Google Jobs API with user's SerpAPI configuration
        
        Args:
            keywords: Search keywords (e.g., "software engineer", "python developer")
            location: Location to search in (overrides config default)
            limit: Maximum number of jobs to return (overrides config default)
            work_from_home: Filter for remote jobs (overrides config default)
            job_type: Job type filter (overrides config default)
            date_posted: Date filter (overrides config default)
            
        Returns:
            List of job dictionaries with standardized format
        """
        try:
            # Load user configuration
            config = self._load_user_config()
            
            # Prepare search parameters using config values or overrides
            params = {
                "engine": config["engine"],
                "q": keywords,
                "location": location or config["location"],
                "google_domain": config["google_domain"],
                "hl": config["hl"],
                "gl": config["gl"],
                "api_key": config["api_key"],
                "output": config["output"]
            }
            
            # Add location type filter (work from home)
            ltype_value = config["ltype"]
            if work_from_home is not None:
                ltype_value = 1 if work_from_home else 0
            if ltype_value == 1:
                params["ltype"] = "1"
                
            # Add no_cache parameter
            if config["no_cache"]:
                params["no_cache"] = "true"
                
            # Handle date posted filter
            date_filter = date_posted or config["date_posted"]
            if date_filter and date_filter != "any":
                # Map common date filters to query modifications
                if date_filter == "today":
                    params["q"] += " posted today"
                elif date_filter == "3days":
                    params["q"] += " in the last 3 days"
                elif date_filter == "week":
                    params["q"] += " in the last week"
                elif date_filter == "month":
                    params["q"] += " in the last month"
            
            # Handle job type filter
            job_type_filter = job_type or config["job_type"]
            if job_type_filter and job_type_filter != "any":
                # Map job types
                job_type_mapping = {
                    "full_time": "full time",
                    "part_time": "part time",
                    "contractor": "contract",
                    "intern": "internship"
                }
                mapped_type = job_type_mapping.get(job_type_filter, job_type_filter)
                params["q"] += f" {mapped_type}"
            
            # Set limit
            effective_limit = limit or config["max_jobs_per_sync"]
            
            print(f"🔍 Searching Google Jobs API with user config:")
            print(f"   Keywords: '{keywords}'")
            print(f"   Location: '{params['location']}'")
            print(f"   Work from home: {ltype_value == 1}")
            print(f"   Max results: {effective_limit}")
            print(f"   Date filter: {date_filter}")
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"❌ Google Jobs API error {response.status}: {error_text}")
                        return []
                    
                    data = await response.json()
                    
                    # Check for API errors
                    if "error" in data:
                        print(f"❌ Google Jobs API error: {data['error']}")
                        return []
                    
                    # Extract jobs from results
                    jobs_results = data.get("jobs_results", [])
                    
                    if not jobs_results:
                        print(f"⚠️ No jobs found for '{keywords}' in '{params['location']}'")
                        return []
                    
                    print(f"✅ Found {len(jobs_results)} jobs from Google Jobs API")
                    
                    # Convert to standard format and limit results
                    standardized_jobs = []
                    for job in jobs_results[:effective_limit]:
                        standardized_job = self._standardize_job_format(job)
                        if standardized_job:
                            standardized_jobs.append(standardized_job)
                    
                    print(f"📝 Standardized {len(standardized_jobs)} jobs")
                    return standardized_jobs
                    
        except aiohttp.ClientError as e:
            print(f"❌ Network error calling Google Jobs API: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error in Google Jobs API: {str(e)}")
            return []
    
    def _standardize_job_format(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert Google Jobs API response to standardized job format
        
        Args:
            job_data: Raw job data from Google Jobs API
            
        Returns:
            Standardized job dictionary or None if invalid
        """
        try:
            # Extract basic information
            title = job_data.get("title", "").strip()
            company = job_data.get("company_name", "").strip()
            location = job_data.get("location", "").strip()
            
            # Skip jobs with missing essential information
            if not title or not company:
                return None
            
            # Get job URL (prefer apply_options if available)
            job_url = ""
            apply_options = job_data.get("apply_options", [])
            if apply_options and len(apply_options) > 0:
                # Use the first apply option URL
                job_url = apply_options[0].get("link", "")
            
            # Fallback to share_link if no apply options
            if not job_url:
                job_url = job_data.get("share_link", "")
            
            # Extract description
            description = job_data.get("description", "").strip()
            
            # Extract requirements from job highlights
            requirements = ""
            job_highlights = job_data.get("job_highlights", [])
            for highlight in job_highlights:
                if highlight.get("title") == "Qualifications":
                    requirements = " | ".join(highlight.get("items", []))
                    break
            
            # Extract salary information
            salary = ""
            extensions = job_data.get("extensions", [])
            detected_extensions = job_data.get("detected_extensions", {})
            
            # Look for salary in extensions
            for ext in extensions:
                if "₹" in str(ext) or "$" in str(ext) or "salary" in str(ext).lower():
                    salary = str(ext)
                    break
            
            # Extract employment type
            employment_type = ""
            if "schedule_type" in detected_extensions:
                employment_type = detected_extensions["schedule_type"]
            else:
                # Look in extensions
                for ext in extensions:
                    ext_lower = str(ext).lower()
                    if any(t in ext_lower for t in ["full-time", "part-time", "contract", "internship"]):
                        employment_type = str(ext)
                        break
            
            # Extract posting date
            posted_date = None
            if "posted_at" in detected_extensions:
                posted_date = detected_extensions["posted_at"]
            else:
                # Look in extensions
                for ext in extensions:
                    ext_str = str(ext)
                    if any(t in ext_str.lower() for t in ["ago", "day", "week", "hour"]):
                        posted_date = ext_str
                        break
            
            # Create standardized job object
            standardized_job = {
                "title": title,
                "company": company,
                "location": location,
                "url": job_url,
                "description": description[:1000] if description else "",  # Limit description length
                "requirements": requirements[:500] if requirements else "",  # Limit requirements length
                "salary": salary,
                "employment_type": employment_type,
                "posted_date": posted_date,
                "source": "Google Jobs API",
                "via": job_data.get("via", ""),
                "thumbnail": job_data.get("thumbnail", ""),
                "job_id": job_data.get("job_id", ""),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            return standardized_job
            
        except Exception as e:
            print(f"⚠️ Error standardizing job format: {str(e)}")
            return None
    
    async def get_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific job
        
        Args:
            job_id: Google Jobs job ID
            
        Returns:
            Detailed job information or None
        """
        try:
            # Note: Google Jobs API doesn't have a direct job details endpoint
            # This would require parsing the job_id and making another search
            # For now, return None - job details are already included in search results
            print(f"ℹ️ Job details not available for individual jobs via Google Jobs API")
            return None
            
        except Exception as e:
            print(f"❌ Error getting job details: {str(e)}")
            return None
    
    def test_api_connection(self) -> bool:
        """
        Test if the API key and connection are working using user configuration
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Load user configuration
            config = self._load_user_config()
            
            params = {
                "engine": config["engine"],
                "q": "test job",
                "location": config["location"],
                "google_domain": config["google_domain"],
                "hl": config["hl"],
                "gl": config["gl"],
                "api_key": config["api_key"]
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" not in data:
                    print("Google Jobs API connection test successful")
                    return True
                else:
                    print(f"Google Jobs API error: {data['error']}")
                    return False
            else:
                print(f"Google Jobs API HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Google Jobs API connection test failed: {str(e)}")
            return False


# Test function for development
async def test_google_jobs_api():
    """Test function to verify Google Jobs API integration"""
    api_service = GoogleJobsAPIService()
    
    print("🧪 Testing Google Jobs API Service...")
    
    # Test connection
    if not api_service.test_api_connection():
        print("❌ API connection test failed")
        return
    
    # Test job search
    print("\n🔍 Testing job search...")
    jobs = await api_service.search_jobs(
        keywords="python developer",
        location="Bangalore, India",
        limit=5
    )
    
    if jobs:
        print(f"✅ Successfully fetched {len(jobs)} jobs")
        for i, job in enumerate(jobs[:2], 1):
            print(f"\nJob {i}:")
            print(f"  Title: {job['title']}")
            print(f"  Company: {job['company']}")
            print(f"  Location: {job['location']}")
            print(f"  Salary: {job['salary']}")
            print(f"  URL: {job['url'][:100]}...")
    else:
        print("❌ No jobs found")

# Run test if executed directly
if __name__ == "__main__":
    asyncio.run(test_google_jobs_api())
