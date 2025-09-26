"""
Multi-Source Indian Job Aggregator
Combines all Indian job sources for maximum coverage
"""

import asyncio
from typing import List, Dict
from datetime import datetime
import random

class IndianJobAggregator:
    def __init__(self):
        self.sources_available = []
        self._check_available_sources()
    
    def _check_available_sources(self):
        """Check which scrapers are available"""
        try:
            from .naukri_scraper import NaukriJobScraper
            self.sources_available.append(('naukri', NaukriJobScraper))
        except ImportError:
            pass
        
        try:
            from .indeed_india_rss import IndeedIndiaRSSFetcher, IndeedMultiLocationFetcher
            self.sources_available.append(('indeed_rss', IndeedIndiaRSSFetcher))
            self.sources_available.append(('indeed_multi', IndeedMultiLocationFetcher))
        except ImportError:
            pass
        
        try:
            from .timesjobs_rss import TimesJobsRSSFetcher
            self.sources_available.append(('timesjobs', TimesJobsRSSFetcher))
        except ImportError:
            pass
        
        print(f"Available job sources: {[name for name, _ in self.sources_available]}")
    
    async def search_all_sources(self, keywords: str, location: str = "Delhi", limit: int = 200) -> List[Dict]:
        """Search jobs from all available sources"""
        all_jobs = []
        jobs_per_source = max(20, limit // max(len(self.sources_available), 1))
        
        tasks = []
        
        for source_name, source_class in self.sources_available:
            task = self._search_single_source(source_name, source_class, keywords, location, jobs_per_source)
            tasks.append(task)
        
        # Run all sources concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            source_name = self.sources_available[i][0]
            
            if isinstance(result, Exception):
                print(f"Error from {source_name}: {str(result)}")
                continue
            
            if isinstance(result, list):
                print(f"{source_name} contributed {len(result)} jobs")
                all_jobs.extend(result)
        
        # Deduplicate and rank
        unique_jobs = self._deduplicate_jobs(all_jobs)
        ranked_jobs = self._rank_jobs(unique_jobs, keywords)
        
        print(f"Total unique jobs found: {len(unique_jobs)}")
        return ranked_jobs[:limit]
    
    async def _search_single_source(self, source_name: str, source_class, keywords: str, location: str, limit: int) -> List[Dict]:
        """Search jobs from a single source"""
        try:
            if source_name == 'indeed_multi':
                # Special handling for multi-location Indeed
                fetcher = source_class()
                jobs = await fetcher.search_jobs_multiple_cities(keywords, limit)
            else:
                async with source_class() as scraper:
                    jobs = await scraper.search_jobs(keywords, location, limit)
            
            # Add source identifier
            for job in jobs:
                job['aggregator_source'] = source_name
                job['scraped_at'] = datetime.utcnow().isoformat()
            
            return jobs
            
        except Exception as e:
            print(f"Error in {source_name}: {str(e)}")
            return []
    
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on URL and title+company"""
        unique_jobs = []
        seen_urls = set()
        seen_combinations = set()
        
        for job in jobs:
            url = job.get('url', '').strip()
            title = job.get('title', '').strip().lower()
            company = job.get('company', '').strip().lower()
            
            # Primary deduplication by URL
            if url and url in seen_urls:
                continue
            
            # Secondary deduplication by title+company
            combination = f"{title}||{company}"
            if combination in seen_combinations:
                continue
            
            if url:
                seen_urls.add(url)
            seen_combinations.add(combination)
            unique_jobs.append(job)
        
        return unique_jobs
    
    def _rank_jobs(self, jobs: List[Dict], keywords: str) -> List[Dict]:
        """Rank jobs by relevance"""
        keywords_lower = keywords.lower().split()
        
        for job in jobs:
            score = 0
            title = job.get('title', '').lower()
            description = job.get('description', '').lower()
            
            # Score by keyword matches in title (higher weight)
            for keyword in keywords_lower:
                if keyword in title:
                    score += 10
                if keyword in description:
                    score += 3
            
            # Bonus for recent posts
            posted = job.get('posted_date', '').lower()
            if any(term in posted for term in ['today', '1 day', 'yesterday']):
                score += 5
            elif any(term in posted for term in ['2 day', '3 day']):
                score += 3
            
            # Bonus for salary disclosed
            salary = job.get('salary', '').lower()
            if salary and salary != 'competitive salary' and salary != 'not disclosed':
                score += 2
            
            # Source reliability bonus
            source = job.get('aggregator_source', '')
            source_bonus = {
                'indeed_rss': 5,
                'indeed_multi': 4,
                'naukri': 4,
                'timesjobs': 3
            }
            score += source_bonus.get(source, 0)
            
            job['relevance_score'] = score
        
        # Sort by relevance score
        return sorted(jobs, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    async def get_source_stats(self) -> Dict:
        """Get statistics about available sources"""
        stats = {
            'available_sources': len(self.sources_available),
            'source_names': [name for name, _ in self.sources_available],
            'estimated_daily_jobs': {
                'naukri': '300-800 jobs/day',
                'indeed_rss': '500-1200 jobs/day', 
                'indeed_multi': '800-1500 jobs/day',
                'timesjobs': '200-600 jobs/day'
            },
            'total_estimated': '1500-3000 jobs/day'
        }
        return stats

# Convenience function for external use
async def search_indian_jobs(keywords: str, location: str = "Delhi", limit: int = 100) -> List[Dict]:
    """
    One-function call to search all Indian job sources
    """
    aggregator = IndianJobAggregator()
    return await aggregator.search_all_sources(keywords, location, limit)

# Test function
async def test_aggregator():
    aggregator = IndianJobAggregator()
    
    # Get stats
    stats = await aggregator.get_source_stats()
    print("Aggregator stats:", stats)
    
    # Search jobs
    jobs = await aggregator.search_all_sources("python developer", "Delhi", 20)
    print(f"\nFound {len(jobs)} total jobs:")
    
    for i, job in enumerate(jobs[:5], 1):
        print(f"\n{i}. {job.get('title')}")
        print(f"   Company: {job.get('company')}")
        print(f"   Location: {job.get('location')}")
        print(f"   Source: {job.get('aggregator_source')}")
        print(f"   Score: {job.get('relevance_score')}")

if __name__ == "__main__":
    asyncio.run(test_aggregator())
