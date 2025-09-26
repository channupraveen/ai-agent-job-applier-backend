"""
Indeed India RSS Job Fetcher - Using Requests
"""

import requests
import feedparser
import asyncio
from typing import List, Dict
from datetime import datetime
import urllib.parse
import time

class IndeedIndiaRSSFetcher:
    def __init__(self):
        self.base_rss_url = "https://in.indeed.com/rss"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml'
        }
        self.session.headers.update(self.headers)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    async def search_jobs(self, keywords: str, location: str = "Delhi", limit: int = 50) -> List[Dict]:
        """Fetch jobs from Indeed India RSS feeds"""
        try:
            jobs = []
            
            # Build RSS URL with search params
            params = {
                'q': keywords,
                'l': location,
                'radius': '25',
                'limit': str(min(limit, 50))  # RSS limit
            }
            
            rss_url = f"{self.base_rss_url}?{urllib.parse.urlencode(params)}"
            print(f"Fetching from Indeed RSS: {rss_url}")
            
            response = self.session.get(rss_url, timeout=30)
            if response.status_code == 200:
                jobs = self._parse_rss_feed(response.text, keywords)
            else:
                print(f"Indeed RSS request failed: {response.status_code}")
                return []
            
            print(f"Indeed RSS found {len(jobs)} jobs")
            return jobs[:limit]
            
        except Exception as e:
            print(f"Indeed RSS error: {str(e)}")
            return []
    
    def _parse_rss_feed(self, rss_content: str, keywords: str) -> List[Dict]:
        """Parse RSS feed content"""
        jobs = []
        
        try:
            feed = feedparser.parse(rss_content)
            
            for entry in feed.entries:
                try:
                    job = self._extract_rss_job_data(entry, keywords)
                    if job:
                        jobs.append(job)
                except Exception:
                    continue
            
            return jobs
            
        except Exception as e:
            print(f"RSS parsing error: {str(e)}")
            return []
    
    def _extract_rss_job_data(self, entry, keywords: str) -> Dict:
        """Extract job data from RSS entry"""
        try:
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()
            description = entry.get('description', '').strip()
            published = entry.get('published', '')
            
            # Extract company and location from title (Indeed format: "Job Title - Company - Location")
            title_parts = title.split(' - ')
            job_title = title_parts[0] if len(title_parts) > 0 else title
            company = title_parts[1] if len(title_parts) > 1 else "Not specified"
            location = title_parts[2] if len(title_parts) > 2 else "India"
            
            # Clean up description (remove HTML tags if any)
            import re
            description = re.sub('<[^<]+?>', '', description)
            description = description.strip()[:500]
            
            return {
                'title': job_title,
                'company': company,
                'location': location,
                'url': link,
                'description': description if description else f"Exciting {keywords} opportunity at {company}",
                'requirements': f"{keywords}, Professional experience, Strong communication skills",
                'salary': "Competitive salary",
                'posted_date': published,
                'job_type': 'full-time',
                'source': 'indeed_india_rss'
            }
            
        except Exception as e:
            return None

# Alternative Indeed locations for better coverage
class IndeedMultiLocationFetcher:
    def __init__(self):
        self.fetcher = IndeedIndiaRSSFetcher()
        self.indian_cities = [
            "Delhi", "Mumbai", "Bangalore", "Hyderabad", "Chennai", 
            "Pune", "Kolkata", "Ahmedabad", "Gurgaon", "Noida"
        ]
    
    async def search_jobs_multiple_cities(self, keywords: str, limit: int = 100) -> List[Dict]:
        """Search jobs across multiple Indian cities"""
        all_jobs = []
        jobs_per_city = max(10, limit // len(self.indian_cities))
        
        async with self.fetcher as fetcher:
            for city in self.indian_cities[:5]:  # Top 5 cities to avoid rate limits
                try:
                    city_jobs = await fetcher.search_jobs(keywords, city, jobs_per_city)
                    all_jobs.extend(city_jobs)
                    
                    if len(all_jobs) >= limit:
                        break
                        
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"Error fetching jobs from {city}: {str(e)}")
                    continue
        
        # Remove duplicates based on URL
        unique_jobs = []
        seen_urls = set()
        
        for job in all_jobs:
            url = job.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)
        
        print(f"Indeed multi-city found {len(unique_jobs)} unique jobs")
        return unique_jobs[:limit]

# Test function
async def test_indeed_rss():
    async with IndeedIndiaRSSFetcher() as fetcher:
        jobs = await fetcher.search_jobs("python developer", "Delhi", 10)
        print(f"Found {len(jobs)} jobs")
        for job in jobs[:3]:
            print(f"- {job.get('title')} at {job.get('company')}")

if __name__ == "__main__":
    asyncio.run(test_indeed_rss())
