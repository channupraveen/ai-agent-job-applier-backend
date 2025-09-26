"""
Test script to verify Indian job scrapers are working
Run with: python test_indian_scrapers.py
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_scrapers():
    print("🔍 Testing Indian Job Scrapers...")
    print("=" * 50)
    
    # Test Naukri Scraper
    print("\n1. Testing Naukri.com scraper...")
    try:
        from src.scrapers.naukri_scraper import NaukriJobScraper
        async with NaukriJobScraper() as scraper:
            jobs = await scraper.search_jobs("python developer", "Delhi", 5)
            print(f"✅ Naukri: Found {len(jobs)} jobs")
            if jobs:
                print(f"   Sample: {jobs[0].get('title')} at {jobs[0].get('company')}")
    except Exception as e:
        print(f"❌ Naukri failed: {str(e)}")
    
    # Test Indeed RSS
    print("\n2. Testing Indeed India RSS...")
    try:
        from src.scrapers.indeed_india_rss import IndeedIndiaRSSFetcher
        async with IndeedIndiaRSSFetcher() as fetcher:
            jobs = await fetcher.search_jobs("python developer", "Delhi", 5)
            print(f"✅ Indeed RSS: Found {len(jobs)} jobs")
            if jobs:
                print(f"   Sample: {jobs[0].get('title')} at {jobs[0].get('company')}")
    except Exception as e:
        print(f"❌ Indeed RSS failed: {str(e)}")
    
    # Test TimesJobs RSS
    print("\n3. Testing TimesJobs RSS...")
    try:
        from src.scrapers.timesjobs_rss import TimesJobsRSSFetcher
        async with TimesJobsRSSFetcher() as fetcher:
            jobs = await fetcher.search_jobs("python developer", "Delhi", 5)
            print(f"✅ TimesJobs: Found {len(jobs)} jobs")
            if jobs:
                print(f"   Sample: {jobs[0].get('title')} at {jobs[0].get('company')}")
    except Exception as e:
        print(f"❌ TimesJobs failed: {str(e)}")
    
    # Test Aggregator
    print("\n4. Testing Job Aggregator...")
    try:
        from src.scrapers.indian_job_aggregator import search_indian_jobs
        jobs = await search_indian_jobs("python developer", "Delhi", 10)
        print(f"✅ Aggregator: Found {len(jobs)} total jobs")
        if jobs:
            sources = set(job.get('aggregator_source', 'unknown') for job in jobs)
            print(f"   Sources used: {', '.join(sources)}")
            print(f"   Top job: {jobs[0].get('title')} at {jobs[0].get('company')} (Score: {jobs[0].get('relevance_score')})")
    except Exception as e:
        print(f"❌ Aggregator failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Complete!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements_scrapers.txt")
    print("2. Start your FastAPI server: uvicorn src.app:app --reload")
    print("3. Use the frontend to trigger job searches")
    print("4. Expected daily volume: 1000-3000 jobs from all sources combined")

if __name__ == "__main__":
    asyncio.run(test_scrapers())
