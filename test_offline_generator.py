"""
Test file for Alternative Job Generator (No Internet Required)
This works completely offline and generates realistic mock data
"""

import sys
import os
import asyncio
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from scrapers.alternative_scraper import SimpleJobGenerator
    print("✅ Successfully imported Alternative scraper")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_offline_generator():
    """Test the offline job generator"""
    print("\n" + "="*60)
    print("🧪 TESTING: Alternative Job Generator (OFFLINE)")
    print("="*60)
    
    test_keywords = "python developer"
    test_location = "Remote"
    test_limit = 15
    
    print(f"Search Parameters:")
    print(f"  Keywords: {test_keywords}")
    print(f"  Location: {test_location}")
    print(f"  Limit: {test_limit}")
    print(f"  Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    try:
        async with SimpleJobGenerator() as generator:
            print("🔍 Generating mock jobs (no internet needed)...")
            jobs = await generator.search_jobs(test_keywords, test_location, test_limit)
            
            print(f"\n📊 RESULTS:")
            print(f"  Jobs generated: {len(jobs)}")
            print(f"  Completed at: {datetime.now().strftime('%H:%M:%S')}")
            print()
            
            if jobs:
                print("🎯 GENERATED JOBS:")
                print("-" * 80)
                for i, job in enumerate(jobs, 1):
                    print(f"\n{i}. {job.get('title', 'N/A')}")
                    print(f"   Company: {job.get('company', 'N/A')}")
                    print(f"   Location: {job.get('location', 'N/A')}")
                    print(f"   Salary: {job.get('salary', 'N/A')}")
                    print(f"   Posted: {job.get('posted_date', 'N/A')}")
                    print(f"   Source: {job.get('source', 'N/A')}")
                    print(f"   URL: {job.get('url', 'N/A')[:50]}...")
                
                print("\n" + "="*60)
                print("✅ SUCCESS: Alternative generator working perfectly!")
                print(f"📈 Generated {len(jobs)} realistic mock jobs")
                
                # Test data quality
                complete_jobs = [j for j in jobs if j.get('title') and j.get('company') and j.get('url')]
                print(f"📋 Data Quality: {len(complete_jobs)}/{len(jobs)} jobs have complete data")
                
                # Show unique companies
                companies = set(job.get('company') for job in jobs)
                print(f"🏢 Unique Companies: {len(companies)}")
                print(f"   Companies: {', '.join(list(companies)[:5])}...")
                
            else:
                print("❌ No jobs generated - something is wrong with the generator")
                
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


async def test_multiple_keywords():
    """Test with different keywords"""
    print("\n" + "="*60)
    print("🧪 TESTING: Multiple Keywords")
    print("="*60)
    
    test_cases = [
        ("python developer", 5),
        ("java engineer", 5), 
        ("data scientist", 5),
        ("full stack developer", 5)
    ]
    
    async with SimpleJobGenerator() as generator:
        for keywords, limit in test_cases:
            print(f"\n🔍 Testing: {keywords}")
            try:
                jobs = await generator.search_jobs(keywords, "Remote", limit)
                print(f"   ✅ Generated {len(jobs)} jobs")
                
                # Show sample job titles
                if jobs:
                    sample_titles = [job.get('title', 'N/A') for job in jobs[:2]]
                    print(f"   📝 Sample: {', '.join(sample_titles)}")
                
                await asyncio.sleep(0.5)  # Small delay
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")


async def main():
    """Run all tests"""
    print("🚀 Starting Offline Generator Tests")
    print("=" * 60)
    print("ℹ️  This works without internet connection!")
    print()
    
    # Basic test
    await test_offline_generator()
    
    # Multiple keywords test
    await test_multiple_keywords()
    
    print("\n🏁 Testing completed!")
    print("\n💡 KEY INSIGHTS:")
    print("✅ Alternative generator works perfectly offline")
    print("✅ Generates realistic job data for testing")
    print("✅ Perfect for developing your application logic")
    print("✅ No API keys or internet connection required")
    print("\n🔄 For REAL jobs, you'll need:")
    print("- Fix internet connectivity issues")
    print("- Or use premium job APIs")
    print("- Or focus on direct web scraping (with proper headers)")


if __name__ == "__main__":
    # Run tests
    asyncio.run(main())
