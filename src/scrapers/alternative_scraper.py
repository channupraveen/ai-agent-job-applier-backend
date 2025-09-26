"""
Simple Job Generator
No external dependencies - creates realistic mock jobs
"""

import asyncio
import random
from typing import List, Dict
from datetime import datetime

class SimpleJobGenerator:
    """
    Generates realistic mock jobs without external API dependencies
    """
    
    def __init__(self):
        pass
    
    async def search_jobs(self, keywords: str, location: str = "Remote", limit: int = 20) -> List[Dict]:
        """Generate realistic mock jobs"""
        try:
            await asyncio.sleep(1)  # Simulate API delay
            
            companies = [
                "Microsoft", "Google", "Amazon", "Meta", "Apple", "Netflix", "Tesla",
                "Spotify", "Airbnb", "Uber", "Twitter", "LinkedIn", "Salesforce",
                "Adobe", "Intel", "NVIDIA", "IBM", "Oracle", "Cisco", "VMware",
                "Stripe", "PayPal", "Square", "Zoom", "Slack", "Dropbox", "Atlassian",
                "GitHub", "GitLab", "MongoDB", "Redis Labs", "Elastic", "Docker"
            ]
            
            job_levels = [
                "Senior", "Lead", "Staff", "Principal", "", "Junior", "Mid-Level"
            ]
            
            positions = [
                f"{keywords} Developer",
                f"{keywords} Engineer", 
                f"Software Engineer - {keywords}",
                f"Backend Developer ({keywords})",
                f"Full Stack Developer",
                f"{keywords} Specialist",
                f"Software Development Engineer",
                f"{keywords} Architect"
            ]
            
            locations = [
                "Remote", "San Francisco, CA", "New York, NY", "Seattle, WA",
                "Austin, TX", "Boston, MA", "Los Angeles, CA", "Chicago, IL",
                "Denver, CO", "Atlanta, GA", "Remote (US)", "Remote (Global)"
            ]
            
            salaries = [
                "$120,000 - $180,000", "$100,000 - $160,000", "$140,000 - $200,000",
                "$90,000 - $140,000", "$110,000 - $170,000", "$130,000 - $190,000",
                "$80,000 - $130,000", "$150,000 - $220,000", "$95,000 - $145,000"
            ]
            
            descriptions = [
                f"We are seeking an experienced {keywords} professional to join our team. You will work on cutting-edge projects and collaborate with top talent in the industry.",
                f"Join our dynamic team as a {keywords} expert. You'll be responsible for developing scalable solutions and mentoring junior developers.",
                f"Exciting opportunity for a {keywords} specialist to work on innovative products used by millions of users worldwide.",
                f"We're looking for a passionate {keywords} developer to help us build the next generation of our platform.",
                f"Great opportunity to work with {keywords} technologies in a fast-paced, collaborative environment."
            ]
            
            posted_dates = [
                "1 day ago", "2 days ago", "3 days ago", "1 week ago", "2 weeks ago"
            ]
            
            jobs = []
            used_combinations = set()
            
            for i in range(min(limit, 25)):
                # Avoid duplicate company-position combinations
                attempts = 0
                while attempts < 10:
                    company = random.choice(companies)
                    job_level = random.choice(job_levels)
                    position = random.choice(positions)
                    
                    title = f"{job_level} {position}".strip() if job_level else position
                    combo = (company.lower(), title.lower())
                    
                    if combo not in used_combinations:
                        used_combinations.add(combo)
                        break
                    attempts += 1
                
                job = {
                    'title': title,
                    'company': company,
                    'location': random.choice(locations) if location == "Remote" else location,
                    'url': f"https://www.linkedin.com/jobs/view/{random.randint(3000000000, 3999999999)}",
                    'description': random.choice(descriptions),
                    'requirements': f"{keywords}, Problem-solving, Team collaboration, Communication skills, Agile methodology",
                    'salary': random.choice(salaries),
                    'posted_date': random.choice(posted_dates),
                    'job_type': 'full-time',
                    'source': 'linkedin_realistic',
                    'scraped_at': datetime.utcnow().isoformat()
                }
                jobs.append(job)
            
            print(f"Generated {len(jobs)} realistic job listings")
            return jobs
            
        except Exception as e:
            print(f"Error generating jobs: {str(e)}")
            return []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Test function
async def test_simple_generator():
    """Test the simple job generator"""
    async with SimpleJobGenerator() as generator:
        jobs = await generator.search_jobs("python developer", "Remote", 10)
        
        print(f"\nFound {len(jobs)} jobs:")
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Salary: {job.get('salary', 'N/A')}")
            print(f"   Posted: {job.get('posted_date', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_simple_generator())
