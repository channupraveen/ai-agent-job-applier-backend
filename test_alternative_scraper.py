"""
Test Alternative Job Scraper
Run this to test the fallback scraper when LinkedIn fails
"""

import sys
import os
import asyncio

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.alternative_scraper import SimpleJobGenerator

async def test_alternative():
    print("Testing Simple Job Generator...")
    
    try:
        async with SimpleJobGenerator() as generator:
            jobs = await generator.search_jobs(
                keywords="python developer",
                location="Remote",
                limit=10
            )
            
            print(f"\\nSuccessfully found {len(jobs)} jobs!")
            
            for i, job in enumerate(jobs, 1):
                print(f"\\n--- Job {i} ---")
                print(f"Title: {job.get('title', 'N/A')}")
                print(f"Company: {job.get('company', 'N/A')}")
                print(f"Location: {job.get('location', 'N/A')}")
                print(f"Salary: {job.get('salary', 'N/A')}")
                print(f"Source: {job.get('source', 'N/A')}")
            
            return len(jobs) > 0
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_alternative())
    
    if success:
        print("\\nAlternative scraper working perfectly!")
        print("This will provide jobs when LinkedIn blocks scraping.")
    else:
        print("\\nAlternative scraper needs debugging")
