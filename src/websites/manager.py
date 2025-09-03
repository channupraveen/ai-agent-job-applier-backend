"""
Website Automation Manager
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import asyncio
from datetime import datetime

from ..automation.browser import BrowserEngine
from ..selectors.job_site_selectors import get_selectors_for_site
from config import Config


class JobSiteType(Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    NAUKRI = "naukri"
    GLASSDOOR = "glassdoor"
    MONSTER = "monster"
    SHINE = "shine"


@dataclass 
class JobSiteConfig:
    """Configuration for a job site"""
    name: str
    base_url: str
    search_url: str
    login_required: bool = False
    rate_limit_delay: int = 30  # seconds between requests
    max_applications_per_session: int = 10
    supports_auto_apply: bool = False
    

class WebsiteManager:
    """Manages automation across different job websites"""
    
    def __init__(self):
        self.config = Config()
        self.browser_engine = BrowserEngine()
        self.supported_sites = self._initialize_supported_sites()
        self.current_site = None
        
    def _initialize_supported_sites(self) -> Dict[str, JobSiteConfig]:
        """Initialize supported job sites configuration"""
        return {
            "linkedin": JobSiteConfig(
                name="LinkedIn",
                base_url="https://www.linkedin.com",
                search_url="https://www.linkedin.com/jobs/search",
                login_required=True,
                rate_limit_delay=45,
                max_applications_per_session=5,
                supports_auto_apply=True
            ),
            "indeed": JobSiteConfig(
                name="Indeed",
                base_url="https://www.indeed.com",
                search_url="https://www.indeed.com/jobs",
                login_required=False,
                rate_limit_delay=30,
                max_applications_per_session=10,
                supports_auto_apply=False
            ),
            "naukri": JobSiteConfig(
                name="Naukri.com",
                base_url="https://www.naukri.com",
                search_url="https://www.naukri.com/jobs",
                login_required=True,
                rate_limit_delay=35,
                max_applications_per_session=8,
                supports_auto_apply=True
            ),
            "glassdoor": JobSiteConfig(
                name="Glassdoor",
                base_url="https://www.glassdoor.com",
                search_url="https://www.glassdoor.com/Jobs",
                login_required=False,
                rate_limit_delay=40,
                max_applications_per_session=6,
                supports_auto_apply=False
            ),
            "monster": JobSiteConfig(
                name="Monster",
                base_url="https://www.monsterindia.com",
                search_url="https://www.monsterindia.com/search",
                login_required=False,
                rate_limit_delay=25,
                max_applications_per_session=10,
                supports_auto_apply=False
            ),
            "shine": JobSiteConfig(
                name="Shine",
                base_url="https://www.shine.com",
                search_url="https://www.shine.com/jobs",
                login_required=False,
                rate_limit_delay=30,
                max_applications_per_session=10,
                supports_auto_apply=False
            )
        }
    
    async def initialize_site(self, site_name: str, credentials: Optional[Dict] = None) -> bool:
        """Initialize connection to a specific job site"""
        try:
            if site_name not in self.supported_sites:
                raise ValueError(f"Unsupported site: {site_name}")
            
            self.current_site = self.supported_sites[site_name]
            
            # Initialize browser
            await self.browser_engine.initialize_browser(
                headless=self.config.BROWSER_HEADLESS
            )
            
            # Navigate to site
            await self.browser_engine.navigate_to_website(self.current_site.base_url)
            
            # Login if required
            if self.current_site.login_required and credentials:
                login_success = await self._perform_login(site_name, credentials)
                if not login_success:
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error initializing site {site_name}: {str(e)}")
            return False
    
    async def search_jobs(self, search_params: Dict[str, Any]) -> List[Dict]:
        """Search for jobs on current site"""
        try:
            if not self.current_site:
                raise ValueError("No site initialized")
            
            # Navigate to search page
            await self.browser_engine.navigate_to_website(self.current_site.search_url)
            
            # Get site-specific selectors
            selectors = get_selectors_for_site(self.current_site.name.lower())
            
            # Fill search form
            search_data = {
                "keywords": search_params.get("keywords", ""),
                "location": search_params.get("location", ""),
                "experience": search_params.get("experience_level", "")
            }
            
            await self.browser_engine.fill_search_form(selectors["search"], search_data)
            
            # Get job listings
            jobs = await self._extract_job_listings(selectors["job_listings"])
            
            return jobs
            
        except Exception as e:
            print(f"Error searching jobs: {str(e)}")
            return []
    
    async def apply_to_job(self, job_id: str, application_data: Dict) -> Dict[str, Any]:
        """Apply to a specific job"""
        try:
            if not self.current_site:
                raise ValueError("No site initialized")
            
            # Check if auto-apply is supported
            if not self.current_site.supports_auto_apply:
                return {
                    "success": False,
                    "message": f"Auto-apply not supported on {self.current_site.name}",
                    "action_required": "manual_application"
                }
            
            # Navigate to job application page
            job_url = self._build_job_url(job_id)
            await self.browser_engine.navigate_to_website(job_url)
            
            # Get application selectors
            selectors = get_selectors_for_site(self.current_site.name.lower())
            
            # Fill application form
            success = await self.browser_engine.fill_application_form(
                selectors["application"], 
                application_data
            )
            
            if not success:
                return {
                    "success": False,
                    "message": "Failed to fill application form"
                }
            
            # Submit application
            submission_result = await self.browser_engine.submit_application()
            
            # Take screenshot for verification
            screenshot_path = await self.browser_engine.take_screenshot(
                f"application_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            return {
                "success": True,
                "application_id": submission_result.get("application_id"),
                "screenshot": screenshot_path,
                "site": self.current_site.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error applying to job: {str(e)}",
                "error_type": type(e).__name__
            }
    
    async def bulk_apply(self, jobs: List[Dict], application_data: Dict) -> Dict[str, Any]:
        """Apply to multiple jobs in sequence"""
        try:
            results = {
                "total_jobs": len(jobs),
                "successful_applications": 0,
                "failed_applications": 0,
                "applications": [],
                "errors": []
            }
            
            max_apps = min(len(jobs), self.current_site.max_applications_per_session)
            
            for i, job in enumerate(jobs[:max_apps]):
                try:
                    # Apply rate limiting
                    if i > 0:
                        await asyncio.sleep(self.current_site.rate_limit_delay)
                    
                    # Apply to job
                    result = await self.apply_to_job(job["id"], application_data)
                    
                    if result["success"]:
                        results["successful_applications"] += 1
                    else:
                        results["failed_applications"] += 1
                        results["errors"].append({
                            "job_id": job["id"],
                            "error": result["message"]
                        })
                    
                    results["applications"].append({
                        "job_id": job["id"],
                        "job_title": job.get("title", "Unknown"),
                        "company": job.get("company", "Unknown"),
                        "result": result
                    })
                    
                except Exception as e:
                    results["failed_applications"] += 1
                    results["errors"].append({
                        "job_id": job.get("id", "unknown"),
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error in bulk apply: {str(e)}"
            }
    
    async def get_site_status(self) -> Dict[str, Any]:
        """Get current site connection status"""
        if not self.current_site:
            return {
                "connected": False,
                "site": None,
                "message": "No site initialized"
            }
        
        return {
            "connected": True,
            "site": self.current_site.name,
            "supports_auto_apply": self.current_site.supports_auto_apply,
            "max_applications": self.current_site.max_applications_per_session,
            "rate_limit_delay": self.current_site.rate_limit_delay
        }
    
    async def close_connection(self):
        """Close connection to current site"""
        if self.browser_engine:
            self.browser_engine.close_browser()
        self.current_site = None
    
    def get_supported_sites(self) -> List[Dict[str, Any]]:
        """Get list of all supported job sites"""
        sites = []
        for site_key, site_config in self.supported_sites.items():
            sites.append({
                "key": site_key,
                "name": site_config.name,
                "base_url": site_config.base_url,
                "login_required": site_config.login_required,
                "supports_auto_apply": site_config.supports_auto_apply,
                "max_applications": site_config.max_applications_per_session
            })
        return sites
    
    # Private helper methods
    async def _perform_login(self, site_name: str, credentials: Dict) -> bool:
        """Perform login for sites that require authentication"""
        try:
            selectors = get_selectors_for_site(site_name)
            login_selectors = selectors.get("login", {})
            
            if not login_selectors:
                return False
            
            # Fill login form
            login_data = {
                "username": credentials.get("username", ""),
                "password": credentials.get("password", "")
            }
            
            success = await self.browser_engine.fill_application_form(
                login_selectors, 
                login_data
            )
            
            if success:
                # Wait for login to complete
                await asyncio.sleep(3)
                return True
            
            return False
            
        except Exception as e:
            print(f"Login error for {site_name}: {str(e)}")
            return False
    
    async def _extract_job_listings(self, job_selectors: Dict) -> List[Dict]:
        """Extract job listings from current page"""
        try:
            # This would use selenium to extract job data
            # For now, return mock data
            
            mock_jobs = [
                {
                    "id": f"job_{i}",
                    "title": f"Python Developer {i}",
                    "company": f"Tech Company {i}",
                    "location": "Remote",
                    "description": f"Job description for position {i}",
                    "url": f"https://example.com/job/{i}",
                    "posted_date": datetime.utcnow().isoformat(),
                    "source": self.current_site.name
                }
                for i in range(1, 6)
            ]
            
            return mock_jobs
            
        except Exception as e:
            print(f"Error extracting job listings: {str(e)}")
            return []
    
    def _build_job_url(self, job_id: str) -> str:
        """Build full URL for a specific job"""
        base_url = self.current_site.base_url
        if "linkedin" in base_url:
            return f"{base_url}/jobs/view/{job_id}"
        elif "indeed" in base_url:
            return f"{base_url}/viewjob?jk={job_id}"
        elif "naukri" in base_url:
            return f"{base_url}/job-listings-{job_id}"
        else:
            return f"{base_url}/job/{job_id}"


# Global website manager instance
website_manager = WebsiteManager()
