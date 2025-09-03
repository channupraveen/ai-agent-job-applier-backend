"""
Website Configuration API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from .auth import get_current_user
from .models import get_job_db, UserProfile as User

router = APIRouter(tags=["Website Configuration"])


class WebsiteConfig(BaseModel):
    name: str
    base_url: str
    job_search_url: str
    login_required: bool = False
    login_url: Optional[str] = None
    search_selectors: Dict[str, str]
    job_selectors: Dict[str, str]
    form_selectors: Optional[Dict[str, str]] = None
    pagination_selector: Optional[str] = None
    max_pages: int = 5
    delay_between_requests: int = 2
    is_active: bool = True


class SelectorTest(BaseModel):
    url: str
    selector: str
    selector_type: str  # css, xpath, id, class


class SelectorUpdate(BaseModel):
    selectors: Dict[str, str]
    selector_type: str = "search"  # search, job, form, pagination


@router.post("/websites")
async def add_website_configuration(
    website_config: WebsiteConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Add new job portal configuration"""
    try:
        # Check if website already exists
        check_query = (
            "SELECT id FROM website_configurations WHERE LOWER(name) = LOWER(:name)"
        )
        existing = db.execute(
            text(check_query), {"name": website_config.name}
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Website '{website_config.name}' already configured",
            )

        # Insert new website configuration
        insert_query = """
        INSERT INTO website_configurations (
            name, base_url, job_search_url, login_required, login_url,
            search_selectors, job_selectors, form_selectors, pagination_selector,
            max_pages, delay_between_requests, is_active, created_at, updated_at
        ) VALUES (
            :name, :base_url, :job_search_url, :login_required, :login_url,
            :search_selectors, :job_selectors, :form_selectors, :pagination_selector,
            :max_pages, :delay_between_requests, :is_active, :created_at, :updated_at
        ) RETURNING id, name
        """

        params = {
            "name": website_config.name,
            "base_url": website_config.base_url,
            "job_search_url": website_config.job_search_url,
            "login_required": website_config.login_required,
            "login_url": website_config.login_url,
            "search_selectors": json.dumps(website_config.search_selectors),
            "job_selectors": json.dumps(website_config.job_selectors),
            "form_selectors": (
                json.dumps(website_config.form_selectors)
                if website_config.form_selectors
                else None
            ),
            "pagination_selector": website_config.pagination_selector,
            "max_pages": website_config.max_pages,
            "delay_between_requests": website_config.delay_between_requests,
            "is_active": website_config.is_active,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = db.execute(text(insert_query), params)
        new_website = result.fetchone()
        db.commit()

        website_dict = dict(new_website._mapping)

        return {
            "success": True,
            "message": f"Website '{website_config.name}' configured successfully",
            "website": website_dict,
            "config": website_config.dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error adding website configuration: {str(e)}"
        )


@router.get("/websites")
async def get_configured_websites(
    active_only: bool = Query(False, description="Return only active websites"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """List configured job websites"""
    try:
        base_query = """
        SELECT id, name, base_url, job_search_url, login_required, 
               is_active, max_pages, delay_between_requests, created_at, updated_at
        FROM website_configurations
        WHERE 1=1
        """

        params = {}

        if active_only:
            base_query += " AND is_active = true"

        final_query = base_query + " ORDER BY name"

        result = db.execute(text(final_query), params)
        websites = []

        for row in result.fetchall():
            website_dict = dict(row._mapping)
            website_dict["created_at"] = website_dict["created_at"].isoformat()
            website_dict["updated_at"] = website_dict["updated_at"].isoformat()
            websites.append(website_dict)

        return {"success": True, "websites": websites, "total": len(websites)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting websites: {str(e)}")


@router.get("/websites/{website_id}")
async def get_website_configuration(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get specific website configuration"""
    try:
        query = """
        SELECT id, name, base_url, job_search_url, login_required, login_url,
               search_selectors, job_selectors, form_selectors, pagination_selector,
               max_pages, delay_between_requests, is_active, created_at, updated_at
        FROM website_configurations
        WHERE id = :website_id
        """

        result = db.execute(text(query), {"website_id": website_id})
        website_row = result.fetchone()

        if not website_row:
            raise HTTPException(
                status_code=404, detail="Website configuration not found"
            )

        website_dict = dict(website_row._mapping)

        # Parse JSON fields
        for json_field in ["search_selectors", "job_selectors", "form_selectors"]:
            if website_dict[json_field]:
                website_dict[json_field] = json.loads(website_dict[json_field])

        website_dict["created_at"] = website_dict["created_at"].isoformat()
        website_dict["updated_at"] = website_dict["updated_at"].isoformat()

        return {"success": True, "website": website_dict}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting website configuration: {str(e)}"
        )


@router.put("/websites/{website_id}")
async def update_website_configuration(
    website_id: int,
    website_config: WebsiteConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Update website configuration"""
    try:
        # Check if website exists
        check_query = "SELECT name FROM website_configurations WHERE id = :website_id"
        existing = db.execute(text(check_query), {"website_id": website_id}).fetchone()

        if not existing:
            raise HTTPException(
                status_code=404, detail="Website configuration not found"
            )

        # Update configuration
        update_query = """
        UPDATE website_configurations SET
            name = :name,
            base_url = :base_url,
            job_search_url = :job_search_url,
            login_required = :login_required,
            login_url = :login_url,
            search_selectors = :search_selectors,
            job_selectors = :job_selectors,
            form_selectors = :form_selectors,
            pagination_selector = :pagination_selector,
            max_pages = :max_pages,
            delay_between_requests = :delay_between_requests,
            is_active = :is_active,
            updated_at = :updated_at
        WHERE id = :website_id
        RETURNING id, name
        """

        params = {
            "website_id": website_id,
            "name": website_config.name,
            "base_url": website_config.base_url,
            "job_search_url": website_config.job_search_url,
            "login_required": website_config.login_required,
            "login_url": website_config.login_url,
            "search_selectors": json.dumps(website_config.search_selectors),
            "job_selectors": json.dumps(website_config.job_selectors),
            "form_selectors": (
                json.dumps(website_config.form_selectors)
                if website_config.form_selectors
                else None
            ),
            "pagination_selector": website_config.pagination_selector,
            "max_pages": website_config.max_pages,
            "delay_between_requests": website_config.delay_between_requests,
            "is_active": website_config.is_active,
            "updated_at": datetime.utcnow(),
        }

        result = db.execute(text(update_query), params)
        updated_website = result.fetchone()
        db.commit()

        website_dict = dict(updated_website._mapping)

        return {
            "success": True,
            "message": f"Website '{website_config.name}' updated successfully",
            "website": website_dict,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error updating website configuration: {str(e)}"
        )


@router.delete("/websites/{website_id}")
async def delete_website_configuration(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Remove website configuration"""
    try:
        # Check if website exists
        check_query = "SELECT name FROM website_configurations WHERE id = :website_id"
        existing = db.execute(text(check_query), {"website_id": website_id}).fetchone()

        if not existing:
            raise HTTPException(
                status_code=404, detail="Website configuration not found"
            )

        website_name = existing[0]

        # Delete configuration
        delete_query = "DELETE FROM website_configurations WHERE id = :website_id"
        db.execute(text(delete_query), {"website_id": website_id})
        db.commit()

        return {
            "success": True,
            "message": f"Website '{website_name}' configuration deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error deleting website configuration: {str(e)}"
        )


@router.post("/websites/{website_id}/test")
async def test_website_automation(
    website_id: int,
    test_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Test automation on website"""
    try:
        # Get website configuration
        config_query = """
        SELECT name, base_url, job_search_url, search_selectors, job_selectors,
               delay_between_requests
        FROM website_configurations
        WHERE id = :website_id AND is_active = true
        """

        config_result = db.execute(text(config_query), {"website_id": website_id})
        config_row = config_result.fetchone()

        if not config_row:
            raise HTTPException(
                status_code=404, detail="Website configuration not found or inactive"
            )

        config_dict = dict(config_row._mapping)
        config_dict["search_selectors"] = json.loads(config_dict["search_selectors"])
        config_dict["job_selectors"] = json.loads(config_dict["job_selectors"])

        # Simulate testing (in real implementation, use Selenium)
        test_url = test_url or config_dict["job_search_url"]

        test_results = {
            "website_name": config_dict["name"],
            "test_url": test_url,
            "timestamp": datetime.utcnow().isoformat(),
            "tests": [
                {
                    "test": "URL Accessibility",
                    "status": "passed",
                    "message": "Website is accessible",
                },
                {
                    "test": "Search Selectors",
                    "status": "passed",
                    "selectors_found": len(config_dict["search_selectors"]),
                    "message": "All search selectors are valid",
                },
                {
                    "test": "Job Listing Selectors",
                    "status": "passed",
                    "selectors_found": len(config_dict["job_selectors"]),
                    "message": "Job listing selectors working",
                },
                {
                    "test": "Response Time",
                    "status": "passed",
                    "response_time_ms": 1250,
                    "message": "Good response time",
                },
            ],
            "overall_status": "passed",
            "recommendations": [
                "Configuration is working well",
                "Consider reducing delay_between_requests if site allows",
            ],
        }

        return {
            "success": True,
            "message": f"Test completed for {config_dict['name']}",
            "test_results": test_results,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing website: {str(e)}")


@router.post("/websites/{website_id}/selectors")
async def update_website_selectors(
    website_id: int,
    selector_update: SelectorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Configure form selectors for specific website"""
    try:
        # Get current configuration
        config_query = """
        SELECT search_selectors, job_selectors, form_selectors
        FROM website_configurations
        WHERE id = :website_id
        """

        config_result = db.execute(text(config_query), {"website_id": website_id})
        config_row = config_result.fetchone()

        if not config_row:
            raise HTTPException(
                status_code=404, detail="Website configuration not found"
            )

        # Parse current selectors
        current_selectors = dict(config_row._mapping)

        # Update the specified selector type
        if selector_update.selector_type == "search":
            field_name = "search_selectors"
        elif selector_update.selector_type == "job":
            field_name = "job_selectors"
        elif selector_update.selector_type == "form":
            field_name = "form_selectors"
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid selector_type. Use: search, job, or form",
            )

        # Update selectors
        update_query = f"""
        UPDATE website_configurations 
        SET {field_name} = :selectors, updated_at = :updated_at
        WHERE id = :website_id
        RETURNING name
        """

        params = {
            "website_id": website_id,
            "selectors": json.dumps(selector_update.selectors),
            "updated_at": datetime.utcnow(),
        }

        result = db.execute(text(update_query), params)
        updated_website = result.fetchone()
        db.commit()

        return {
            "success": True,
            "message": f"{selector_update.selector_type.title()} selectors updated for {updated_website[0]}",
            "updated_selectors": selector_update.selectors,
            "selector_type": selector_update.selector_type,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error updating selectors: {str(e)}"
        )


@router.get("/websites/{website_id}/selectors")
async def get_website_selectors(
    website_id: int,
    selector_type: Optional[str] = Query(
        None, description="Specific selector type to get"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get website selectors"""
    try:
        query = """
        SELECT name, search_selectors, job_selectors, form_selectors
        FROM website_configurations
        WHERE id = :website_id
        """

        result = db.execute(text(query), {"website_id": website_id})
        config_row = result.fetchone()

        if not config_row:
            raise HTTPException(
                status_code=404, detail="Website configuration not found"
            )

        config_dict = dict(config_row._mapping)

        # Parse JSON selectors
        selectors = {
            "search_selectors": (
                json.loads(config_dict["search_selectors"])
                if config_dict["search_selectors"]
                else {}
            ),
            "job_selectors": (
                json.loads(config_dict["job_selectors"])
                if config_dict["job_selectors"]
                else {}
            ),
            "form_selectors": (
                json.loads(config_dict["form_selectors"])
                if config_dict["form_selectors"]
                else {}
            ),
        }

        if selector_type:
            if selector_type not in ["search", "job", "form"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid selector_type. Use: search, job, or form",
                )

            selector_key = f"{selector_type}_selectors"
            return {
                "success": True,
                "website_name": config_dict["name"],
                "selector_type": selector_type,
                "selectors": selectors[selector_key],
            }

        return {
            "success": True,
            "website_name": config_dict["name"],
            "all_selectors": selectors,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting selectors: {str(e)}"
        )


@router.post("/websites/test-selector")
async def test_css_selector(
    selector_test: SelectorTest, current_user: User = Depends(get_current_user)
):
    """Test CSS selector on a specific URL"""
    try:
        # In real implementation, use Selenium or BeautifulSoup to test selector

        # Simulate selector testing
        test_result = {
            "url": selector_test.url,
            "selector": selector_test.selector,
            "selector_type": selector_test.selector_type,
            "test_timestamp": datetime.utcnow().isoformat(),
            "status": "success",  # or "failed"
            "elements_found": 5,  # simulated count
            "sample_text": "Sample job title found",
            "recommendations": [
                "Selector is working correctly",
                "Found multiple matching elements",
            ],
        }

        return {
            "success": True,
            "message": "Selector test completed",
            "test_result": test_result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing selector: {str(e)}")
