#!/usr/bin/env python3
"""
Test Google Jobs API Integration
Quick test to verify the API is working correctly
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from services.google_jobs_api import GoogleJobsAPIService

async def main():
    print("🧪 Testing Google Jobs API Integration...")
    print("=" * 50)
    
    # Initialize the service
    api_service = GoogleJobsAPIService()
    
    # Test 1: Connection Test
    print("\n1️⃣ Testing API Connection...")
    if api_service.test_api_connection():
        print("✅ API Connection: SUCCESS")
    else:
        print("❌ API Connection: FAILED")
        return
    
    # Test 2: Job Search Test
    print("\n2️⃣ Testing Job Search...")
    try:
        jobs = await api_service.search_jobs(
            keywords="python developer",
            location="Bangalore, India",
            limit=3
        )
        
        if jobs:
            print(f"✅ Job Search: SUCCESS - Found {len(jobs)} jobs")
            
            # Display sample jobs
            print("\n📋 Sample Jobs Found:")
            print("-" * 40)
            
            for i, job in enumerate(jobs, 1):
                print(f"\nJob {i}:")
                print(f"  📌 Title: {job['title']}")
                print(f"  🏢 Company: {job['company']}")
                print(f"  📍 Location: {job['location']}")
                print(f"  💰 Salary: {job.get('salary', 'Not specified')}")
                print(f"  🔗 URL: {job['url'][:80]}...")
                print(f"  📅 Posted: {job.get('posted_date', 'Not specified')}")
                
        else:
            print("⚠️ Job Search: No jobs found")
            
    except Exception as e:
        print(f"❌ Job Search: FAILED - {str(e)}")
        return
    
    # Test 3: Search with Filters
    print("\n3️⃣ Testing Search with Remote Filter...")
    try:
        remote_jobs = await api_service.search_jobs(
            keywords="software engineer",
            location="India",
            limit=2,
            work_from_home=True
        )
        
        if remote_jobs:
            print(f"✅ Remote Job Search: SUCCESS - Found {len(remote_jobs)} remote jobs")
        else:
            print("⚠️ Remote Job Search: No remote jobs found")
            
    except Exception as e:
        print(f"❌ Remote Job Search: FAILED - {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Google Jobs API Integration Test Complete!")
    print("💡 Next steps:")
    print("   1. Run migrations: python run_migrations.py")
    print("   2. Start backend server")
    print("   3. Test from frontend API Integration tab")

if __name__ == "__main__":
    asyncio.run(main())
