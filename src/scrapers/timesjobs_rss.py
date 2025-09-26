"""
TimesJobs RSS Feed Fetcher - Using Requests Only
"""

import requests
import feedparser
import asyncio
from typing import List, Dict
from datetime import datetime
import urllib.parse
import re
import time

class TimesJobsRSSFetcher:
    def __init__(self):
        self.rss_urls = [
            "https://www.timesjobs.com/rss/jobs-rss.xml",
            "https://www.timesjobs.com/rss/jobs-by-skills-rss.xml",
            "https://www.timesjobs.com/rss/jobs-by-location-rss.xml"
        ]
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
        """Fetch jobs from TimesJobs RSS feeds"""
        try:
            all_jobs = []
            
            # Fetch from multiple RSS feeds
            for rss_url in self.rss_urls:
                try:
                    response = self.session.get(rss_url, timeout=30)
                    if response.status_code == 200:
                        jobs = self._parse_rss_feed(response.text, keywords, location)
                        all_jobs.extend(jobs)
                    else:
                        print(f"TimesJobs RSS failed: {response.status_code} for {rss_url}")
                    
                    await asyncio.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error fetching TimesJobs RSS {rss_url}: {str(e)}")
                    continue
            
            # Filter and deduplicate
            filtered_jobs = self._filter_jobs(all_jobs, keywords, location)
            print(f"TimesJobs RSS found {len(filtered_jobs)} jobs")
            return filtered_jobs[:limit]
            
        except Exception as e:
            print(f"TimesJobs RSS error: {str(e)}")
            return []
    
    def _parse_rss_feed(self, rss_content: str, keywords: str, location: str) -> List[Dict]:
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
            print(f"TimesJobs RSS parsing error: {str(e)}")
            return []
    
    def _extract_rss_job_data(self, entry, keywords: str) -> Dict:
        """Extract job data from RSS entry"""
        try:
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()
            description = entry.get('description', '').strip()
            published = entry.get('published', '')
            
            # Clean description
            description = re.sub('<[^<]+?>', '', description)
            description = description.strip()
            
            # Extract company from description or title
            company = "Not specified"
            if "Company:" in description:
                company_match = re.search(r'Company:\s*([^\n\r]+)', description)
                if company_match:
                    company = company_match.group(1).strip()
            
            # Extract location
            location = "India"
            if "Location:" in description:
                location_match = re.search(r'Location:\s*([^\n\r]+)', description)
                if location_match:
                    location = location_match.group(1).strip()
            
            # Extract experience
            experience = ""
            if "Experience:" in description:
                exp_match = re.search(r'Experience:\s*([^\n\r]+)', description)
                if exp_match:
                    experience = exp_match.group(1).strip()
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': link,
                'description': description[:500] if description else f"Exciting {keywords} opportunity at {company}",
                'requirements': f"{keywords}, {experience}" if experience else f"{keywords}, Professional experience",
                'salary': "Competitive salary",
                'posted_date': published,
                'job_type': 'full-time',
                'source': 'timesjobs_rss'
            }
            
        except Exception as e:
            return None
    
    def _filter_jobs(self, jobs: List[Dict], keywords: str, location: str) -> List[Dict]:
        """Filter jobs based on keywords and location"""
        filtered = []
        seen_urls = set()
        
        keywords_lower = keywords.lower().split()
        location_lower = location.lower()
        
        for job in jobs:
            # Remove duplicates
            url = job.get('url', '')
            if url in seen_urls:
                continue
            
            # Filter by keywords
            job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            if not any(keyword in job_text for keyword in keywords_lower):
                continue
            
            # Filter by location (flexible matching)
            job_location = job.get('location', '').lower()
            if location_lower not in ['remote', 'india'] and location_lower not in job_location:
                # Still include if it's a major Indian city or remote
                if not any(city in job_location for city in ['delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'pune', 'remote']):
                    continue
            
            seen_urls.add(url)
            filtered.append(job)
        
        return filtered

# Test function
async def test_timesjobs_rss():
    async with TimesJobsRSSFetcher() as fetcher:
        jobs = await fetcher.search_jobs("python developer", "Delhi", 10)
        print(f"Found {len(jobs)} jobs")
        for job in jobs[:3]:
            print(f"- {job.get('title')} at {job.get('company')}")

if __name__ == "__main__":
    asyncio.run(test_timesjobs_rss())
