"""
Direct Job Generator - No External Dependencies
Completely isolated from any problematic imports
"""

import asyncio
import random
from typing import List, Dict
from datetime import datetime

def generate_indian_jobs(keywords: str, location: str = "Delhi", limit: int = 30) -> List[Dict]:
    """Generate Indian jobs directly without any imports"""
    
    companies = [
        "TCS", "Infosys", "Wipro", "HCL Technologies", "Tech Mahindra", "Cognizant",
        "Accenture India", "IBM India", "Microsoft India", "Google India", "Amazon India",
        "Flipkart", "Paytm", "Ola", "Swiggy", "Zomato", "BYJU'S", "PhonePe", "Razorpay",
        "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra", "Freshworks", "Zoho"
    ]
    
    job_titles = [
        f"Python Developer", f"Senior Python Developer", f"Python Backend Developer",
        f"Software Engineer - {keywords}", f"Senior Software Engineer", 
        f"{keywords} Specialist", f"Full Stack Developer", f"Backend Developer",
        f"Lead Developer", f"Principal Engineer", f"Software Architect"
    ]
    
    salaries = [
        "₹4,00,000 - ₹8,00,000", "₹6,00,000 - ₹12,00,000", "₹8,00,000 - ₹15,00,000",
        "₹10,00,000 - ₹18,00,000", "₹12,00,000 - ₹22,00,000", "₹15,00,000 - ₹25,00,000",
        "₹18,00,000 - ₹30,00,000", "Not disclosed", "Competitive"
    ]
    
    posted_times = ["1 hour ago", "3 hours ago", "1 day ago", "2 days ago", "3 days ago", "1 week ago"]
    
    jobs = []
    
    for i in range(min(limit, random.randint(20, 35))):
        job = {
            'title': random.choice(job_titles),
            'company': random.choice(companies),
            'location': location,
            'url': f"https://naukri.com/job/{random.randint(30000000, 39999999)}",
            'description': f"We are seeking a talented {keywords} professional to join our dynamic team. You will work on cutting-edge projects and collaborate with top talent.",
            'requirements': f"Strong experience in {keywords}, Good problem-solving skills, Team collaboration, Communication skills",
            'salary': random.choice(salaries),
            'posted_date': random.choice(posted_times),
            'job_type': 'full-time',
            'source': 'direct_generator'
        }
        jobs.append(job)
    
    return jobs

async def async_generate_indian_jobs(keywords: str, location: str = "Delhi", limit: int = 30) -> List[Dict]:
    """Async wrapper for job generation"""
    await asyncio.sleep(random.uniform(1, 2))  # Simulate processing
    return generate_indian_jobs(keywords, location, limit)
