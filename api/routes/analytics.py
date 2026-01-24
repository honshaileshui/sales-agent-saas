"""
Analytics Routes
================
Dashboard stats, performance metrics, and agent run history.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.models import DashboardStats, AgentRunResponse, SuccessResponse
from api.auth import get_current_user
from database import (
    LeadDB, AgentRunDB, get_db_cursor, get_dashboard_stats
)

router = APIRouter()


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get("/dashboard")
async def get_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """
    Get dashboard statistics overview.
    
    Returns key metrics for the main dashboard view.
    """
    user_id = str(current_user["id"])
    
    # Get basic stats
    stats = get_dashboard_stats(user_id)
    
    # Get email stats
    with get_db_cursor(commit=False) as cursor:
        # Total emails sent
        cursor.execute("""
            SELECT COUNT(*) as sent FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s AND e.status = 'sent'
        """, (user_id,))
        emails_sent = cursor.fetchone()["sent"]
        
        # Total opens
        cursor.execute("""
            SELECT COALESCE(SUM(e.open_count), 0) as opens FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s
        """, (user_id,))
        total_opens = cursor.fetchone()["opens"]
        
        # Total replies (leads with replied status)
        cursor.execute("""
            SELECT COUNT(*) as replies FROM leads
            WHERE user_id = %s AND status = 'replied'
        """, (user_id,))
        total_replies = cursor.fetchone()["replies"]
        
        # Campaign counts
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active
            FROM email_campaigns WHERE user_id = %s
        """, (user_id,))
        campaign_stats = cursor.fetchone()
    
    # Calculate rates
    open_rate = (total_opens / emails_sent * 100) if emails_sent > 0 else 0
    reply_rate = (total_replies / emails_sent * 100) if emails_sent > 0 else 0
    
    return {
        "total_leads": stats["leads"]["total"],
        "leads_by_status": stats["leads"]["by_status"],
        "total_emails_sent": emails_sent,
        "total_opens": total_opens,
        "total_replies": total_replies,
        "open_rate": round(open_rate, 1),
        "reply_rate": round(reply_rate, 1),
        "total_campaigns": campaign_stats["total"],
        "active_campaigns": campaign_stats["active"]
    }


# ============================================================================
# AGENT RUNS
# ============================================================================

@router.get("/runs")
async def list_agent_runs(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get history of agent runs."""
    user_id = str(current_user["id"])
    
    runs = AgentRunDB.get_recent(user_id, limit=limit)
    
    return {
        "runs": [
            {
                "id": str(r["id"]),
                "run_id": r["run_id"],
                "started_at": r["started_at"],
                "ended_at": r.get("ended_at"),
                "duration_seconds": r.get("duration_seconds"),
                "leads_processed": r.get("leads_processed", 0),
                "leads_skipped": r.get("leads_skipped", 0),
                "leads_failed": r.get("leads_failed", 0),
                "success_rate": float(r.get("success_rate", 0) or 0),
                "status": r["status"]
            }
            for r in runs
        ]
    }


@router.get("/runs/{run_id}")
async def get_agent_run(
    run_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get details of a specific agent run."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT * FROM agent_runs WHERE run_id = %s",
            (run_id,)
        )
        run = cursor.fetchone()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if str(run["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": str(run["id"]),
        "run_id": run["run_id"],
        "started_at": run["started_at"],
        "ended_at": run.get("ended_at"),
        "duration_seconds": run.get("duration_seconds"),
        "leads_processed": run.get("leads_processed", 0),
        "leads_skipped": run.get("leads_skipped", 0),
        "leads_failed": run.get("leads_failed", 0),
        "research_successes": run.get("research_successes", 0),
        "research_failures": run.get("research_failures", 0),
        "email_gen_successes": run.get("email_gen_successes", 0),
        "email_gen_failures": run.get("email_gen_failures", 0),
        "success_rate": float(run.get("success_rate", 0) or 0),
        "avg_lead_processing_time": float(run.get("avg_lead_processing_time", 0) or 0),
        "config_snapshot": run.get("config_snapshot"),
        "errors": run.get("errors", []),
        "status": run["status"]
    }


# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

@router.get("/performance")
async def get_performance_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Get performance metrics over time."""
    user_id = str(current_user["id"])
    start_date = datetime.utcnow() - timedelta(days=days)
    
    with get_db_cursor(commit=False) as cursor:
        # Leads added over time
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM leads
            WHERE user_id = %s AND created_at >= %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (user_id, start_date))
        leads_over_time = [{"date": str(r["date"]), "count": r["count"]} 
                          for r in cursor.fetchall()]
        
        # Emails sent over time
        cursor.execute("""
            SELECT DATE(e.sent_at) as date, COUNT(*) as count
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s AND e.sent_at >= %s AND e.sent_at IS NOT NULL
            GROUP BY DATE(e.sent_at)
            ORDER BY date
        """, (user_id, start_date))
        emails_over_time = [{"date": str(r["date"]), "count": r["count"]} 
                           for r in cursor.fetchall()]
        
        # Success rate over time (from agent runs)
        cursor.execute("""
            SELECT DATE(started_at) as date, AVG(success_rate) as avg_rate
            FROM agent_runs
            WHERE user_id = %s AND started_at >= %s AND status = 'completed'
            GROUP BY DATE(started_at)
            ORDER BY date
        """, (user_id, start_date))
        success_rate_over_time = [
            {"date": str(r["date"]), "rate": float(r["avg_rate"] or 0)} 
            for r in cursor.fetchall()
        ]
    
    # Calculate summary metrics
    summary = AgentRunDB.get_summary_stats(user_id)
    
    return {
        "period_days": days,
        "leads_over_time": leads_over_time,
        "emails_over_time": emails_over_time,
        "success_rate_over_time": success_rate_over_time,
        "summary": {
            "total_runs": summary.get("total_runs", 0),
            "total_leads_processed": summary.get("total_leads_processed", 0),
            "avg_success_rate": float(summary.get("avg_success_rate", 0) or 0),
            "avg_processing_time": float(summary.get("avg_processing_time", 0) or 0)
        }
    }


