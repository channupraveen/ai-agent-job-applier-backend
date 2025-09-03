"""
Enhanced Browser Automation Engine with Full Implementation
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from typing import Dict, List, Optional, Any, Union
import asyncio
import time
import os
from datetime import datetime
from pathlib import Path

from config import Config


class BrowserEngine:
    """Enhanced browser automation engine"""
    
    def __init__(self):
        self.config = Config()
        self.driver = None
        self.wait = None
        self.default_timeout = self.config.BROWSER_TIMEOUT
        self.session_active = False
        self.current_url = ""
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
    
    async def initialize_browser(self, headless: bool = True, browser: str = "chrome") -> bool:
        """Initialize browser session"""
        try:
            if browser.lower() == "chrome":
                options = ChromeOptions()
                if headless:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                
                self.driver = webdriver.Chrome(options=options)
            
            elif browser.lower() == "firefox":
                options = FirefoxOptions()
                if headless:
                    options.add_argument("--headless")
                options.add_argument("--width=1920")
                options.add_argument("--height=1080")
                
                self.driver = webdriver.Firefox(options=options)
            
            else:
                raise ValueError(f"Unsupported browser: {browser}")
            
            self.wait = WebDriverWait(self.driver, self.default_timeout)
            self.session_active = True
            
            # Set implicit wait
            self.driver.implicitly_wait(10)
            
            return True
            
        except Exception as e:
            print(f"Error initializing browser: {str(e)}")
            return False
    
    async def navigate_to_website(self, url: str) -> bool:
        """Navigate to job website"""
        try:
            if not self.session_active or not self.driver:
                raise Exception("Browser not initialized")
            
            self.driver.get(url)
            self.current_url = self.driver.current_url
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"Error navigating to {url}: {str(e)}")
            return False
    
    async def wait_for_element(
        self, 
        selector: str, 
        by: By = By.CSS_SELECTOR, 
        timeout: Optional[int] = None
    ) -> Union[object, None]:
        """Wait for element to be present and return it"""
        try:
            wait_time = timeout or self.default_timeout
            wait = WebDriverWait(self.driver, wait_time)
            element = wait.until(EC.presence_of_element_located((by, selector)))
            return element
        except TimeoutException:
            print(f"Element not found: {selector}")
            return None
    
    async def wait_for_clickable(
        self, 
        selector: str, 
        by: By = By.CSS_SELECTOR, 
        timeout: Optional[int] = None
    ) -> Union[object, None]:
        """Wait for element to be clickable and return it"""
        try:
            wait_time = timeout or self.default_timeout
            wait = WebDriverWait(self.driver, wait_time)
            element = wait.until(EC.element_to_be_clickable((by, selector)))
            return element
        except TimeoutException:
            print(f"Element not clickable: {selector}")
            return None
    
    async def fill_input_field(self, selector: str, value: str, clear_first: bool = True) -> bool:
        """Fill an input field with value"""
        try:
            element = await self.wait_for_element(selector)
            if not element:
                return False
            
            if clear_first:
                element.clear()
            
            element.send_keys(value)
            await asyncio.sleep(0.5)  # Brief pause after typing
            
            return True
            
        except Exception as e:
            print(f"Error filling input {selector}: {str(e)}")
            return False
    
    async def click_element(self, selector: str, wait_for_clickable: bool = True) -> bool:
        """Click an element"""
        try:
            if wait_for_clickable:
                element = await self.wait_for_clickable(selector)
            else:
                element = await self.wait_for_element(selector)
            
            if not element:
                return False
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            await asyncio.sleep(1)
            
            element.click()
            await asyncio.sleep(1)  # Brief pause after clicking
            
            return True
            
        except Exception as e:
            print(f"Error clicking element {selector}: {str(e)}")
            return False
    
    async def select_dropdown_option(self, selector: str, value: str, by_value: bool = True) -> bool:
        """Select option from dropdown"""
        try:
            element = await self.wait_for_element(selector)
            if not element:
                return False
            
            select = Select(element)
            
            if by_value:
                select.select_by_value(value)
            else:
                select.select_by_visible_text(value)
            
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"Error selecting dropdown option: {str(e)}")
            return False
    
    async def upload_file(self, selector: str, file_path: str) -> bool:
        """Upload file to input field"""
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
            
            element = await self.wait_for_element(selector)
            if not element:
                return False
            
            element.send_keys(os.path.abspath(file_path))
            await asyncio.sleep(2)  # Wait for file to upload
            
            return True
            
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return False
    
    async def fill_search_form(self, selectors: dict, data: dict) -> bool:
        """Fill job search form"""
        try:
            success = True
            
            # Fill keywords
            if "keywords" in selectors and "keywords" in data:
                if not await self.fill_input_field(selectors["keywords"], data["keywords"]):
                    success = False
            
            # Fill location
            if "location" in selectors and "location" in data:
                if not await self.fill_input_field(selectors["location"], data["location"]):
                    success = False
            
            # Set experience level
            if "experience" in selectors and "experience" in data:
                if not await self.select_dropdown_option(selectors["experience"], data["experience"]):
                    success = False
            
            # Click search button
            if "submit" in selectors:
                if not await self.click_element(selectors["submit"]):
                    success = False
            
            # Wait for results to load
            await asyncio.sleep(3)
            
            return success
            
        except Exception as e:
            print(f"Error filling search form: {str(e)}")
            return False
    
    async def fill_application_form(self, selectors: dict, data: dict) -> bool:
        """Fill job application form"""
        try:
            success = True
            
            # Fill personal information
            if "name" in selectors and "name" in data:
                if not await self.fill_input_field(selectors["name"], data["name"]):
                    success = False
            
            if "email" in selectors and "email" in data:
                if not await self.fill_input_field(selectors["email"], data["email"]):
                    success = False
            
            if "phone" in selectors and "phone" in data:
                if not await self.fill_input_field(selectors["phone"], data["phone"]):
                    success = False
            
            # Upload resume
            if "resume_upload" in selectors and "resume_path" in data:
                if not await self.upload_file(selectors["resume_upload"], data["resume_path"]):
                    success = False
            
            # Fill cover letter
            if "cover_letter" in selectors and "cover_letter_text" in data:
                if not await self.fill_input_field(selectors["cover_letter"], data["cover_letter_text"]):
                    success = False
            
            # Fill expected salary
            if "expected_salary" in selectors and "expected_salary" in data:
                if not await self.fill_input_field(selectors["expected_salary"], data["expected_salary"]):
                    success = False
            
            return success
            
        except Exception as e:
            print(f"Error filling application form: {str(e)}")
            return False
    
    async def submit_application(self) -> dict:
        """Submit job application"""
        try:
            # Look for common submit button selectors
            submit_selectors = [
                "button[type='submit']",
                ".submit-btn",
                ".apply-btn",
                "#submit",
                ".btn-primary"
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    if await self.click_element(selector):
                        submitted = True
                        break
                except:
                    continue
            
            if not submitted:
                return {"status": "error", "message": "Could not find submit button"}
            
            # Wait for submission to complete
            await asyncio.sleep(5)
            
            # Check for success indicators
            success_indicators = [
                ".success-message",
                ".application-submitted",
                ".thank-you",
                "[data-testid='success']"
            ]
            
            for indicator in success_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                    if element:
                        return {
                            "status": "submitted",
                            "application_id": f"app_{int(time.time())}",
                            "timestamp": datetime.now().isoformat()
                        }
                except:
                    continue
            
            # If no success indicator found, assume success
            return {
                "status": "submitted",
                "application_id": f"app_{int(time.time())}",
                "timestamp": datetime.now().isoformat(),
                "note": "Submission status unclear"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error submitting application: {str(e)}"
            }
    
    async def extract_job_listings(self, selectors: dict, limit: int = 10) -> List[dict]:
        """Extract job listings from current page"""
        try:
            jobs = []
            
            # Wait for job cards to load
            job_cards_selector = selectors.get("job_cards", ".job-card")
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, job_cards_selector)
            
            for i, card in enumerate(job_cards[:limit]):
                try:
                    job_data = {}
                    
                    # Extract title
                    if "job_title" in selectors:
                        title_element = card.find_element(By.CSS_SELECTOR, selectors["job_title"])
                        job_data["title"] = title_element.text.strip()
                    
                    # Extract company
                    if "company_name" in selectors:
                        company_element = card.find_element(By.CSS_SELECTOR, selectors["company_name"])
                        job_data["company"] = company_element.text.strip()
                    
                    # Extract location
                    if "location" in selectors:
                        location_element = card.find_element(By.CSS_SELECTOR, selectors["location"])
                        job_data["location"] = location_element.text.strip()
                    
                    # Extract job link
                    if "job_link" in selectors:
                        link_element = card.find_element(By.CSS_SELECTOR, selectors["job_link"])
                        job_data["url"] = link_element.get_attribute("href")
                    
                    # Extract salary if available
                    if "salary" in selectors:
                        try:
                            salary_element = card.find_element(By.CSS_SELECTOR, selectors["salary"])
                            job_data["salary"] = salary_element.text.strip()
                        except:
                            job_data["salary"] = None
                    
                    job_data["id"] = f"job_{i+1}_{int(time.time())}"
                    job_data["source"] = self.current_url
                    jobs.append(job_data)
                    
                except Exception as e:
                    print(f"Error extracting job {i}: {str(e)}")
                    continue
            
            return jobs
            
        except Exception as e:
            print(f"Error extracting job listings: {str(e)}")
            return []
    
    async def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot for verification"""
        try:
            if not filename:
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            filepath = self.screenshots_dir / filename
            self.driver.save_screenshot(str(filepath))
            
            return str(filepath)
            
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            return ""
    
    async def handle_modal_or_popup(self) -> bool:
        """Handle common modals or popups"""
        try:
            # Common modal/popup selectors
            modal_selectors = [
                ".modal",
                ".popup",
                ".overlay",
                "[role='dialog']",
                ".cookie-banner"
            ]
            
            close_selectors = [
                ".close",
                ".modal-close",
                "[aria-label='Close']",
                ".popup-close",
                "button[data-dismiss='modal']"
            ]
            
            for modal_selector in modal_selectors:
                try:
                    modal = self.driver.find_element(By.CSS_SELECTOR, modal_selector)
                    if modal and modal.is_displayed():
                        # Try to close it
                        for close_selector in close_selectors:
                            try:
                                close_btn = modal.find_element(By.CSS_SELECTOR, close_selector)
                                if close_btn:
                                    close_btn.click()
                                    await asyncio.sleep(1)
                                    return True
                            except:
                                continue
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Error handling modal: {str(e)}")
            return False
    
    async def scroll_page(self, direction: str = "down", pixels: int = 1000) -> bool:
        """Scroll page in specified direction"""
        try:
            if direction.lower() == "down":
                self.driver.execute_script(f"window.scrollBy(0, {pixels});")
            elif direction.lower() == "up":
                self.driver.execute_script(f"window.scrollBy(0, -{pixels});")
            elif direction.lower() == "top":
                self.driver.execute_script("window.scrollTo(0, 0);")
            elif direction.lower() == "bottom":
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error scrolling page: {str(e)}")
            return False
    
    async def wait_for_page_load(self, timeout: int = 30) -> bool:
        """Wait for page to fully load"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            print("Page load timeout")
            return False
    
    def get_page_source(self) -> str:
        """Get current page source"""
        try:
            return self.driver.page_source
        except Exception as e:
            print(f"Error getting page source: {str(e)}")
            return ""
    
    def get_current_url(self) -> str:
        """Get current page URL"""
        try:
            return self.driver.current_url
        except Exception as e:
            print(f"Error getting current URL: {str(e)}")
            return ""
    
    def close_browser(self):
        """Close browser session"""
        try:
            if self.driver:
                self.driver.quit()
            self.session_active = False
            self.driver = None
            self.wait = None
        except Exception as e:
            print(f"Error closing browser: {str(e)}")
    
    def is_session_active(self) -> bool:
        """Check if browser session is active"""
        return self.session_active and self.driver is not None
    
    async def execute_custom_script(self, script: str) -> Any:
        """Execute custom JavaScript"""
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            print(f"Error executing script: {str(e)}")
            return None


# Factory function to create browser engine
def create_browser_engine() -> BrowserEngine:
    """Create and return a new browser engine instance"""
    return BrowserEngine()
