"""
External Job Site API Integrations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
import asyncio
from dataclasses import dataclass
import json

from config import Config


@dataclass
class ExternalJobResult:
    """Standardized job result from external APIs"""
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    salary: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[str] = None
    source: str = ""
    requirements: Optional[str] = None


class ExternalJobIntegration:
    """Base class for external job site integrations"""
    
    def __init__(self):
        self.config = Config()
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def search_jobs(self, query: str, location: str = "", **kwargs) -> List[ExternalJobResult]:
        """Search jobs - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def get_job_details(self, job_id: str) -> Optional[ExternalJobResult]:
        """Get detailed job information"""
        raise NotImplementedError
    
    async def close(self):
        """Close HTTP session"""
        await self.session.aclose()


class LinkedInJobsAPI(ExternalJobIntegration):
    """LinkedIn Jobs API integration (requires LinkedIn API access)"""
    
    def __init__(self):
        super().__init__()
        self.api_key = getattr(self.config, 'LINKEDIN_API_KEY', '')
        self.base_url = "https://api.linkedin.com/v2"
    
    async def search_jobs(self, query: str, location: str = "", **kwargs) -> List[ExternalJobResult]:
        """Search LinkedIn jobs"""
        try:
            if not self.api_key:
                # Return mock data if no API key
                return self._get_mock_linkedin_jobs(query, location)
            
            params = {
                "keywords": query,
                "location": location,
                "count": kwargs.get("limit", 25),
                "start": kwargs.get("offset", 0)
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            response = await self.session.get(
                f"{self.base_url}/jobSearch",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_linkedin_jobs(data)
            else:
                return []
                
        except Exception as e:
            print(f"LinkedIn API error: {str(e)}")
            return self._get_mock_linkedin_jobs(query, location)
    
    def _parse_linkedin_jobs(self, data: dict) -> List[ExternalJobResult]:
        """Parse LinkedIn API response"""
        jobs = []
        for job in data.get("elements", []):
            jobs.append(ExternalJobResult(
                id=job.get("id", ""),
                title=job.get("title", ""),
                company=job.get("companyDetails", {}).get("name", ""),
                location=job.get("formattedLocation", ""),
                description=job.get("description", ""),
                url=f"https://www.linkedin.com/jobs/view/{job.get('id', '')}",
                salary=job.get("salary", {}).get("displayValue"),
                job_type=job.get("workplaceTypes", [{}])[0].get("displayValue"),
                posted_date=job.get("listedAt"),
                source="LinkedIn"
            ))
        return jobs
    
    def _get_mock_linkedin_jobs(self, query: str, location: str) -> List[ExternalJobResult]:
        """Mock LinkedIn jobs for testing"""
        return [
            ExternalJobResult(
                id=f"linkedin_{i}",
                title=f"{query} Developer {i}",
                company=f"LinkedIn Company {i}",
                location=location or "Remote",
                description=f"Job description for {query} position {i} at LinkedIn Company {i}",
                url=f"https://www.linkedin.com/jobs/view/linkedin_{i}",
                salary="$80,000 - $120,000",
                job_type="Full-time",
                posted_date=(datetime.now() - timedelta(days=i)).isoformat(),
                source="LinkedIn"
            )
            for i in range(1, 6)
        ]


class IndeedJobsAPI(ExternalJobIntegration):
    """Indeed Jobs API integration"""
    
    def __init__(self):
        super().__init__()
        self.publisher_id = getattr(self.config, 'INDEED_PUBLISHER_ID', '')
        self.base_url = "https://api.indeed.com/ads/apisearch"
    
    async def search_jobs(self, query: str, location: str = "", **kwargs) -> List[ExternalJobResult]:
        """Search Indeed jobs"""
        try:
            if not self.publisher_id:
                return self._get_mock_indeed_jobs(query, location)
            
            params = {
                "publisher": self.publisher_id,
                "q": query,
                "l": location,
                "sort": "date",
                "radius": kwargs.get("radius", 25),
                "limit": kwargs.get("limit", 25),
                "start": kwargs.get("offset", 0),
                "format": "json",
                "v": "2"
            }
            
            response = await self.session.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_indeed_jobs(data)
            else:
                return []
                
        except Exception as e:
            print(f"Indeed API error: {str(e)}")
            return self._get_mock_indeed_jobs(query, location)
    
    def _parse_indeed_jobs(self, data: dict) -> List[ExternalJobResult]:
        """Parse Indeed API response"""
        jobs = []
        for job in data.get("results", []):
            jobs.append(ExternalJobResult(
                id=job.get("jobkey", ""),
                title=job.get("jobtitle", ""),
                company=job.get("company", ""),
                location=job.get("formattedLocation", ""),
                description=job.get("snippet", ""),
                url=job.get("url", ""),
                salary=job.get("salary"),
                job_type=job.get("formattedRelativeTime"),
                posted_date=job.get("date"),
                source="Indeed"
            ))
        return jobs
    
    def _get_mock_indeed_jobs(self, query: str, location: str) -> List[ExternalJobResult]:
        """Mock Indeed jobs for testing"""
        return [
            ExternalJobResult(
                id=f"indeed_{i}",
                title=f"{query} Specialist {i}",
                company=f"Indeed Corp {i}",
                location=location or "Remote",
                description=f"Excellent opportunity for {query} specialist at Indeed Corp {i}",
                url=f"https://www.indeed.com/viewjob?jk=indeed_{i}",
                salary="$70,000 - $100,000",
                job_type="Full-time",
                posted_date=(datetime.now() - timedelta(days=i)).isoformat(),
                source="Indeed"
            )
            for i in range(1, 6)
        ]


class JobAggregatorService:
    """Service to aggregate jobs from multiple external sources"""
    
    def __init__(self):
        self.integrations = {
            "linkedin": LinkedInJobsAPI(),
            "indeed": IndeedJobsAPI()
        }
    
    async def search_all_sources(
        self, 
        query: str, 
        location: str = "", 
        sources: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, List[ExternalJobResult]]:
        """Search jobs across all or specified sources"""
        
        if sources is None:
            sources = list(self.integrations.keys())
        
        results = {}
        tasks = []
        
        for source in sources:
            if source in self.integrations:
                task = asyncio.create_task(
                    self._search_source(source, query, location, **kwargs),
                    name=source
                )
                tasks.append(task)
        
        # Wait for all tasks to complete
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for task, result in zip(tasks, completed_tasks):
            source = task.get_name()
            if isinstance(result, Exception):
                print(f"Error searching {source}: {str(result)}")
                results[source] = []
            else:
                results[source] = result
        
        return results
    
    async def _search_source(
        self, 
        source: str, 
        query: str, 
        location: str, 
        **kwargs
    ) -> List[ExternalJobResult]:
        """Search a single source"""
        try:
            integration = self.integrations[source]
            return await integration.search_jobs(query, location, **kwargs)
        except Exception as e:
            print(f"Error searching {source}: {str(e)}")
            return []
    
    def get_combined_results(
        self, 
        source_results: Dict[str, List[ExternalJobResult]]
    ) -> List[ExternalJobResult]:
        """Combine results from all sources, removing duplicates"""
        
        all_jobs = []
        seen_urls = set()
        
        for source, jobs in source_results.items():
            for job in jobs:
                # Simple duplicate detection based on URL and title+company
                job_key = (job.url, f"{job.title}_{job.company}")
                if job_key not in seen_urls:
                    seen_urls.add(job_key)
                    all_jobs.append(job)
        
        # Sort by posted date (most recent first)
        return sorted(
            all_jobs, 
            key=lambda x: x.posted_date or "", 
            reverse=True
        )
    
    async def close_all(self):
        """Close all integration sessions"""
        for integration in self.integrations.values():
            await integration.close()


# Global aggregator service instance
job_aggregator_service = JobAggregatorService()