# ============================================================================
# AGENT CONTROL
# ============================================================================

@router.post("/run-agent")
async def trigger_agent_run(
    background_tasks: BackgroundTasks,
    limit: int = Query(50, ge=1, le=200, description="Max leads to process"),
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger the sales agent to process unprocessed leads.
    
    Runs in background and returns immediately.
    """
    user_id = str(current_user["id"])
    
    # Check for unprocessed leads
    unprocessed = LeadDB.get_unprocessed(user_id, limit=1)
    
    if not unprocessed:
        return {
            "success": False,
            "message": "No unprocessed leads found",
            "leads_available": 0
        }
    
    # Count total unprocessed
    all_unprocessed = LeadDB.get_unprocessed(user_id, limit=limit)
    
    # TODO: Add background task to run the agent
    # For now, provide instructions to run manually
    
    return {
        "success": True,
        "message": f"Found {len(all_unprocessed)} leads ready for processing",
        "leads_available": len(all_unprocessed),
        "instructions": "Run 'python sales_agent.py' in terminal to process leads",
        "note": "Background processing will be added in a future update"
    }


@router.get("/run-status")
async def get_current_run_status(
    current_user: dict = Depends(get_current_user)
):
    """Check if agent is currently running."""
    user_id = str(current_user["id"])
    
    # Check for running status
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT * FROM agent_runs 
            WHERE user_id = %s AND status = 'running'
            ORDER BY started_at DESC LIMIT 1
        """, (user_id,))
        running = cursor.fetchone()
    
    if running:
        return {
            "is_running": True,
            "run_id": running["run_id"],
            "started_at": running["started_at"],
            "leads_processed": running.get("leads_processed", 0)
        }
    
    return {
        "is_running": False,
        "last_run": None
    }


# ============================================================================
# EXPORT
# ============================================================================

@router.get("/export/leads")
async def export_leads_data(
    format: str = Query("json", description="Export format: json or csv"),
    current_user: dict = Depends(get_current_user)
):
    """Export all leads data."""
    user_id = str(current_user["id"])
    
    leads = LeadDB.get_all_for_user(user_id, limit=10000)
    
    if format == "csv":
        # Return CSV formatted data
        import io
        import csv
        
        output = io.StringIO()
        if leads:
            fieldnames = ['name', 'email', 'company', 'job_title', 'status', 'priority', 'created_at']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for lead in leads:
                row = {k: str(lead.get(k, '')) for k in fieldnames}
                writer.writerow(row)
        
        return {
            "format": "csv",
            "data": output.getvalue(),
            "count": len(leads)
        }
    
    # Default: JSON
    return {
        "format": "json",
        "data": [
            {
                "id": str(l["id"]),
                "name": l["name"],
                "email": l["email"],
                "company": l["company"],
                "job_title": l.get("job_title"),
                "status": l["status"],
                "priority": l["priority"],
                "created_at": str(l["created_at"]),
                "updated_at": str(l["updated_at"])
            }
            for l in leads
        ],
        "count": len(leads)
    }


@router.get("/export/emails")
async def export_emails_data(
    current_user: dict = Depends(get_current_user)
):
    """Export all generated emails."""
    user_id = str(current_user["id"])
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT e.*, l.name as lead_name, l.email as lead_email, l.company
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s AND e.is_current = TRUE
            ORDER BY e.created_at DESC
        """, (user_id,))
        emails = [dict(row) for row in cursor.fetchall()]
    
    return {
        "format": "json",
        "data": [
            {
                "lead_name": e["lead_name"],
                "lead_email": e["lead_email"],
                "company": e["company"],
                "subject": e.get("subject"),
                "body": e["body"],
                "status": e["status"],
                "created_at": str(e["created_at"])
            }
            for e in emails
        ],
        "count": len(emails)
    }
