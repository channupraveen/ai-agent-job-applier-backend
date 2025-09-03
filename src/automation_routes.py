"""
Automation Control API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio

from .auth import get_current_user
from .models import get_job_db, UserProfile as User

router = APIRouter(tags=["Automation Control"])


class AutomationStartRequest(BaseModel):
    keywords: Optional[str] = None
    max_applications: int = 10
    job_sources: List[str] = ["linkedin", "indeed", "naukri"]
    auto_apply: bool = False
    filters: Optional[Dict[str, Any]] = None


class ScheduleRequest(BaseModel):
    schedule_type: str  # daily, weekly, once
    start_time: str  # HH:MM format
    days_of_week: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    max_applications: int = 10
    is_active: bool = True


# Global automation state
automation_sessions = {}


@router.post("/agent/start")
async def start_automation_session(
    automation_request: AutomationStartRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Start automated job application session"""
    # try-except block added below
    try:
        # Check if user already has active session
        if current_user.id in automation_sessions:
            current_session = automation_sessions[current_user.id]
            if current_session.get("status") == "running":
                return {
                    "success": False,
                    "message": "Automation session already running",
                    "session_id": current_session["session_id"],
                }

        # Create new session in database
        session_insert = """
        INSERT INTO application_sessions (
            started_at, keywords, status, jobs_found, jobs_applied, jobs_skipped, errors
        ) VALUES (
            :started_at, :keywords, 'running', 0, 0, 0, 0
        ) RETURNING id
        """

        session_params = {
            "started_at": datetime.utcnow(),
            "keywords": automation_request.keywords or "python developer",
        }

        session_result = db.execute(text(session_insert), session_params)
        session_id = session_result.fetchone()[0]
        db.commit()

        # Store session in memory
        automation_sessions[current_user.id] = {
            "session_id": session_id,
            "status": "running",
            "started_at": datetime.utcnow(),
            "progress": {
                "jobs_found": 0,
                "jobs_applied": 0,
                "jobs_skipped": 0,
                "errors": 0,
            },
            "current_action": "Initializing automation...",
            "max_applications": automation_request.max_applications,
        }

        # Start automation in background
        background_tasks.add_task(
            run_automation_process, current_user.id, session_id, automation_request, db
        )

        return {
            "success": True,
            "message": "Automation session started successfully",
            "session_id": session_id,
            "max_applications": automation_request.max_applications,
            "estimated_duration": f"{automation_request.max_applications * 2} minutes",
            "job_sources": automation_request.job_sources,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error starting automation: {str(e)}"
        )


