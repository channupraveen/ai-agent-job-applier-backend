"""
Test file for Naukri.com Web Scraper
Run this to test your Naukri scraper functionality
"""

import sys
import os
import asyncio
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from scrapers.naukri_scraper import NaukriJobScraper
    print("✅ Successfully imported Naukri scraper")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you have BeautifulSoup4 installed: pip install beautifulsoup4")
    sys.exit(1)


async def test_naukri_scraper():
    """Test the Naukri web scraper"""
    print("\n" + "="*60)
    print("🧪 TESTING: Naukri.com Web Scraper")
    print("="*60)
    
    test_keywords = "python developer"
    test_location = "Delhi"
    test_limit = 10
    
    print(f"Search Parameters:")
    print(f"  Keywords: {test_keywords}")
    print(f"  Location: {test_location}")
    print(f"  Limit: {test_limit}")
    print(f"  Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    try:
        async with NaukriJobScraper() as scraper:
            print("🔍 Searching Naukri.com...")
            jobs = await scraper.search_jobs(test_keywords, test_location, test_limit)
            
            print(f"\n📊 RESULTS:")
            print(f"  Jobs found: {len(jobs)}")
            print(f"  Completed at: {datetime.now().strftime('%H:%M:%S')}")
            print()
            
            if jobs:
                print("🎯 TOP JOBS FOUND:")
                print("-" * 80)
                for i, job in enumerate(jobs[:5], 1):
                    print(f"\n{i}. {job.get('title', 'N/A')}")
                    print(f"   Company: {job.get('company', 'N/A')}")
                    print(f"   Location: {job.get('location', 'N/A')}")
                    print(f"   Salary: {job.get('salary', 'Not disclosed')}")
                    print(f"   Posted: {job.get('posted_date', 'N/A')}")
                    print(f"   URL: {job.get('url', 'N/A')[:80]}...")
                    print(f"   Description: {job.get('description', 'N/A')[:100]}...")
                
                print("\n" + "="*60)
                print("✅ SUCCESS: Naukri scraper is working!")
                print(f"📈 Found {len(jobs)} jobs in total")
                
                # Test data quality
                valid_jobs = [j for j in jobs if j.get('title') and j.get('company') and j.get('url')]
                print(f"📋 Data Quality: {len(valid_jobs)}/{len(jobs)} jobs have complete data")
                
            else:
                print("❌ No jobs found. Possible reasons:")
                print("   - Naukri may have anti-bot protection")
                print("   - Network connectivity issues")
                print("   - HTML structure may have changed")
                print("   - Search terms too specific")
                
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Install required packages: pip install requests beautifulsoup4")
        print("3. Try different search terms")
        print("4. Naukri may be blocking automated requests")


async def test_multiple_searches():
    """Test multiple search scenarios"""
    print("\n" + "="*60)
    print("🧪 TESTING: Multiple Search Scenarios")
    print("="*60)
    
    test_cases = [
        ("python", "Mumbai", 5),
        ("java developer", "Bangalore", 5),
        ("data scientist", "Hyderabad", 5)
    ]
    
    async with NaukriJobScraper() as scraper:
        for keywords, location, limit in test_cases:
            print(f"\n🔍 Testing: {keywords} in {location}")
            try:
                jobs = await scraper.search_jobs(keywords, location, limit)
                print(f"   ✅ Found {len(jobs)} jobs")
                
                # Wait between requests
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")


async def main():
    """Run all tests"""
    print("🚀 Starting Naukri Scraper Tests")
    print("=" * 60)
    
    # Basic test
    await test_naukri_scraper()
    
    # Ask user if they want to run more tests
    print("\n" + "?"*60)
    response = input("Run additional tests? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        await test_multiple_searches()
    
    print("\n🏁 Testing completed!")
    print("If scraper is not working, focus on API-based approaches instead.")


if __name__ == "__main__":
    # Check dependencies
    try:
        import requests
        import bs4
        print("✅ All required packages found")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Install with: pip install requests beautifulsoup4")
        sys.exit(1)
    
    # Run tests
    asyncio.run(main())
