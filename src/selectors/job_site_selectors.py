"""
Job Site Selectors for Web Scraping and Automation
"""

from typing import Dict, Any


def get_selectors_for_site(site_name: str) -> Dict[str, Any]:
    """Get CSS/XPath selectors for a specific job site"""
    
    selectors_map = {
        "linkedin": {
            "login": {
                "username": "#username",
                "password": "#password",
                "submit": "button[type='submit']"
            },
            "search": {
                "keywords": "input[aria-label='Search by title, skill, or company']",
                "location": "input[aria-label='City, state, or zip code']",
                "submit": "button[aria-label='Search']",
                "experience_filter": ".search-reusables__filter-binary-toggle"
            },
            "job_listings": {
                "job_cards": ".job-search-card",
                "job_title": ".sr-only",
                "company_name": ".hidden-nested-link",
                "location": ".job-search-card__location",
                "job_link": ".job-search-card__title-link",
                "easy_apply_button": ".jobs-apply-button--top-card"
            },
            "application": {
                "easy_apply_modal": ".jobs-easy-apply-modal",
                "phone": "input[id*='phoneNumber']",
                "cover_letter": "textarea[id*='coverLetter']",
                "submit_button": ".jobs-easy-apply-form__submit-button",
                "next_button": ".jobs-easy-apply-modal__next-btn",
                "review_button": ".jobs-easy-apply-modal__review-btn"
            }
        },
        
        "indeed": {
            "search": {
                "keywords": "#text-input-what",
                "location": "#text-input-where", 
                "submit": "button[type='submit']",
                "date_filter": "#dateposted",
                "salary_filter": "#salary"
            },
            "job_listings": {
                "job_cards": ".job_seen_beacon",
                "job_title": ".jobTitle",
                "company_name": ".companyName",
                "location": ".companyLocation",
                "job_link": ".jobTitle a",
                "apply_button": ".ia-IndeedApplyButton"
            },
            "application": {
                "apply_modal": ".ia-Modal",
                "resume_upload": "input[type='file']",
                "cover_letter": "textarea[name='coverLetter']",
                "phone": "input[name='phone']",
                "submit_button": "button[type='submit']"
            }
        },
        
        "naukri": {
            "login": {
                "username": "#usernameField",
                "password": "#passwordField",
                "submit": "#loginButton"
            },
            "search": {
                "keywords": ".suggestor-input",
                "location": "#locationField",
                "submit": ".qsbSubmit",
                "experience_filter": ".experienceDD"
            },
            "job_listings": {
                "job_cards": ".jobTuple",
                "job_title": ".title",
                "company_name": ".subTitle",
                "location": ".location",
                "job_link": ".title a",
                "apply_button": ".apply"
            },
            "application": {
                "apply_form": ".applyForm",
                "cover_letter": "textarea[name='coverLetter']",
                "expected_salary": "input[name='expectedSalary']",
                "submit_button": ".btn-apply"
            }
        },
        
        "glassdoor": {
            "search": {
                "keywords": "#searchBar-jobTitle",
                "location": "#searchBar-location",
                "submit": "#searchButton",
                "company_size_filter": ".filterContainer"
            },
            "job_listings": {
                "job_cards": ".react-job-listing",
                "job_title": ".jobTitle",
                "company_name": ".employerName",
                "location": ".location",
                "job_link": ".jobTitle a",
                "easy_apply_button": ".oa-EasyApplyJobCard-module_easyApplyButton"
            },
            "application": {
                "apply_modal": ".oa-EasyApplyModal",
                "cover_letter": "textarea[data-test='coverLetterTextArea']",
                "phone": "input[data-test='phoneNumber']",
                "submit_button": "button[data-test='submit-application']"
            }
        },
        
        "monster": {
            "search": {
                "keywords": "#q",
                "location": "#where",
                "submit": "#search",
                "job_type_filter": ".checkbox-filter"
            },
            "job_listings": {
                "job_cards": ".js_result_row",
                "job_title": ".js_job_link",
                "company_name": ".company",
                "location": ".location",
                "job_link": ".js_job_link",
                "apply_button": ".apply-btn"
            },
            "application": {
                "apply_form": "#apply-form",
                "resume_upload": "input[name='resume']",
                "cover_letter": "textarea[name='coverLetter']",
                "submit_button": ".btn-apply"
            }
        },
        
        "shine": {
            "search": {
                "keywords": "#id_q",
                "location": "#id_loc",
                "submit": "#searchform input[type='submit']",
                "experience_filter": ".exp-filter"
            },
            "job_listings": {
                "job_cards": ".job-card",
                "job_title": ".job-title",
                "company_name": ".recruiter-name",
                "location": ".job-location",
                "job_link": ".job-title a",
                "apply_button": ".apply-btn"
            },
            "application": {
                "apply_modal": ".apply-modal",
                "cover_letter": "textarea[name='coverNote']",
                "expected_salary": "input[name='expectedSalary']",
                "submit_button": ".submit-application"
            }
        }
    }
    
    return selectors_map.get(site_name.lower(), {})


