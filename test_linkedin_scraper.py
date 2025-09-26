"""
Test LinkedIn Scraper
Run this to test if LinkedIn scraping is working
"""

import sys
import os
import asyncio

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.linkedin_scraper import LinkedInJobScraper

async def test_scraper():
    print("🚀 Testing LinkedIn Job Scraper...")
    
    scraper = LinkedInJobScraper()
    
    try:
        # Test scraping with visible browser for debugging
        await scraper.start_browser(headless=False)
        
        jobs = await scraper.search_jobs(
            keywords="python developer",
            location="Remote",
            limit=5
        )
        
        print(f"\n✅ Successfully scraped {len(jobs)} jobs!")
        
        for i, job in enumerate(jobs, 1):
            print(f"\n--- Job {i} ---")
            print(f"Title: {job.get('title', 'N/A')}")
            print(f"Company: {job.get('company', 'N/A')}")
            print(f"Location: {job.get('location', 'N/A')}")
            print(f"Posted: {job.get('posted_date', 'N/A')}")
            print(f"URL: {job.get('url', 'N/A')}")
            
        return len(jobs) > 0
        
    except Exception as e:
        print(f"❌ Scraping failed: {str(e)}")
        return False
    
    finally:
        # Keep browser open for 10 seconds to see what happened
        print("\n🔍 Keeping browser open for 10 seconds for inspection...")
        await asyncio.sleep(10)
        await scraper.close_browser()

if __name__ == "__main__":
    success = asyncio.run(test_scraper())
    
    if success:
        print("\n🎯 LinkedIn scraper is working!")
    else:
        print("\n⚠️  LinkedIn scraper needs debugging")
        print("Make sure to install: pip install playwright")
        print("Then run: playwright install chromium")
