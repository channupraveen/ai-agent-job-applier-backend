"""
LinkedIn Job Scraper using Playwright
"""

import asyncio
import random
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
from urllib.parse import quote_plus
import json
import time
from datetime import datetime

class LinkedInJobScraper:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    async def start_browser(self, headless: bool = True):
        """Initialize browser with stealth settings"""
        try:
            playwright = await async_playwright().start()
            
            # Launch browser with anti-detection settings
            self.browser = await playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-web-security',
                    '--disable-features=translate',
                    '--disable-ipc-flooding-protection'
                ]
            )
            
            # Create context with random user agent
            context = await self.browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            
            self.page = await context.new_page()
            
            # Add stealth scripts
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                window.chrome = {
                    runtime: {},
                };
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            print("✅ Browser started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error starting browser: {str(e)}")
            return False

    async def search_jobs(self, keywords: str, location: str = "Remote", limit: int = 20) -> List[Dict]:
        """Search for jobs on LinkedIn"""
        if not self.page:
            await self.start_browser()
        
        try:
            jobs = []
            
            # Encode search parameters
            encoded_keywords = quote_plus(keywords)
            encoded_location = quote_plus(location)
            
            # Try different LinkedIn job URLs
            search_urls = [
                f"https://www.linkedin.com/jobs/search?keywords={encoded_keywords}&location={encoded_location}&f_TPR=r86400&f_JT=F",
                f"https://www.linkedin.com/jobs/search?keywords={encoded_keywords}&location={encoded_location}",
                f"https://www.linkedin.com/jobs/search?q={encoded_keywords}&l={encoded_location}"
            ]
            
            for i, search_url in enumerate(search_urls):
                try:
                    print(f"Attempt {i+1}: Searching with URL: {search_url}")
                    
                    # Navigate with longer timeout and different wait strategy
                    await self.page.goto(search_url, timeout=60000, wait_until='domcontentloaded')
                    await self.random_delay(3, 5)
                    
                    # Wait for page to load completely
                    await self.page.wait_for_load_state('networkidle', timeout=30000)
                    
                    # Check if we got blocked or redirected to login
                    current_url = self.page.url
                    if 'login' in current_url or 'authwall' in current_url:
                        print(f"Redirected to login page: {current_url}")
                        continue
                    
                    # Try to find job listings with different selectors
                    jobs = await self.extract_jobs_from_page(limit)
                    
                    if jobs:
                        print(f"Successfully found {len(jobs)} jobs!")
                        return jobs
                    
                    print(f"No jobs found with URL {i+1}, trying next...")
                    
                except Exception as e:
                    print(f"Error with URL {i+1}: {str(e)}")
                    continue
            
            print("All URLs failed, LinkedIn may be blocking requests")
            return []
            
        except Exception as e:
            print(f"Error searching jobs: {str(e)}")
            return []

    async def extract_jobs_from_page(self, limit: int = 20) -> List[Dict]:
        """Extract jobs from current page"""
        try:
            jobs = []
            
            # Wait for job listings to load
            await self.random_delay(2, 4)
            
            # Try different selectors for job listings container
            listing_selectors = [
                '.jobs-search__results-list',
                'ul[data-finite-scroll-hotkey]',
                '.scaffold-layout__list-container',
                '.jobs-search-results__list'
            ]
            
            for selector in listing_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    break
                except:
                    continue
            
            # Get job listing elements - try multiple selectors
            job_card_selectors = [
                '.job-search-card',
                '.jobs-search-results__list-item',
                '.base-search-card',
                'li[data-occludable-job-id]',
                '.scaffold-layout__list-container li',
                '.jobs-search-results__list li'
            ]
            
            job_cards = []
            for selector in job_card_selectors:
                job_cards = await self.page.query_selector_all(selector)
                if job_cards:
                    print(f"Found {len(job_cards)} job cards using selector: {selector}")
                    break
            
            if not job_cards:
                print("No job cards found with any selector")
                # Save page content for debugging
                page_content = await self.page.content()
                with open('linkedin_debug.html', 'w', encoding='utf-8') as f:
                    f.write(page_content)
                print("Page content saved to linkedin_debug.html for analysis")
                return []
            
            # Extract job data
            for i, card in enumerate(job_cards[:limit]):
                try:
                    job_data = await self.extract_job_data(card)
                    if job_data:
                        jobs.append(job_data)
                        print(f"Extracted job {i+1}: {job_data.get('title', 'Unknown')}")
                    
                    # Random delay between extractions
                    await self.random_delay(0.5, 1.5)
                    
                except Exception as e:
                    print(f"Error extracting job {i+1}: {str(e)}")
                    continue
            
            return jobs
            
        except Exception as e:
            print(f"Error extracting jobs from page: {str(e)}")
            return []

    async def extract_job_data(self, card_element) -> Optional[Dict]:
        """Extract job information from a job card element"""
        try:
            job_data = {}
            
            # Extract job title - try multiple selectors
            try:
                title_selectors = [
                    'h3 a span[title]',
                    '.job-search-card__title a',
                    'h3.base-search-card__title a',
                    'h3 a',
                    '.base-search-card__title a',
                    '.job-card-container__link'
                ]
                
                title_element = None
                for selector in title_selectors:
                    title_element = await card_element.query_selector(selector)
                    if title_element:
                        break
                
                if title_element:
                    # Get title text
                    title_span = await title_element.query_selector('span[title]')
                    if title_span:
                        job_data['title'] = await title_span.get_attribute('title')
                    else:
                        job_data['title'] = (await title_element.text_content()).strip()
                    
                    # Get URL
                    job_data['url'] = await title_element.get_attribute('href')
                    if job_data['url'] and not job_data['url'].startswith('http'):
                        job_data['url'] = f"https://www.linkedin.com{job_data['url']}"
            except Exception as e:
                print(f"Error extracting title: {e}")
            
            # Extract company name - try multiple selectors
            try:
                company_selectors = [
                    'h4 a span[title]',
                    '.job-search-card__subtitle-link',
                    'h4.base-search-card__subtitle a',
                    'h4 a',
                    '.base-search-card__subtitle a'
                ]
                
                company_element = None
                for selector in company_selectors:
                    company_element = await card_element.query_selector(selector)
                    if company_element:
                        break
                
                if company_element:
                    company_span = await company_element.query_selector('span[title]')
                    if company_span:
                        job_data['company'] = await company_span.get_attribute('title')
                    else:
                        job_data['company'] = (await company_element.text_content()).strip()
            except Exception as e:
                print(f"Error extracting company: {e}")
            
            # Extract location - try multiple selectors
            try:
                location_selectors = [
                    '.job-search-card__location',
                    '.base-search-card__metadata span',
                    'span.job-search-card__location',
                    'span[data-test-id="job-location"]'
                ]
                
                location_element = None
                for selector in location_selectors:
                    location_element = await card_element.query_selector(selector)
                    if location_element:
                        break
                
                if location_element:
                    job_data['location'] = (await location_element.text_content()).strip()
            except Exception as e:
                print(f"Error extracting location: {e}")
            
            # Extract posted time
            try:
                time_selectors = [
                    'time',
                    '.job-search-card__listdate',
                    'span[data-test-id="job-posted-date"]'
                ]
                
                time_element = None
                for selector in time_selectors:
                    time_element = await card_element.query_selector(selector)
                    if time_element:
                        break
                
                if time_element:
                    job_data['posted_date'] = (await time_element.text_content()).strip()
            except Exception as e:
                print(f"Error extracting posted date: {e}")
            
            # Extract salary if available
            try:
                salary_selectors = [
                    '.job-search-card__salary-info',
                    'span[data-test-id="job-salary"]',
                    '.base-search-card__metadata .job-search-card__salary-info'
                ]
                
                salary_element = None
                for selector in salary_selectors:
                    salary_element = await card_element.query_selector(selector)
                    if salary_element:
                        break
                
                if salary_element:
                    job_data['salary'] = (await salary_element.text_content()).strip()
            except Exception as e:
                print(f"Error extracting salary: {e}")
            
            # Extract job description preview
            try:
                desc_selectors = [
                    '.job-search-card__snippet',
                    '.base-search-card__snippet',
                    'p[data-test-id="job-snippet"]'
                ]
                
                desc_element = None
                for selector in desc_selectors:
                    desc_element = await card_element.query_selector(selector)
                    if desc_element:
                        break
                
                if desc_element:
                    job_data['description'] = (await desc_element.text_content()).strip()
            except Exception as e:
                print(f"Error extracting description: {e}")
            
            # Add metadata
            job_data['source'] = 'linkedin'
            job_data['scraped_at'] = datetime.utcnow().isoformat()
            
            # Debug: Print what we extracted
            if job_data.get('title') or job_data.get('company'):
                print(f"🔍 Extracted: {job_data.get('title', 'No title')} at {job_data.get('company', 'No company')}")
            else:
                # Try to get any text content for debugging
                all_text = await card_element.text_content()
                print(f"⚠️ No title/company found. Card text preview: {all_text[:100]}...")
                
                # Try to find all links in the card
                all_links = await card_element.query_selector_all('a')
                for i, link in enumerate(all_links[:3]):  # Check first 3 links
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    print(f"   Link {i+1}: {text[:50]} -> {href}")
            
            # Only return if we have essential fields
            if job_data.get('title') and job_data.get('company'):
                return job_data
            elif job_data.get('title'):  # At least we have a title
                job_data['company'] = 'Company not specified'
                return job_data
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error extracting job data: {str(e)}")
            return None

    async def get_job_details(self, job_url: str) -> Optional[Dict]:
        """Get detailed job information from job URL"""
        try:
            await self.page.goto(job_url, wait_until='networkidle')
            await self.random_delay(2, 3)
            
            details = {}
            
            # Extract full job description
            try:
                desc_element = await self.page.query_selector('.show-more-less-html__markup, .jobs-description-content__text')
                if desc_element:
                    details['full_description'] = await desc_element.text_content()
            except:
                pass
            
            # Extract job criteria (employment type, experience level, etc.)
            try:
                criteria_elements = await self.page.query_selector_all('.jobs-unified-top-card__job-insight')
                criteria = []
                for element in criteria_elements:
                    text = await element.text_content()
                    if text:
                        criteria.append(text.strip())
                details['job_criteria'] = criteria
            except:
                pass
            
            # Extract skills
            try:
                skills_elements = await self.page.query_selector_all('.jobs-unified-top-card__skills-list li')
                skills = []
                for element in skills_elements:
                    skill = await element.text_content()
                    if skill:
                        skills.append(skill.strip())
                details['required_skills'] = skills
            except:
                pass
            
            return details
            
        except Exception as e:
            print(f"⚠️ Error getting job details: {str(e)}")
            return {}

    async def random_delay(self, min_seconds: float = 1, max_seconds: float = 3):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    async def scroll_page(self, scrolls: int = 3):
        """Scroll page to load more content"""
        for i in range(scrolls):
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await self.random_delay(1, 2)

    async def close_browser(self):
        """Clean up browser resources"""
        try:
            if self.browser:
                await self.browser.close()
                print("✅ Browser closed successfully")
        except Exception as e:
            print(f"⚠️ Error closing browser: {str(e)}")

    async def __aenter__(self):
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_browser()

# Usage example and testing
async def test_linkedin_scraper():
    """Test the LinkedIn scraper"""
    scraper = LinkedInJobScraper()
    
    try:
        await scraper.start_browser(headless=False)  # Set to True for production
        
        jobs = await scraper.search_jobs(
            keywords="python developer",
            location="Remote", 
            limit=10
        )
        
        print(f"\n🎯 Final Results: {len(jobs)} jobs found")
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Posted: {job.get('posted_date', 'N/A')}")
            print(f"   URL: {job.get('url', 'N/A')[:80]}...")
        
        return jobs
        
    finally:
        await scraper.close_browser()

if __name__ == "__main__":
    # Run test
    asyncio.run(test_linkedin_scraper())
