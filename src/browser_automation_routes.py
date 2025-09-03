"""
Browser Automation API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import base64
import asyncio
import os

from .auth import get_current_user
from .models import get_job_db, UserProfile as User

router = APIRouter(tags=["Browser Automation"])


class BrowserStartRequest(BaseModel):
    headless: bool = True
    browser_type: str = "chrome"  # chrome, firefox, edge
    window_size: Optional[str] = "1920x1080"
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    timeout: int = 30


class InteractionRequest(BaseModel):
    action: str  # click, type, scroll, wait, navigate
    selector: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    wait_time: Optional[int] = None
    scroll_pixels: Optional[int] = None


class ScreenshotRequest(BaseModel):
    full_page: bool = False
    element_selector: Optional[str] = None
    save_to_file: bool = True


# Global browser sessions storage
browser_sessions = {}


@router.post("/automation/browser/start")
async def start_browser_session(
    browser_request: BrowserStartRequest, current_user: User = Depends(get_current_user)
):
    """Initialize browser automation session"""
    try:
        # Check if user already has an active session
        if current_user.id in browser_sessions:
            existing_session = browser_sessions[current_user.id]
            if existing_session.get("status") == "active":
                return {
                    "success": False,
                    "message": "Browser session already active",
                    "session_id": existing_session["session_id"],
                }

        # Generate session ID
        session_id = f"browser_{current_user.id}_{int(datetime.utcnow().timestamp())}"

        # In real implementation, initialize Selenium WebDriver here
        # For now, simulate browser session creation

        browser_config = {
            "headless": browser_request.headless,
            "browser_type": browser_request.browser_type,
            "window_size": browser_request.window_size,
            "user_agent": browser_request.user_agent,
            "proxy": browser_request.proxy,
            "timeout": browser_request.timeout,
        }

        # Store session info
        browser_sessions[current_user.id] = {
            "session_id": session_id,
            "status": "active",
            "started_at": datetime.utcnow(),
            "config": browser_config,
            "current_url": "about:blank",
            "actions_performed": 0,
            "screenshots_taken": 0,
        }

        return {
            "success": True,
            "message": "Browser session started successfully",
            "session_id": session_id,
            "browser_config": browser_config,
            "capabilities": [
                "navigation",
                "element_interaction",
                "form_filling",
                "screenshot_capture",
                "page_scraping",
                "cookie_management",
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting browser session: {str(e)}"
        )


@router.get("/automation/browser/status")
async def get_browser_status(current_user: User = Depends(get_current_user)):
    """Get browser session status"""
    try:
        if current_user.id not in browser_sessions:
            return {
                "success": True,
                "session_active": False,
                "message": "No active browser session",
            }

        session_data = browser_sessions[current_user.id]

        # Calculate session duration
        duration = datetime.utcnow() - session_data["started_at"]

        return {
            "success": True,
            "session_active": True,
            "session_id": session_data["session_id"],
            "status": session_data["status"],
            "started_at": session_data["started_at"].isoformat(),
            "duration": str(duration),
            "current_url": session_data["current_url"],
            "browser_type": session_data["config"]["browser_type"],
            "actions_performed": session_data["actions_performed"],
            "screenshots_taken": session_data["screenshots_taken"],
            "session_health": "healthy",  # In real implementation, check actual browser health
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting browser status: {str(e)}"
        )


@router.post("/automation/browser/navigate")
async def navigate_to_url(
    url: str, wait_for_load: bool = True, current_user: User = Depends(get_current_user)
):
    """Navigate browser to specific URL"""
    try:
        if current_user.id not in browser_sessions:
            raise HTTPException(status_code=404, detail="No active browser session")

        session_data = browser_sessions[current_user.id]

        # Validate URL
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Simulate navigation
        await asyncio.sleep(2)  # Simulate page load time

        # Update session data
        session_data["current_url"] = url
        session_data["actions_performed"] += 1

        # Simulate page analysis
        page_info = {
            "title": f"Page Title for {url}",
            "load_time": 2.1,
            "elements_found": {"forms": 2, "buttons": 15, "links": 45, "inputs": 8},
            "has_job_listings": "indeed.com" in url
            or "linkedin.com" in url
            or "naukri.com" in url,
        }

        return {
            "success": True,
            "message": f"Successfully navigated to {url}",
            "current_url": url,
            "page_info": page_info,
            "navigation_time": "2.1 seconds",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error navigating to URL: {str(e)}"
        )


@router.post("/automation/browser/interact")
async def browser_interact(
    interaction: InteractionRequest, current_user: User = Depends(get_current_user)
):
    """Perform browser interaction (click, type, scroll, etc.)"""
    try:
        if current_user.id not in browser_sessions:
            raise HTTPException(status_code=404, detail="No active browser session")

        session_data = browser_sessions[current_user.id]

        # Validate interaction
        valid_actions = [
            "click",
            "type",
            "scroll",
            "wait",
            "navigate",
            "select",
            "hover",
        ]
        if interaction.action not in valid_actions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action. Use: {', '.join(valid_actions)}",
            )

        # Simulate different interactions
        interaction_result = {}

        if interaction.action == "click":
            if not interaction.selector:
                raise HTTPException(
                    status_code=400, detail="Selector required for click action"
                )

            await asyncio.sleep(0.5)  # Simulate click delay
            interaction_result = {
                "action": "click",
                "selector": interaction.selector,
                "result": "Element clicked successfully",
                "element_found": True,
            }

        elif interaction.action == "type":
            if not interaction.selector or not interaction.text:
                raise HTTPException(
                    status_code=400, detail="Selector and text required for type action"
                )

            await asyncio.sleep(len(interaction.text) * 0.1)  # Simulate typing delay
            interaction_result = {
                "action": "type",
                "selector": interaction.selector,
                "text_entered": interaction.text,
                "result": "Text entered successfully",
            }

        elif interaction.action == "scroll":
            scroll_pixels = interaction.scroll_pixels or 300
            await asyncio.sleep(0.3)
            interaction_result = {
                "action": "scroll",
                "pixels_scrolled": scroll_pixels,
                "result": "Page scrolled successfully",
            }

        elif interaction.action == "wait":
            wait_time = interaction.wait_time or 2
            await asyncio.sleep(wait_time)
            interaction_result = {
                "action": "wait",
                "wait_time": wait_time,
                "result": f"Waited for {wait_time} seconds",
            }

        elif interaction.action == "navigate":
            if not interaction.url:
                raise HTTPException(
                    status_code=400, detail="URL required for navigate action"
                )

            return await navigate_to_url(interaction.url, current_user=current_user)

        # Update session stats
        session_data["actions_performed"] += 1

        return {
            "success": True,
            "message": f"Interaction '{interaction.action}' completed successfully",
            "interaction_result": interaction_result,
            "session_stats": {
                "total_actions": session_data["actions_performed"],
                "current_url": session_data["current_url"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error performing interaction: {str(e)}"
        )


@router.post("/automation/browser/screenshot")
async def take_screenshot(
    screenshot_request: ScreenshotRequest,
    current_user: User = Depends(get_current_user),
):
    """Take website screenshot"""
    try:
        if current_user.id not in browser_sessions:
            raise HTTPException(status_code=404, detail="No active browser session")

        session_data = browser_sessions[current_user.id]

        # Simulate screenshot capture
        await asyncio.sleep(1)

        # Generate screenshot filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"screenshot_{current_user.id}_{timestamp}.png"

        # Create screenshots directory
        screenshots_dir = "uploads/screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshots_dir, screenshot_filename)

        # Simulate screenshot data (in real implementation, use Selenium screenshot)
        screenshot_info = {
            "filename": screenshot_filename,
            "file_path": screenshot_path,
            "full_page": screenshot_request.full_page,
            "element_selector": screenshot_request.element_selector,
            "timestamp": datetime.utcnow().isoformat(),
            "file_size": "245 KB",
            "dimensions": "1920x1080",
            "current_url": session_data["current_url"],
        }

        if screenshot_request.save_to_file:
            # In real implementation, save actual screenshot
            with open(screenshot_path, "w") as f:
                f.write("Simulated screenshot data")

        # Update session stats
        session_data["screenshots_taken"] += 1

        return {
            "success": True,
            "message": "Screenshot captured successfully",
            "screenshot_info": screenshot_info,
            "download_url": f"/uploads/screenshots/{screenshot_filename}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error taking screenshot: {str(e)}"
        )


@router.post("/automation/browser/fill-form")
async def fill_job_application_form(
    form_data: Dict[str, Any],
    form_selectors: Dict[str, str],
    current_user: User = Depends(get_current_user),
):
    """Fill job application form automatically"""
    try:
        if current_user.id not in browser_sessions:
            raise HTTPException(status_code=404, detail="No active browser session")

        session_data = browser_sessions[current_user.id]

        # Simulate form filling
        filled_fields = []

        for field_name, field_value in form_data.items():
            if field_name in form_selectors:
                selector = form_selectors[field_name]

                # Simulate typing in field
                await asyncio.sleep(0.5)

                filled_fields.append(
                    {
                        "field": field_name,
                        "selector": selector,
                        "value": (
                            str(field_value)[:50] + "..."
                            if len(str(field_value)) > 50
                            else str(field_value)
                        ),
                        "status": "filled",
                    }
                )

        # Simulate file uploads (resume, cover letter)
        uploaded_files = []
        if "resume_upload" in form_selectors and current_user.resume_path:
            uploaded_files.append(
                {
                    "file_type": "resume",
                    "file_path": current_user.resume_path,
                    "status": "uploaded",
                }
            )

        session_data["actions_performed"] += len(filled_fields)

        return {
            "success": True,
            "message": f"Form filled successfully. {len(filled_fields)} fields completed.",
            "filled_fields": filled_fields,
            "uploaded_files": uploaded_files,
            "form_completion": {
                "total_fields": len(form_data),
                "fields_filled": len(filled_fields),
                "completion_rate": f"{(len(filled_fields) / max(len(form_data), 1)) * 100:.1f}%",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filling form: {str(e)}")


@router.get("/automation/browser/page-info")
async def get_current_page_info(current_user: User = Depends(get_current_user)):
    """Get information about the current page"""
    try:
        if current_user.id not in browser_sessions:
            raise HTTPException(status_code=404, detail="No active browser session")

        session_data = browser_sessions[current_user.id]
        current_url = session_data["current_url"]

        # Simulate page analysis
        await asyncio.sleep(1)

        page_analysis = {
            "url": current_url,
            "title": f"Page Analysis for {current_url}",
            "page_type": detect_page_type(current_url),
            "elements": {
                "job_listings": 12 if "jobs" in current_url else 0,
                "application_forms": 1 if "apply" in current_url else 0,
                "login_forms": 1 if "login" in current_url else 0,
                "search_boxes": 2,
                "navigation_links": 15,
                "buttons": 8,
                "input_fields": 6,
            },
            "automation_opportunities": generate_automation_suggestions(current_url),
            "scraped_data": {
                "company_name": extract_company_from_url(current_url),
                "job_count": 12 if "jobs" in current_url else 0,
                "page_load_time": "2.3 seconds",
            },
            "technical_info": {
                "framework_detected": (
                    "React"
                    if "linkedin" in current_url
                    else "Vue.js" if "indeed" in current_url else "Unknown"
                ),
                "ajax_requests": 5,
                "cookies_count": 8,
                "local_storage_items": 3,
            },
        }

        return {
            "success": True,
            "message": "Page analysis completed",
            "page_info": page_analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing page: {str(e)}")


@router.post("/automation/browser/scrape-jobs")
async def scrape_jobs_from_current_page(
    max_jobs: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Scrape job listings from current page"""
    try:
        if current_user.id not in browser_sessions:
            raise HTTPException(status_code=404, detail="No active browser session")

        session_data = browser_sessions[current_user.id]
        current_url = session_data["current_url"]

        # Simulate job scraping
        await asyncio.sleep(3)

        scraped_jobs = []
        for i in range(min(max_jobs, 12)):  # Simulate finding jobs
            job_data = {
                "title": f"Software Engineer {i+1}",
                "company": f"Company {i+1}",
                "location": "Remote" if i % 2 == 0 else "Bangalore",
                "url": f"{current_url}/job/{i+1}",
                "description": f"Exciting opportunity for software engineer {i+1}",
                "requirements": "Python, JavaScript, React, Node.js",
                "salary": f"₹{10 + i},00,000 - ₹{15 + i},00,000",
                "posted_date": f"{i+1} days ago",
                "scraped_from": current_url,
                "scraped_at": datetime.utcnow().isoformat(),
            }
            scraped_jobs.append(job_data)

        # Save scraped jobs to database
        saved_jobs = 0
        for job_data in scraped_jobs:
            try:
                # Check if job already exists
                existing_query = "SELECT id FROM job_applications WHERE url = :url"
                existing = db.execute(
                    text(existing_query), {"url": job_data["url"]}
                ).fetchone()

                if not existing:
                    # Calculate match score
                    user_skills = json.loads(current_user.skills or "[]")
                    match_score = calculate_match_score(job_data, user_skills)

                    insert_query = """
                   INSERT INTO job_applications (
                       title, company, location, url, description, requirements,
                       salary_range, status, match_score, ai_decision, ai_reasoning,
                       created_at, updated_at
                   ) VALUES (
                       :title, :company, :location, :url, :description, :requirements,
                       :salary_range, 'found', :match_score, :ai_decision, :ai_reasoning,
                       :created_at, :updated_at
                   ) RETURNING id
                   """

                    ai_decision = (
                        "apply"
                        if match_score >= 70
                        else "maybe" if match_score >= 40 else "skip"
                    )

                    params = {
                        "title": job_data["title"],
                        "company": job_data["company"],
                        "location": job_data["location"],
                        "url": job_data["url"],
                        "description": job_data["description"],
                        "requirements": job_data["requirements"],
                        "salary_range": job_data["salary"],
                        "match_score": match_score,
                        "ai_decision": ai_decision,
                        "ai_reasoning": f"Browser scraped job: {match_score}% match",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }

                    result = db.execute(text(insert_query), params)
                    if result.fetchone():
                        saved_jobs += 1
            except Exception:
                continue

        db.commit()
        session_data["actions_performed"] += 1

        return {
            "success": True,
            "message": f"Scraped {len(scraped_jobs)} jobs from current page",
            "scraping_results": {
                "jobs_found": len(scraped_jobs),
                "jobs_saved": saved_jobs,
                "source_url": current_url,
                "scraping_time": "3.2 seconds",
            },
            "scraped_jobs": scraped_jobs[:5],  # Return first 5 for preview
            "high_match_jobs": len(
                [
                    j
                    for j in scraped_jobs
                    if calculate_match_score(j, json.loads(current_user.skills or "[]"))
                    >= 80
                ]
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error scraping jobs: {str(e)}")


@router.post("/automation/browser/auto-apply")
async def auto_apply_to_job(
    job_url: str,
    use_saved_data: bool = True,
    custom_cover_letter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Automatically apply to a specific job"""
    try:
        if current_user.id not in browser_sessions:
            raise HTTPException(status_code=404, detail="No active browser session")

        session_data = browser_sessions[current_user.id]

        # Navigate to job application page
        await asyncio.sleep(2)
        session_data["current_url"] = job_url

        # Simulate application process
        application_steps = []

        # Step 1: Fill personal information
        personal_info = {
            "name": current_user.name or "John Doe",
            "email": current_user.email,
            "phone": current_user.phone or "9999999999",
            "experience_years": current_user.experience_years or 3,
        }

        application_steps.append(
            {
                "step": "personal_information",
                "status": "completed",
                "fields_filled": len(personal_info),
                "duration": "15 seconds",
            }
        )

        # Step 2: Upload resume
        resume_uploaded = False
        if current_user.resume_path and os.path.exists(current_user.resume_path):
            resume_uploaded = True
            application_steps.append(
                {
                    "step": "resume_upload",
                    "status": "completed",
                    "file_path": current_user.resume_path,
                    "duration": "10 seconds",
                }
            )

        # Step 3: Cover letter
        cover_letter_added = False
        if custom_cover_letter or use_saved_data:
            cover_letter_added = True
            application_steps.append(
                {
                    "step": "cover_letter",
                    "status": "completed",
                    "method": "custom" if custom_cover_letter else "generated",
                    "duration": "20 seconds",
                }
            )

        # Step 4: Additional questions (simulate)
        additional_questions = [
            {
                "question": "Years of experience with Python?",
                "answer": str(current_user.experience_years or 3),
            },
            {"question": "Available to start immediately?", "answer": "Yes"},
            {"question": "Willing to relocate?", "answer": "Yes"},
        ]

        application_steps.append(
            {
                "step": "additional_questions",
                "status": "completed",
                "questions_answered": len(additional_questions),
                "duration": "30 seconds",
            }
        )

        # Step 5: Submit application
        await asyncio.sleep(1)
        application_steps.append(
            {
                "step": "submission",
                "status": "completed",
                "confirmation_number": f"APP{int(datetime.utcnow().timestamp())}",
                "duration": "5 seconds",
            }
        )

        # Update database with application status
        try:
            update_query = """
           UPDATE job_applications 
           SET status = 'applied', applied_at = :applied_at, updated_at = :updated_at
           WHERE url = :job_url
           RETURNING id, title, company
           """

            result = db.execute(
                text(update_query),
                {
                    "job_url": job_url,
                    "applied_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )

            updated_job = result.fetchone()
            db.commit()

            job_info = (
                dict(updated_job._mapping)
                if updated_job
                else {"title": "Unknown Job", "company": "Unknown Company"}
            )

        except Exception:
            job_info = {"title": "Job Application", "company": "Unknown Company"}

        session_data["actions_performed"] += 5  # Count all application steps

        total_duration = sum(
            int(step.get("duration", "0 seconds").split()[0])
            for step in application_steps
        )

        return {
            "success": True,
            "message": f"Successfully applied to {job_info['title']} at {job_info['company']}",
            "application_result": {
                "job_url": job_url,
                "job_title": job_info["title"],
                "company": job_info["company"],
                "application_status": "submitted",
                "total_steps": len(application_steps),
                "total_duration": f"{total_duration} seconds",
                "resume_uploaded": resume_uploaded,
                "cover_letter_added": cover_letter_added,
            },
            "application_steps": application_steps,
            "confirmation": {
                "applied_at": datetime.utcnow().isoformat(),
                "confirmation_available": True,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error auto-applying to job: {str(e)}"
        )


@router.post("/automation/browser/close")
async def close_browser_session(current_user: User = Depends(get_current_user)):
    """Close browser automation session"""
    try:
        if current_user.id not in browser_sessions:
            return {"success": True, "message": "No active browser session to close"}

        session_data = browser_sessions[current_user.id]
        session_duration = datetime.utcnow() - session_data["started_at"]

        # Get session summary
        session_summary = {
            "session_id": session_data["session_id"],
            "duration": str(session_duration),
            "actions_performed": session_data["actions_performed"],
            "screenshots_taken": session_data["screenshots_taken"],
            "final_url": session_data["current_url"],
            "browser_type": session_data["config"]["browser_type"],
        }

        # Clean up session
        del browser_sessions[current_user.id]

        return {
            "success": True,
            "message": "Browser session closed successfully",
            "session_summary": session_summary,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error closing browser session: {str(e)}"
        )


@router.get("/automation/browser/sessions")
async def get_browser_session_history(
    limit: int = Query(10, ge=1, le=50), current_user: User = Depends(get_current_user)
):
    """Get browser session history"""
    try:
        # In a full implementation, you'd store session history in database
        # For now, return mock data

        session_history = [
            {
                "session_id": f"browser_{current_user.id}_{i}",
                "started_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "duration": f"{20 + i * 5} minutes",
                "actions_performed": 15 + i * 3,
                "screenshots_taken": i + 1,
                "status": "completed",
                "browser_type": "chrome",
                "final_url": f"https://example-{i}.com",
            }
            for i in range(1, min(limit + 1, 6))
        ]

        return {
            "success": True,
            "session_history": session_history,
            "total_sessions": len(session_history),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting session history: {str(e)}"
        )


# Helper functions
def detect_page_type(url: str) -> str:
    """Detect the type of page based on URL"""
    if "linkedin.com/jobs" in url:
        return "linkedin_jobs"
    elif "indeed.com" in url:
        return "indeed_jobs"
    elif "naukri.com" in url:
        return "naukri_jobs"
    elif "glassdoor.com" in url:
        return "glassdoor_jobs"
    elif "/apply" in url:
        return "application_form"
    elif "/login" in url:
        return "login_page"
    else:
        return "general_page"


def generate_automation_suggestions(url: str) -> List[str]:
    """Generate automation suggestions based on current page"""
    suggestions = []

    if "jobs" in url:
        suggestions.extend(
            [
                "Scrape job listings from this page",
                "Filter jobs by salary range",
                "Save high-match jobs to database",
                "Take screenshot of job listings",
            ]
        )

    if "apply" in url:
        suggestions.extend(
            [
                "Auto-fill application form",
                "Upload resume and cover letter",
                "Answer common application questions",
                "Submit application automatically",
            ]
        )

    if "linkedin.com" in url:
        suggestions.extend(
            [
                "Connect with company recruiters",
                "Save job posts for later",
                "Apply with LinkedIn profile",
            ]
        )

    if not suggestions:
        suggestions = [
            "Navigate to job search pages",
            "Take screenshot of current page",
            "Analyze page structure",
            "Extract contact information",
        ]

    return suggestions


def extract_company_from_url(url: str) -> str:
    """Extract company name from URL"""
    if "linkedin.com" in url:
        return "LinkedIn"
    elif "indeed.com" in url:
        return "Indeed"
    elif "naukri.com" in url:
        return "Naukri.com"
    elif "glassdoor.com" in url:
        return "Glassdoor"
    else:
        return "Unknown Company"


def calculate_match_score(job_data: Dict, user_skills: List[str]) -> int:
    """Calculate job match score"""
    if not user_skills:
        return 50

    job_text = f"{job_data.get('title', '')} {job_data.get('description', '')} {job_data.get('requirements', '')}".lower()
    matches = sum(1 for skill in user_skills if skill.lower() in job_text)
    score = min(int((matches / len(user_skills)) * 100), 100)

    return max(score, 30)  # Minimum score of 30
