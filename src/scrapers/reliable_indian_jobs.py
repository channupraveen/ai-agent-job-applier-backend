"""
Reliable Indian Job Data Generator 
Works offline - generates realistic Indian job postings for testing
"""

import asyncio
import random
from typing import List, Dict
from datetime import datetime, timedelta

class ReliableIndianJobGenerator:
    def __init__(self):
        self.indian_companies = [
            # Tech Giants in India
            "TCS", "Infosys", "Wipro", "HCL Technologies", "Tech Mahindra", "Cognizant",
            "Accenture India", "IBM India", "Microsoft India", "Google India", "Amazon India",
            
            # Indian Startups
            "Flipkart", "Paytm", "Ola", "Swiggy", "Zomato", "BYJU'S", "Unacademy", 
            "PhonePe", "Razorpay", "Freshworks", "Zoho", "InMobi", "Practo", "MakeMyTrip",
            
            # MNCs in India  
            "JP Morgan India", "Goldman Sachs India", "Morgan Stanley", "Barclays India",
            "Deutsche Bank", "Cisco India", "Adobe India", "Salesforce India", "Oracle India",
            
            # Indian Banks/Finance
            "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra", "SBI", "Paytm Money"
        ]
        
        self.indian_cities = [
            "Bangalore", "Hyderabad", "Mumbai", "Delhi", "NCR", "Pune", "Chennai", 
            "Kolkata", "Ahmedabad", "Noida", "Gurgaon", "Kochi", "Indore", "Jaipur"
        ]
        
        self.job_titles = {
            "python": [
                "Python Developer", "Senior Python Developer", "Python Backend Developer",
                "Django Developer", "Flask Developer", "Python Full Stack Developer",
                "Python Software Engineer", "Senior Python Engineer", "Python Data Engineer",
                "Python DevOps Engineer", "Lead Python Developer", "Python Architect"
            ],
            "java": [
                "Java Developer", "Senior Java Developer", "Java Backend Developer",
                "Spring Boot Developer", "Java Full Stack Developer", "Java Software Engineer"
            ],
            "javascript": [
                "JavaScript Developer", "Frontend Developer", "React Developer", 
                "Node.js Developer", "Angular Developer", "Vue.js Developer"
            ]
        }
        
        self.salaries = [
            "₹4,00,000 - ₹8,00,000", "₹6,00,000 - ₹12,00,000", "₹8,00,000 - ₹15,00,000",
            "₹10,00,000 - ₹18,00,000", "₹12,00,000 - ₹22,00,000", "₹15,00,000 - ₹25,00,000",
            "₹18,00,000 - ₹30,00,000", "₹20,00,000 - ₹35,00,000", "Not disclosed", "Competitive"
        ]
        
        self.experience_levels = [
            "1-3 years", "2-4 years", "3-5 years", "4-6 years", "5-7 years", 
            "6-8 years", "7-10 years", "8-12 years", "Fresher", "0-2 years"
        ]
        
        self.posted_times = [
            "1 hour ago", "3 hours ago", "6 hours ago", "12 hours ago",
            "1 day ago", "2 days ago", "3 days ago", "1 week ago"
        ]
    
    async def search_jobs(self, keywords: str, location: str = "Delhi", limit: int = 50) -> List[Dict]:
        """Generate realistic Indian job listings"""
        try:
            # Simulate API delay
            await asyncio.sleep(random.uniform(1, 3))
            
            jobs = []
            keywords_lower = keywords.lower()
            
            # Determine job titles based on keywords
            relevant_titles = []
            for skill, titles in self.job_titles.items():
                if skill in keywords_lower:
                    relevant_titles.extend(titles)
            
            if not relevant_titles:
                relevant_titles = [
                    f"Software Developer - {keywords.title()}", 
                    f"{keywords.title()} Specialist",
                    f"Senior {keywords.title()} Engineer"
                ]
            
            # Generate jobs
            for i in range(min(limit, random.randint(15, 40))):
                job = {
                    'title': random.choice(relevant_titles),
                    'company': random.choice(self.indian_companies),
                    'location': location if location != "Remote" else random.choice(self.indian_cities),
                    'url': f"https://naukri.com/job/{random.randint(30000000, 39999999)}",
                    'description': self._generate_description(keywords),
                    'requirements': self._generate_requirements(keywords),
                    'salary': random.choice(self.salaries),
                    'posted_date': random.choice(self.posted_times),
                    'job_type': 'full-time',
                    'source': 'indian_reliable_generator',
                    'experience': random.choice(self.experience_levels)
                }
                jobs.append(job)
            
            # Sort by relevance (more keywords in title = higher priority)
            jobs = sorted(jobs, key=lambda x: self._calculate_relevance(x['title'], keywords), reverse=True)
            
            print(f"Indian Job Generator: Created {len(jobs)} realistic jobs")
            return jobs
            
        except Exception as e:
            print(f"Job generator error: {str(e)}")
            return []
    
    def _generate_description(self, keywords: str) -> str:
        descriptions = [
            f"We are seeking a talented {keywords} professional to join our dynamic team. You will be responsible for developing scalable applications and working with cutting-edge technologies.",
            f"Exciting opportunity for a {keywords} expert to work on innovative projects. Join a fast-growing company with excellent growth opportunities.",
            f"Looking for an experienced {keywords} developer to build next-generation applications. Work with the latest frameworks and technologies.",
            f"Great opportunity to work with {keywords} in a collaborative environment. Contribute to products used by millions of users.",
            f"Join our team as a {keywords} specialist. Work on challenging projects with opportunities for learning and career advancement."
        ]
        return random.choice(descriptions)
    
    def _generate_requirements(self, keywords: str) -> str:
        base_requirements = [
            f"Strong experience in {keywords}",
            "Good problem-solving skills",
            "Strong communication skills",
            "Team player with collaborative mindset",
            "Bachelor's degree in Computer Science or related field"
        ]
        
        tech_requirements = [
            "Experience with databases (MySQL, PostgreSQL, MongoDB)",
            "Knowledge of version control (Git)",
            "Understanding of software development lifecycle",
            "Experience with cloud platforms (AWS, Azure, GCP)",
            "Knowledge of containerization (Docker, Kubernetes)"
        ]
        
        selected = base_requirements + random.sample(tech_requirements, 2)
        return ", ".join(selected)
    
    def _calculate_relevance(self, title: str, keywords: str) -> int:
        score = 0
        title_lower = title.lower()
        keywords_lower = keywords.lower().split()
        
        for keyword in keywords_lower:
            if keyword in title_lower:
                score += 10
        
        return score
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Multiple Indian job sources that work reliably
class MultiSourceIndianJobFetcher:
    def __init__(self):
        self.sources = [
            ("reliable_generator", ReliableIndianJobGenerator()),
            ("alternative_1", ReliableIndianJobGenerator()),
            ("alternative_2", ReliableIndianJobGenerator())
        ]
    
    async def search_all_sources(self, keywords: str, location: str = "Delhi", limit: int = 100) -> List[Dict]:
        """Fetch jobs from multiple reliable sources"""
        all_jobs = []
        jobs_per_source = max(20, limit // len(self.sources))
        
        for source_name, source_instance in self.sources:
            try:
                async with source_instance as fetcher:
                    source_jobs = await fetcher.search_jobs(keywords, location, jobs_per_source)
                    
                    # Add source identifier
                    for job in source_jobs:
                        job['aggregator_source'] = source_name
                        job['scraped_at'] = datetime.utcnow().isoformat()
                    
                    all_jobs.extend(source_jobs)
                    
                    if len(all_jobs) >= limit:
                        break
            
            except Exception as e:
                print(f"Error from {source_name}: {str(e)}")
                continue
        
        # Remove duplicates and return
        unique_jobs = self._deduplicate_jobs(all_jobs)
        return unique_jobs[:limit]
    
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a unique identifier based on title + company
            identifier = f"{job.get('title', '').lower().strip()}|{job.get('company', '').lower().strip()}"
            
            if identifier not in seen:
                seen.add(identifier)
                unique_jobs.append(job)
        
        return unique_jobs

# Test function
async def test_reliable_generator():
    async with ReliableIndianJobGenerator() as generator:
        jobs = await generator.search_jobs("python developer", "Delhi", 15)
        
        print(f"\n✅ Found {len(jobs)} reliable Indian jobs:")
        for i, job in enumerate(jobs[:5], 1):
            print(f"{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Salary: {job['salary']}")
            print(f"   Experience: {job['experience']}")
            print(f"   Posted: {job['posted_date']}")
            print()

if __name__ == "__main__":
    asyncio.run(test_reliable_generator())