def get_common_selectors() -> Dict[str, str]:
    """Get common selectors used across multiple sites"""
    return {
        "generic_job_title": ["h1", ".job-title", ".jobTitle", ".title"],
        "generic_company": [".company", ".companyName", ".employer"],
        "generic_location": [".location", ".job-location", ".companyLocation"],
        "generic_description": [".job-description", ".jobDescription", ".description"],
        "generic_apply_button": [".apply", ".apply-btn", ".easy-apply", ".jobs-apply-button"],
        "generic_salary": [".salary", ".sal", ".compensation"],
        "generic_job_type": [".job-type", ".employment-type", ".jobType"]
    }


def get_anti_bot_selectors() -> Dict[str, str]:
    """Selectors for handling anti-bot measures"""
    return {
        "captcha": [
            ".recaptcha",
            "#captcha",
            ".g-recaptcha",
            ".hcaptcha"
        ],
        "verification": [
            ".verification-modal",
            ".human-verification", 
            ".security-check"
        ],
        "rate_limit": [
            ".rate-limit-message",
            ".too-many-requests",
            ".slow-down"
        ],
        "blocked": [
            ".access-denied",
            ".blocked-message",
            ".unauthorized"
        ]
    }


def get_form_field_selectors() -> Dict[str, list]:
    """Common form field selectors across job sites"""
    return {
        "name": [
            "input[name='name']",
            "input[name='firstName']", 
            "input[name='fullName']",
            "#name",
            "#fullName"
        ],
        "email": [
            "input[type='email']",
            "input[name='email']",
            "#email",
            "#emailAddress"
        ],
        "phone": [
            "input[type='tel']",
            "input[name='phone']",
            "input[name='phoneNumber']",
            "#phone",
            "#phoneNumber"
        ],
        "resume_upload": [
            "input[type='file'][accept*='pdf']",
            "input[name='resume']",
            "input[name='cv']",
            ".resume-upload input",
            "#resume"
        ],
        "cover_letter": [
            "textarea[name='coverLetter']",
            "textarea[name='coverNote']", 
            "textarea[name='message']",
            "#coverLetter",
            ".cover-letter textarea"
        ],
        "expected_salary": [
            "input[name='salary']",
            "input[name='expectedSalary']",
            "input[name='salaryExpectation']",
            "#salary",
            "#expectedSalary"
        ]
    }


def validate_selectors(site_name: str) -> bool:
    """Validate that selectors exist for a given site"""
    selectors = get_selectors_for_site(site_name)
    
    required_sections = ["search", "job_listings"]
    return all(section in selectors for section in required_sections)


def get_site_specific_config(site_name: str) -> Dict[str, Any]:
    """Get site-specific configuration and quirks"""
    configs = {
        "linkedin": {
            "requires_login": True,
            "has_easy_apply": True,
            "rate_limit_seconds": 30,
            "max_applications_per_day": 50,
            "supports_bulk_apply": True,
            "anti_bot_measures": ["captcha", "rate_limiting"]
        },
        "indeed": {
            "requires_login": False,
            "has_easy_apply": True,
            "rate_limit_seconds": 15,
            "max_applications_per_day": 100,
            "supports_bulk_apply": False,
            "anti_bot_measures": ["rate_limiting"]
        },
        "naukri": {
            "requires_login": True,
            "has_easy_apply": True,
            "rate_limit_seconds": 20,
            "max_applications_per_day": 75,
            "supports_bulk_apply": True,
            "anti_bot_measures": ["captcha", "verification"]
        },
        "glassdoor": {
            "requires_login": False,
            "has_easy_apply": True,
            "rate_limit_seconds": 25,
            "max_applications_per_day": 40,
            "supports_bulk_apply": False,
            "anti_bot_measures": ["captcha", "rate_limiting", "verification"]
        },
        "monster": {
            "requires_login": False,
            "has_easy_apply": False,
            "rate_limit_seconds": 10,
            "max_applications_per_day": 80,
            "supports_bulk_apply": False,
            "anti_bot_measures": ["rate_limiting"]
        },
        "shine": {
            "requires_login": False,
            "has_easy_apply": True,
            "rate_limit_seconds": 15,
            "max_applications_per_day": 60,
            "supports_bulk_apply": False,
            "anti_bot_measures": ["rate_limiting"]
        }
    }
    
    return configs.get(site_name.lower(), {})
