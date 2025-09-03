"""
Intelligent Form Filling Engine
"""

from typing import Dict, List, Optional, Any, Union
import asyncio
import re
from datetime import datetime
from dataclasses import dataclass
from selenium.webdriver.common.by import By

from .browser import BrowserEngine
from config import Config


@dataclass
class FormField:
    """Represents a form field to be filled"""
    name: str
    selector: str
    field_type: str  # input, textarea, select, file, checkbox, radio
    value: Any
    required: bool = False
    validation_pattern: Optional[str] = None


class FormFiller:
    """Intelligent form filling with data mapping and validation"""
    
    def __init__(self, browser_engine: Optional[BrowserEngine] = None):
        self.browser = browser_engine or BrowserEngine()
        self.config = Config()
        self.common_field_mappings = self._initialize_common_mappings()
    
    def _initialize_common_mappings(self) -> Dict[str, List[str]]:
        """Initialize common field name mappings"""
        return {
            # Personal Information
            "full_name": ["name", "fullName", "firstName", "full_name"],
            "first_name": ["firstName", "fname", "first_name"],
            "last_name": ["lastName", "lname", "last_name"],
            "email": ["email", "emailAddress", "email_address"],
            "phone": ["phone", "phoneNumber", "mobile", "phone_number"],
            "address": ["address", "street_address", "home_address"],
            "city": ["city", "location", "current_city"],
            "state": ["state", "province", "region"],
            "zip_code": ["zipCode", "postalCode", "zip", "postal_code"],
            "country": ["country", "nationality"],
            
            # Professional Information
            "current_title": ["currentTitle", "jobTitle", "position", "current_position"],
            "company": ["company", "currentCompany", "employer", "current_company"],
            "experience_years": ["experience", "yearsExperience", "work_experience"],
            "salary_expectation": ["expectedSalary", "salaryExpectation", "desired_salary"],
            
            # Job Search
            "keywords": ["keywords", "jobTitle", "position", "what", "q"],
            "location_search": ["location", "where", "city", "place"],
            
            # Files
            "resume": ["resume", "cv", "resume_file", "cv_file"],
            "cover_letter_file": ["coverLetterFile", "cover_letter", "motivation_letter"]
        }
    
    async def fill_form_with_selectors(
        self, 
        selectors: Dict[str, str], 
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill form using provided selectors"""
        results = {
            "success": True,
            "filled_fields": [],
            "failed_fields": [],
            "warnings": []
        }
        
        for field_name, selector in selectors.items():
            try:
                value = self._get_field_value(field_name, user_data)
                if value is not None:
                    success = await self.browser.fill_input_field(selector, str(value))
                    if success:
                        results["filled_fields"].append(field_name)
                    else:
                        results["failed_fields"].append({
                            "field": field_name,
                            "reason": "Failed to fill in browser"
                        })
                else:
                    results["warnings"].append(f"No value for field: {field_name}")
            except Exception as e:
                results["failed_fields"].append({
                    "field": field_name,
                    "reason": str(e)
                })
        
        return results
    
    def _get_field_value(
        self, 
        field_name: str, 
        user_data: Dict[str, Any], 
        custom_mappings: Optional[Dict[str, str]] = None
    ) -> Any:
        """Get value for a field from user data"""
        
        # First check custom mappings
        if custom_mappings and field_name in custom_mappings:
            return user_data.get(custom_mappings[field_name])
        
        # Check direct field name match
        if field_name in user_data:
            return user_data[field_name]
        
        # Check common mappings
        if field_name in self.common_field_mappings:
            for possible_key in self.common_field_mappings[field_name]:
                if possible_key in user_data:
                    return user_data[possible_key]
        
        # Check for partial matches (case insensitive)
        field_lower = field_name.lower()
        for key, value in user_data.items():
            if field_lower in key.lower() or key.lower() in field_lower:
                return value
        
        return None
    
    async def fill_smart_form(
        self, 
        user_data: Dict[str, Any], 
        form_selectors: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Intelligently fill form by detecting fields automatically"""
        try:
            if form_selectors:
                return await self.fill_form_with_selectors(form_selectors, user_data)
            else:
                # Use common selectors
                common_selectors = {
                    "keywords": "input[name='q'], input[name='keywords'], #text-input-what",
                    "location": "input[name='l'], input[name='location'], #text-input-where",
                    "email": "input[type='email'], input[name='email']",
                    "phone": "input[type='tel'], input[name='phone']",
                    "name": "input[name='name'], input[name='firstName']"
                }
                return await self.fill_form_with_selectors(common_selectors, user_data)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in smart form filling: {str(e)}",
                "filled_fields": [],
                "failed_fields": [],
                "warnings": []
            }


# Factory function
def create_form_filler(browser_engine: Optional[BrowserEngine] = None) -> FormFiller:
    """Create and return a new form filler instance"""
    return FormFiller(browser_engine)
