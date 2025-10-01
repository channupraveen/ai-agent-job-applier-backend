"""
Utility to extract job source from URL
"""

def extract_source_from_url(url: str) -> str:
    """
    Extract the job source/platform name from a job URL
    
    Args:
        url: Job posting URL
        
    Returns:
        Source name (e.g., 'LinkedIn', 'Indeed', 'Naukri')
    """
    if not url:
        return 'Unknown'
    
    url_lower = url.lower()
    
    # Job boards
    if 'linkedin.com' in url_lower:
        return 'LinkedIn'
    elif 'shine.com' in url_lower:
        return 'Shine'
    elif 'glassdoor' in url_lower:
        return 'Glassdoor'
    elif 'jooble.org' in url_lower:
        return 'Jooble'
    elif 'instahyre.com' in url_lower:
        return 'Instahyre'
    elif 'indeed.com' in url_lower:
        return 'Indeed'
    elif 'foundit.in' in url_lower or 'monsterindia' in url_lower:
        return 'Foundit'
    elif 'hirist.tech' in url_lower or 'hirist.com' in url_lower:
        return 'Hirist'
    elif 'timesjobs.com' in url_lower:
        return 'TimesJobs'
    elif 'talent.com' in url_lower:
        return 'Talent.com'
    elif 'adzuna.in' in url_lower:
        return 'Adzuna'
    elif 'internshala.com' in url_lower:
        return 'Internshala'
    elif 'naukri.com' in url_lower:
        return 'Naukri'
    elif 'cutshort.io' in url_lower:
        return 'Cutshort'
    elif 'wellfound.com' in url_lower or 'angel.co' in url_lower:
        return 'Wellfound'
    elif 'apnacircle.com' in url_lower:
        return 'Apna Circle'
    
    # Company career sites
    elif 'jobs.barclays' in url_lower:
        return 'Barclays Careers'
    elif 'careers.cognizant.com' in url_lower:
        return 'Cognizant Careers'
    elif 'jobs.siemens.com' in url_lower:
        return 'Siemens Careers'
    elif 'jobs.citi.com' in url_lower:
        return 'Citi Careers'
    elif 'capgemini.com' in url_lower:
        return 'Capgemini Careers'
    elif 'se.com' in url_lower and 'careers' in url_lower:
        return 'Schneider Electric Careers'
    elif 'careers.blackrock.com' in url_lower:
        return 'BlackRock Careers'
    elif 'careers.mastercard.com' in url_lower:
        return 'Mastercard Careers'
    elif 'careers.united.com' in url_lower:
        return 'United Airlines Careers'
    elif 'careers.oracle.com' in url_lower:
        return 'Oracle Careers'
    elif 'jobs.mercedes-benz.com' in url_lower:
        return 'Mercedes-Benz Careers'
    elif 'telstra.wd3.myworkdayjobs.com' in url_lower:
        return 'Telstra Careers'
    elif 'careers.hpe.com' in url_lower:
        return 'HPE Careers'
    elif 'jobs-ups.com' in url_lower:
        return 'UPS Careers'
    elif 'synechron.wd1.myworkdayjobs.com' in url_lower:
        return 'Synechron Careers'
    elif 'group.bnpparibas' in url_lower:
        return 'BNP Paribas Careers'
    elif 'careers.ibm.com' in url_lower or 'ibm.com/jobs' in url_lower:
        return 'IBM Careers'
    
    # Generic company career sites
    elif 'careers.' in url_lower or '/careers/' in url_lower:
        return 'Company Website'
    elif 'jobs.' in url_lower or '/jobs/' in url_lower:
        return 'Company Website'
    
    # Google Jobs API results (these come from various sources)
    elif 'google.com/search' in url_lower or 'jobs.google.com' in url_lower:
        return 'Google Jobs'
    
    # Default
    else:
        return 'Company Website'
