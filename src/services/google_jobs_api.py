"""
Google Jobs API Service using SerpAPI
Fetches real job data from Google Jobs search results
"""

import requests
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


class GoogleJobsAPIService:
    """Service for fetching jobs from Google Jobs API via SerpAPI"""
    
    def __init__(self, api_key: str = "a448fc3f98bea2711a110c46c86d75cc09e786b729a8212f666c89d35800429f"):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search.json"
        self.rate_limit_delay = 1  # 1 second between requests
        
    async def search_jobs(
        self, 
        keywords: str, 
        location: str = "India",
        limit: int = 30,
        work_from_home: bool = False,
        job_type: str = None,
        date_posted: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs using Google Jobs API
        
        Args:
            keywords: Search keywords (e.g., "software engineer", "python developer")
            location: Location to search in (default: "India")
            limit: Maximum number of jobs to return (default: 30)
            work_from_home: Filter for remote jobs (default: False)
            job_type: Job type filter (full-time, part-time, contract)
            date_posted: Date filter (yesterday, last week, last month)
            
        Returns:
            List of job dictionaries with standardized format
        """
        try:
            # Prepare search parameters
            params = {
                "engine": "google_jobs",
                "q": f"{keywords} {location}",
                "location": location,
                "hl": "en",
                "gl": "in",  # India-specific results
                "api_key": self.api_key
            }
            
            # Add optional filters
            if work_from_home:
                params["ltype"] = "1"  # Work from home filter
                
            if job_type:
                params["q"] += f" {job_type}"
                
            if date_posted:
                if date_posted == "yesterday":
                    params["uds"] = "ADvngMg3E3nZHBbR_ywpl3w6An90vX97JE-gu4BCrGwDJohluO_YEx5Dyq_CVMlfRWHofzvK0Wk891JW2_eoOlnHmlGhoQlGfxNX50Okp0sL0zMn3nwdzY_McxyGs0hImvmu_hEEFqi-4xASRa-l3trlS2XDqCTc4P2bJB8q1JFTtzHoIpfg98trHjtghpEcpH8ESmICX9xJL1_jOxNc-Jj3MQVqoKQQj7LoM84AVPDMESy36tT36cTj2iVbBT6f5RVyJrrp2LahzKGMydKp5doDK56yVOIvgqJjjE_z2R67VkMtqoybidk"
                elif date_posted == "last_week":
                    params["uds"] = "ADvngMg3E3nZHBbR_ywpl3w6An90vX97JE-gu4BCrGwDJohluGEiwNCBuePlScFgQPeZH8hoEIyVEdYwhzCz4-CgEiwMvBboHCRaWYLAOFnab9e8YOmH2R6krQFyehIFp0TQeo332IsFVWHPMQ5aaDzWEcMKVaMdiJnVrlWWVzQv6njJEsGo4_7V9ekRIJwqi2HPU8gpLUCnX_4j0K_Q7f7gPXlem6q3Z7jUzVx5v5PDYnFCc62WQziX1GuTN_550pnbDcFTC7QCsrJmxVjIuzglOim1DS6-gQVnyChXenTK141YjJYBjHA"
            
            print(f"🔍 Searching Google Jobs API: '{keywords}' in '{location}'")
            print(f"📊 Parameters: {params}")
            
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
                        print(f"⚠️ No jobs found for '{keywords}' in '{location}'")
                        return []
                    
                    print(f"✅ Found {len(jobs_results)} jobs from Google Jobs API")
                    
                    # Convert to standard format and limit results
                    standardized_jobs = []
                    for job in jobs_results[:limit]:
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
        Test if the API key and connection are working
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            params = {
                "engine": "google_jobs",
                "q": "test job",
                "location": "India",
                "api_key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" not in data:
                    print("✅ Google Jobs API connection test successful")
                    return True
                else:
                    print(f"❌ Google Jobs API error: {data['error']}")
                    return False
            else:
                print(f"❌ Google Jobs API HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Google Jobs API connection test failed: {str(e)}")
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
