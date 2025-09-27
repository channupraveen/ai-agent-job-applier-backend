"""
Real Naukri.com Job Scraper for Indian Jobs - Using Requests
"""

import asyncio
import requests
import json
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime
import random
import time

class NaukriJobScraper:
    def __init__(self):
        self.base_url = "https://www.naukri.com"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(self.headers)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    async def search_jobs(self, keywords: str, location: str = "Delhi", limit: int = 50) -> List[Dict]:
        """Search jobs on Naukri.com"""
        try:
            jobs = []
            
            # Build search URL
            search_url = f"{self.base_url}/jobs-search"
            params = {
                'q': keywords,
                'l': location,
                'experience': '0',
                'salary': '',
                'industry': '',
                'jobAge': '1',
                'src': 'jobsearchDesk',
                'start': 0
            }
            
            pages_to_scrape = min(3, (limit // 20) + 1)
            
            for page in range(pages_to_scrape):
                params['start'] = page * 20
                
                try:
                    response = self.session.get(search_url, params=params, timeout=30)
                    if response.status_code == 200:
                        page_jobs = self._parse_job_listings(response.text, keywords)
                        jobs.extend(page_jobs)
                        
                        if len(jobs) >= limit:
                            break
                    else:
                        print(f"Naukri request failed: {response.status_code}")
                        break
                    
                    # Rate limiting - be respectful
                    await asyncio.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    print(f"Error scraping Naukri page {page}: {str(e)}")
                    continue
            
            print(f"Naukri found {len(jobs)} jobs")
            return jobs[:limit]
            
        except Exception as e:
            print(f"Naukri scraper error: {str(e)}")
            return []
    
    def _parse_job_listings(self, html: str, keywords: str) -> List[Dict]:
        """Parse job listings from HTML"""
        jobs = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.find_all('div', class_=['row', 'jobTuple'])
            
            for card in job_cards:
                try:
                    job = self._extract_job_data(card, keywords)
                    if job and job.get('url'):
                        jobs.append(job)
                except Exception:
                    continue
            
            return jobs
            
        except Exception as e:
            print(f"Naukri HTML parsing error: {str(e)}")
            return []
    
    def _extract_job_data(self, card, keywords: str) -> Dict:
        """Extract job data from a job card"""
        try:
            # Title and URL
            title_elem = card.find('a', class_='title')
            title = title_elem.text.strip() if title_elem else ""
            url = self.base_url + title_elem['href'] if title_elem and title_elem.get('href') else ""
            
            # Company
            company_elem = card.find('a', class_='subTitle')
            company = company_elem.text.strip() if company_elem else ""
            
            # Location
            location_elem = card.find('span', class_='ellipsis location')
            location = location_elem.text.strip() if location_elem else ""
            
            # Experience
            exp_elem = card.find('span', class_='ellipsis experience')
            experience = exp_elem.text.strip() if exp_elem else ""
            
            # Salary
            salary_elem = card.find('span', class_='ellipsis salary')
            salary = salary_elem.text.strip() if salary_elem else "Not disclosed"
            
            # Posted date
            posted_elem = card.find('span', class_='job-post-day')
            posted_date = posted_elem.text.strip() if posted_elem else "Recently posted"
            
            # Description
            desc_elem = card.find('div', class_='job-description')
            description = desc_elem.text.strip() if desc_elem else f"Exciting {keywords} opportunity at {company}"
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': url,
                'description': description[:500],
                'requirements': f"{keywords}, {experience}, Communication skills",
                'salary': salary,
                'posted_date': posted_date,
                'job_type': 'full-time',
                'source': 'naukri'
            }
            
        except Exception as e:
            return None

# Test function
async def test_naukri_scraper():
    async with NaukriJobScraper() as scraper:
        jobs = await scraper.search_jobs("python developer", "Delhi", 10)
        print(f"Found {len(jobs)} jobs")
        for job in jobs[:3]:
            print(f"- {job.get('title')} at {job.get('company')}")

if __name__ == "__main__":
    asyncio.run(test_naukri_scraper())