@router.post("/agent/stop")
async def stop_automation_session(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_job_db)
):
    """Stop current automation session"""
    try:
        if current_user.id not in automation_sessions:
            raise HTTPException(
                status_code=404, detail="No active automation session found"
            )

        session_data = automation_sessions[current_user.id]
        session_id = session_data["session_id"]

        # Update session status in database
        update_query = """
       UPDATE application_sessions 
       SET status = 'stopped', ended_at = :ended_at,
           jobs_found = :jobs_found, jobs_applied = :jobs_applied,
           jobs_skipped = :jobs_skipped, errors = :errors
       WHERE id = :session_id
       """

        progress = session_data["progress"]
        update_params = {
            "session_id": session_id,
            "ended_at": datetime.utcnow(),
            "jobs_found": progress["jobs_found"],
            "jobs_applied": progress["jobs_applied"],
            "jobs_skipped": progress["jobs_skipped"],
            "errors": progress["errors"],
        }

        db.execute(text(update_query), update_params)
        db.commit()

        # Update memory state
        automation_sessions[current_user.id]["status"] = "stopped"
        automation_sessions[current_user.id]["ended_at"] = datetime.utcnow()

        return {
            "success": True,
            "message": "Automation session stopped successfully",
            "session_id": session_id,
            "final_stats": progress,
            "duration": str(datetime.utcnow() - session_data["started_at"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error stopping automation: {str(e)}"
        )


@router.get("/agent/status")
async def get_automation_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_job_db)
):
    """Get real-time automation status"""
    try:
        # Check memory first for real-time data
        if current_user.id in automation_sessions:
            session_data = automation_sessions[current_user.id]

            # Calculate progress percentage
            progress_pct = 0
            if session_data["max_applications"] > 0:
                progress_pct = min(
                    int(
                        (
                            session_data["progress"]["jobs_applied"]
                            / session_data["max_applications"]
                        )
                        * 100
                    ),
                    100,
                )

            return {
                "success": True,
                "session_active": True,
                "session_id": session_data["session_id"],
                "status": session_data["status"],
                "started_at": session_data["started_at"].isoformat(),
                "current_action": session_data.get("current_action", "Processing..."),
                "progress": session_data["progress"],
                "progress_percentage": progress_pct,
                "max_applications": session_data["max_applications"],
                "estimated_time_remaining": calculate_time_remaining(session_data),
            }

        # Check database for recent sessions
        recent_query = """
       SELECT id, started_at, ended_at, status, jobs_found, jobs_applied, 
              jobs_skipped, errors, keywords
       FROM application_sessions
       ORDER BY started_at DESC
       LIMIT 1
       """

        result = db.execute(text(recent_query))
        recent_session = result.fetchone()

        if recent_session:
            session_dict = dict(recent_session._mapping)
            session_dict["started_at"] = session_dict["started_at"].isoformat()
            if session_dict["ended_at"]:
                session_dict["ended_at"] = session_dict["ended_at"].isoformat()

            return {
                "success": True,
                "session_active": False,
                "last_session": session_dict,
            }

        return {
            "success": True,
            "session_active": False,
            "message": "No automation sessions found",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.post("/agent/schedule")
async def schedule_automation_runs(
    schedule_request: ScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Schedule automation to run automatically"""
    try:
        # For now, store schedule preferences in user profile
        # In a full implementation, you'd use a task queue like Celery

        schedule_data = {
            "schedule_type": schedule_request.schedule_type,
            "start_time": schedule_request.start_time,
            "days_of_week": schedule_request.days_of_week,
            "max_applications": schedule_request.max_applications,
            "is_active": schedule_request.is_active,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Store in user preferences (you could create a separate schedules table)
        update_query = """
       UPDATE user_profiles 
       SET preferred_job_types = :schedule_data, updated_at = :updated_at
       WHERE id = :user_id
       """

        # This is a simplified implementation - in production you'd want a proper schedules table
        db.execute(
            text(update_query),
            {
                "schedule_data": json.dumps({"automation_schedule": schedule_data}),
                "updated_at": datetime.utcnow(),
                "user_id": current_user.id,
            },
        )
        db.commit()

        return {
            "success": True,
            "message": f"Automation scheduled for {schedule_request.schedule_type} runs",
            "schedule": schedule_data,
            "note": "Schedule saved. Automatic execution requires background worker setup.",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error scheduling automation: {str(e)}"
        )


@router.get("/agent/logs")
async def get_automation_logs(
    session_id: Optional[int] = Query(None, description="Specific session ID"),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get detailed automation logs"""
    try:
        base_query = """
       SELECT al.id, al.session_id, al.action, al.message, al.details,
              al.error_type, al.error_details, al.timestamp,
              jas.keywords, jas.started_at as session_started
       FROM application_logs al
       LEFT JOIN application_sessions jas ON al.session_id = jas.id
       WHERE 1=1
       """

        params = {"limit": limit}
        conditions = []

        if session_id:
            conditions.append("al.session_id = :session_id")
            params["session_id"] = session_id

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        final_query = f"""
       {base_query}
       ORDER BY al.timestamp DESC
       LIMIT :limit
       """

        result = db.execute(text(final_query), params)
        logs = []

        for row in result.fetchall():
            log_dict = dict(row._mapping)
            log_dict["timestamp"] = log_dict["timestamp"].isoformat()
            if log_dict["session_started"]:
                log_dict["session_started"] = log_dict["session_started"].isoformat()

            # Parse details JSON if present
            if log_dict["details"]:
                try:
                    log_dict["details"] = json.loads(log_dict["details"])
                except:
                    pass  # Keep as string if not valid JSON

            logs.append(log_dict)

        return {
            "success": True,
            "logs": logs,
            "total_logs": len(logs),
            "session_id": session_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")


@router.get("/agent/sessions")
async def get_automation_sessions(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Get list of all automation sessions"""
    try:
        query = """
       SELECT id, started_at, ended_at, keywords, jobs_found, jobs_applied,
              jobs_skipped, errors, status
       FROM application_sessions
       ORDER BY started_at DESC
       LIMIT :limit
       """

        result = db.execute(text(query), {"limit": limit})
        sessions = []

        for row in result.fetchall():
            session_dict = dict(row._mapping)
            session_dict["started_at"] = session_dict["started_at"].isoformat()
            if session_dict["ended_at"]:
                session_dict["ended_at"] = session_dict["ended_at"].isoformat()
                # Calculate duration
                duration = datetime.fromisoformat(
                    session_dict["ended_at"]
                ) - datetime.fromisoformat(session_dict["started_at"])
                session_dict["duration"] = str(duration)

            # Calculate success rate
            total_jobs = session_dict.get("jobs_found", 0)
            applied_jobs = session_dict.get("jobs_applied", 0)
            session_dict["success_rate"] = round(
                (applied_jobs / max(total_jobs, 1)) * 100, 1
            )

            sessions.append(session_dict)

        return {"success": True, "sessions": sessions, "total_sessions": len(sessions)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sessions: {str(e)}")


@router.delete("/agent/sessions/{session_id}")
async def delete_automation_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_job_db),
):
    """Delete automation session and its logs"""
    try:
        # Check if session exists
        check_query = "SELECT status FROM application_sessions WHERE id = :session_id"
        existing = db.execute(text(check_query), {"session_id": session_id}).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Session not found")

        if existing[0] == "running":
            raise HTTPException(
                status_code=400, detail="Cannot delete running session. Stop it first."
            )

        # Delete logs first (foreign key constraint)
        db.execute(
            text("DELETE FROM application_logs WHERE session_id = :session_id"),
            {"session_id": session_id},
        )

        # Delete session
        db.execute(
            text("DELETE FROM application_sessions WHERE id = :session_id"),
            {"session_id": session_id},
        )

        db.commit()

        # Remove from memory if present
        if current_user.id in automation_sessions:
            if automation_sessions[current_user.id]["session_id"] == session_id:
                del automation_sessions[current_user.id]

        return {
            "success": True,
            "message": f"Session {session_id} and its logs deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


# Helper functions
async def run_automation_process(
    user_id: int, session_id: int, request: AutomationStartRequest, db: Session
):
    """Background automation process"""
    try:
        session_data = automation_sessions[user_id]

        # Simulate automation process
        for i in range(request.max_applications):
            if session_data["status"] == "stopped":
                break

            # Update current action
            session_data["current_action"] = (
                f"Processing job {i+1} of {request.max_applications}"
            )

            # Simulate job processing
            await asyncio.sleep(2)  # Simulate processing time

            # Update progress
            session_data["progress"]["jobs_found"] += 1
            if i % 2 == 0:  # Simulate applying to every other job
                session_data["progress"]["jobs_applied"] += 1
            else:
                session_data["progress"]["jobs_skipped"] += 1

        # Mark as completed
        session_data["status"] = "completed"
        session_data["current_action"] = "Automation completed"
        session_data["ended_at"] = datetime.utcnow()

        # Update database
        update_query = """
       UPDATE application_sessions 
       SET status = 'completed', ended_at = :ended_at,
           jobs_found = :jobs_found, jobs_applied = :jobs_applied,
           jobs_skipped = :jobs_skipped
       WHERE id = :session_id
       """

        progress = session_data["progress"]
        db.execute(
            text(update_query),
            {
                "session_id": session_id,
                "ended_at": datetime.utcnow(),
                "jobs_found": progress["jobs_found"],
                "jobs_applied": progress["jobs_applied"],
                "jobs_skipped": progress["jobs_skipped"],
            },
        )
        db.commit()

    except Exception as e:
        # Mark as error
        if user_id in automation_sessions:
            automation_sessions[user_id]["status"] = "error"
            automation_sessions[user_id]["current_action"] = f"Error: {str(e)}"


def calculate_time_remaining(session_data: Dict) -> str:
    """Calculate estimated time remaining for automation"""
    try:
        progress = session_data["progress"]
        max_apps = session_data["max_applications"]
        applied = progress["jobs_applied"]

        if applied == 0:
            return "Calculating..."

        # Estimate based on current progress
        elapsed_minutes = (
            datetime.utcnow() - session_data["started_at"]
        ).total_seconds() / 60
        avg_time_per_job = elapsed_minutes / applied
        remaining_jobs = max_apps - applied
        remaining_minutes = int(remaining_jobs * avg_time_per_job)

        if remaining_minutes < 1:
            return "Less than 1 minute"
        elif remaining_minutes < 60:
            return f"{remaining_minutes} minutes"
        else:
            hours = remaining_minutes // 60
            minutes = remaining_minutes % 60
            return f"{hours}h {minutes}m"
    except:
        return "Unknown"
