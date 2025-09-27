"""
Google Jobs API Service with Custom Configuration Support
Enhanced version that accepts configuration parameters directly
"""

import requests
import asyncio
import aiohttp
import json
from typing import List, Dict, Optional, Any
from datetime import datetime


class GoogleJobsAPIServiceWithConfig:
    """Service for fetching jobs from Google Jobs API via SerpAPI with custom configuration"""
    
    def __init__(self, custom_config: Dict[str, Any]):
        self.base_url = "https://serpapi.com/search.json"
        self.rate_limit_delay = 1  # 1 second between requests
        self.config = custom_config
        
        print(f"🔧 GoogleJobsAPIServiceWithConfig initialized with config: {self.config}")
        
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
        Search for jobs using Google Jobs API with custom configuration and pagination
        
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
            all_jobs = []
            next_page_token = None
            effective_limit = limit or self.config.get("max_jobs_per_sync", 50)
            
            print(f"🎯 Target: {effective_limit} jobs total")
            
            # Continue fetching until we have enough jobs or no more pages
            while len(all_jobs) < effective_limit:
                # Prepare search parameters using config values or overrides
                params = {
                    "engine": self.config.get("engine", "google_jobs"),
                    "q": keywords,
                    "location": location or self.config.get("location", "India"),
                    "google_domain": self.config.get("google_domain", "google.com"),
                    "hl": self.config.get("hl", "en"),
                    "gl": self.config.get("gl", "in"),
                    "api_key": self.config.get("api_key"),
                    "output": self.config.get("output", "json")
                }
                
                # Add pagination token if we have one
                if next_page_token:
                    params["next_page_token"] = next_page_token
                    print(f"📄 Fetching page with token: {next_page_token[:20]}...")
            
                print(f"📝 Original keywords received: '{keywords}'")
                
                # Handle multiple keywords - SerpAPI works better with OR operator
                if ',' in keywords:
                    # Split keywords and join with OR
                    keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
                    if len(keyword_list) > 1:
                        # Use OR operator for multiple keywords
                        params["q"] = ' OR '.join([f'"{kw}"' for kw in keyword_list])
                        print(f"🔧 Converted to SerpAPI query: '{params['q']}'")
                    else:
                        params["q"] = keyword_list[0] if keyword_list else keywords
                else:
                    params["q"] = keywords
                
                # Add location type filter (work from home)
                ltype_value = self.config.get("ltype", 0)
                if work_from_home is not None:
                    ltype_value = 1 if work_from_home else 0
                if ltype_value == 1:
                    params["ltype"] = "1"
                    
                # Add no_cache parameter
                if self.config.get("no_cache", False):
                    params["no_cache"] = "true"
                    
                # Handle date posted filter
                date_filter = date_posted or self.config.get("date_posted", "any")
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
                job_type_filter = job_type or self.config.get("job_type", "any")
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
                
                # Log this page request
                page_num = 1 if not next_page_token else "Next"
                print(f"🔍 Searching Google Jobs API (Page {page_num}):")
                print(f"   Final Query: '{params['q']}'")
                print(f"   Location: '{params['location']}'")
                print(f"   Work from home: {ltype_value == 1}")
                print(f"   Date filter: {date_filter}")
                print(f"   Job type filter: {job_type_filter}")
                print(f"   Current results: {len(all_jobs)}/{effective_limit}")
            
                # Make API request
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.base_url, params=params) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            print(f"❌ Google Jobs API error {response.status}: {error_text}")
                            break
                        
                        data = await response.json()
                        
                        # LOG THE COMPLETE SERPAPI RESPONSE
                        print(f"\n" + "="*80)
                        print(f"📋 COMPLETE SERPAPI RESPONSE (Page {page_num}):")
                        print(f"="*80)
                        print(json.dumps(data, indent=2, default=str))
                        print(f"="*80 + "\n")
                        
                        # Check for API errors
                        if "error" in data:
                            print(f"❌ Google Jobs API error: {data['error']}")
                            break
                        
                        # Extract jobs from results
                        jobs_results = data.get("jobs_results", [])
                        
                        # LOG KEY RESPONSE FIELDS SUMMARY
                        print(f"📊 SERPAPI RESPONSE SUMMARY:")
                        print(f"   • Jobs found: {len(jobs_results)}")
                        print(f"   • Search info: {data.get('search_information', {})}")
                        print(f"   • Search params: {data.get('search_parameters', {})}")
                        print(f"   • Pagination: {data.get('serpapi_pagination', {})}")
                        
                        if jobs_results:
                            print(f"   • Sample job titles:")
                            for i, job in enumerate(jobs_results[:3]):
                                print(f"     {i+1}. {job.get('title', 'No title')} - {job.get('company_name', 'No company')}")
                        print()
                        
                        if not jobs_results:
                            print(f"⚠️ No more jobs found for query: '{params['q']}' in '{params['location']}'")
                            break
                        
                        print(f"✅ Found {len(jobs_results)} jobs in this page")
                        
                        # Convert to standard format and add to collection
                        for job in jobs_results:
                            if len(all_jobs) >= effective_limit:
                                break
                            
                            standardized_job = self._standardize_job_format(job)
                            if standardized_job:
                                all_jobs.append(standardized_job)
                        
                        # Check for next page
                        serpapi_pagination = data.get("serpapi_pagination", {})
                        next_page_token = serpapi_pagination.get("next_page_token")
                        
                        if not next_page_token:
                            print(f"📄 No more pages available")
                            break
                        
                        if len(all_jobs) >= effective_limit:
                            print(f"🎯 Reached target limit of {effective_limit} jobs")
                            break
                        
                        print(f"📄 Found next page token, continuing...")
                        
                        # Add delay between requests to respect rate limits
                        await asyncio.sleep(self.rate_limit_delay)
            
            print(f"📊 Final result: {len(all_jobs)} jobs collected from Google Jobs API")
            return all_jobs[:effective_limit]  # Ensure we don't exceed the limit
                    
        except aiohttp.ClientError as e:
            print(f"❌ Network error calling Google Jobs API with custom config: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error in Google Jobs API with custom config: {str(e)}")
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
            
            # If no structured requirements found, extract from description
            if not requirements or requirements.strip() == "":
                # Import the requirements extraction function
                from ..job_routes import extract_requirements_from_description
                requirements = extract_requirements_from_description(
                    description, 
                    requirements
                )
            
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
                "source": "Google Jobs API (Custom Config)",
                "via": job_data.get("via", ""),
                "thumbnail": job_data.get("thumbnail", ""),
                "job_id": job_data.get("job_id", ""),
                "extracted_at": datetime.utcnow().isoformat(),
                "config_used": {
                    "location": self.config.get("location"),
                    "max_jobs": self.config.get("max_jobs_per_sync"),
                    "work_type": "Remote Only" if self.config.get("ltype") == 1 else "All Jobs",
                    "date_posted": self.config.get("date_posted"),
                    "job_type": self.config.get("job_type")
                }
            }
            
            return standardized_job
            
        except Exception as e:
            print(f"⚠️ Error standardizing job format with custom config: {str(e)}")
            return None
    
    def test_api_connection(self) -> bool:
        """
        Test if the custom configuration is working
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            params = {
                "engine": self.config.get("engine", "google_jobs"),
                "q": "test job",
                "location": self.config.get("location", "India"),
                "google_domain": self.config.get("google_domain", "google.com"),
                "hl": self.config.get("hl", "en"),
                "gl": self.config.get("gl", "in"),
                "api_key": self.config.get("api_key")
            }
            
            print(f"🧪 Testing custom SerpAPI config with params: {params}")
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" not in data:
                    print("✅ Custom Google Jobs API configuration test successful")
                    return True
                else:
                    print(f"❌ Custom Google Jobs API error: {data['error']}")
                    return False
            else:
                print(f"❌ Custom Google Jobs API HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Custom Google Jobs API connection test failed: {str(e)}")
            return False


# Test function for development
async def test_custom_google_jobs_api():
    """Test function to verify custom Google Jobs API integration"""
    
    # Example custom configuration
    custom_config = {
        "api_key": "a448fc3f98bea2711a110c46c86d75cc09e786b729a8212f666c89d35800429f",
        "engine": "google_jobs",
        "location": "Mumbai, India",
        "google_domain": "google.com",
        "hl": "en",
        "gl": "in",
        "max_jobs_per_sync": 25,
        "search_radius": 30,
        "ltype": 1,  # Remote only
        "date_posted": "week",
        "job_type": "full_time",
        "no_cache": False,
        "output": "json"
    }
    
    api_service = GoogleJobsAPIServiceWithConfig(custom_config)
    
    print("🧪 Testing Custom Google Jobs API Service...")
    
    # Test connection
    if not api_service.test_api_connection():
        print("❌ Custom API connection test failed")
        return
    
    # Test job search
    print("\n🔍 Testing custom job search...")
    jobs = await api_service.search_jobs(
        keywords="python developer",
        location="Mumbai, India",
        limit=5
    )
    
    if jobs:
        print(f"✅ Successfully fetched {len(jobs)} jobs with custom config")
        for i, job in enumerate(jobs[:2], 1):
            print(f"\nJob {i}:")
            print(f"  Title: {job['title']}")
            print(f"  Company: {job['company']}")
            print(f"  Location: {job['location']}")
            print(f"  Source: {job['source']}")
            print(f"  Config Used: {job['config_used']}")
    else:
        print("❌ No jobs found with custom configuration")

# Run test if executed directly
if __name__ == "__main__":
    asyncio.run(test_custom_google_jobs_api())
