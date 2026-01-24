"""
Dashboard API - FRESH BUILD
============================
Clean dashboard API that works with your exact database structure.

Author: Shailesh Hon
Version: 3.0 (Fresh Build)
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def get_current_user_optional():
    """
    Optional auth - returns None if not authenticated.
    This allows dashboard to work even without login for testing.
    """
    async def _get_user(request):
        from fastapi import Request
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        try:
            from api.auth import decode_token
            token = auth_header.replace("Bearer ", "")
            payload = decode_token(token)
            if payload:
                return {"id": payload.get("sub")}
        except:
            pass
        return None
    return _get_user


@router.get("/stats")
async def get_dashboard_stats(user_id: Optional[str] = None):
    """
    Get dashboard statistics.
    Works with or without authentication.
    """
    from database import get_db_cursor
    
    try:
        with get_db_cursor(commit=False) as cursor:
            # Get total leads count
            if user_id:
                cursor.execute("SELECT COUNT(*) as count FROM leads WHERE user_id = %s", (user_id,))
            else:
                cursor.execute("SELECT COUNT(*) as count FROM leads")
            total_leads = cursor.fetchone()["count"]
            
            # Get leads by status
            if user_id:
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM leads 
                    WHERE user_id = %s
                    GROUP BY status
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM leads 
                    GROUP BY status
                """)
            status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            # Get email statistics
            if user_id:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_emails,
                        COUNT(CASE WHEN sent_at IS NOT NULL THEN 1 END) as sent,
                        COUNT(CASE WHEN opened_at IS NOT NULL OR open_count > 0 THEN 1 END) as opened,
                        COUNT(CASE WHEN click_count > 0 THEN 1 END) as clicked,
                        COUNT(CASE WHEN bounced = TRUE THEN 1 END) as bounced,
                        COALESCE(SUM(open_count), 0) as total_opens,
                        COALESCE(SUM(click_count), 0) as total_clicks
                    FROM generated_emails e
                    JOIN leads l ON e.lead_id = l.id
                    WHERE l.user_id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_emails,
                        COUNT(CASE WHEN sent_at IS NOT NULL THEN 1 END) as sent,
                        COUNT(CASE WHEN opened_at IS NOT NULL OR open_count > 0 THEN 1 END) as opened,
                        COUNT(CASE WHEN click_count > 0 THEN 1 END) as clicked,
                        COUNT(CASE WHEN bounced = TRUE THEN 1 END) as bounced,
                        COALESCE(SUM(open_count), 0) as total_opens,
                        COALESCE(SUM(click_count), 0) as total_clicks
                    FROM generated_emails
                """)
            
            email_stats = cursor.fetchone()
            
            total_emails = email_stats["total_emails"] or 0
            sent = email_stats["sent"] or 0
            opened = email_stats["opened"] or 0
            clicked = email_stats["clicked"] or 0
            bounced = email_stats["bounced"] or 0
            
            # Calculate rates (avoid division by zero)
            sent_for_calc = sent if sent > 0 else 1
            open_rate = round((opened / sent_for_calc) * 100, 1) if sent > 0 else 0
            click_rate = round((clicked / sent_for_calc) * 100, 1) if sent > 0 else 0
            bounce_rate = round((bounced / sent_for_calc) * 100, 1) if sent > 0 else 0
            
            # Get recent activity (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM leads 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """)
            new_leads_7_days = cursor.fetchone()["count"]
            
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM generated_emails 
                WHERE sent_at >= NOW() - INTERVAL '7 days'
            """)
            emails_sent_7_days = cursor.fetchone()["count"]
        
        return {
            "success": True,
            "stats": {
                "total_leads": total_leads,
                "total_emails": total_emails,
                "total_emails_sent": sent,
                "total_opened": opened,
                "total_clicked": clicked,
                "total_bounced": bounced,
                "open_rate": open_rate,
                "click_rate": click_rate,
                "bounce_rate": bounce_rate,
                "total_opens": email_stats["total_opens"] or 0,
                "total_clicks": email_stats["total_clicks"] or 0,
                "leads_by_status": status_counts,
                "recent_activity": {
                    "new_leads_last_7_days": new_leads_7_days,
                    "emails_sent_last_7_days": emails_sent_7_days
                }
            },
            # Also include flat structure for compatibility
            "leads": {
                "total": total_leads,
                "new": status_counts.get("new", 0),
                "researched": status_counts.get("researched", 0),
                "contacted": status_counts.get("contacted", 0),
                "engaged": status_counts.get("engaged", 0),
                "interested": status_counts.get("interested", 0)
            },
            "emails": {
                "total": total_emails,
                "sent": sent,
                "opened": opened,
                "clicked": clicked,
                "bounced": bounced,
                "total_opens": email_stats["total_opens"] or 0,
                "total_clicks": email_stats["total_clicks"] or 0
            },
            "rates": {
                "open_rate": open_rate,
                "click_rate": click_rate,
                "bounce_rate": bounce_rate,
                "delivery_rate": round(((sent - bounced) / sent_for_calc) * 100, 1) if sent > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        # Return empty stats instead of error
        return {
            "success": False,
            "error": str(e),
            "stats": {
                "total_leads": 0,
                "total_emails": 0,
                "total_emails_sent": 0,
                "total_opened": 0,
                "total_clicked": 0,
                "open_rate": 0,
                "click_rate": 0,
                "bounce_rate": 0,
                "recent_activity": {
                    "new_leads_last_7_days": 0,
                    "emails_sent_last_7_days": 0
                }
            },
            "leads": {"total": 0},
            "emails": {"total": 0, "sent": 0},
            "rates": {"open_rate": 0, "click_rate": 0}
        }


@router.get("/recent")
async def get_recent_activity(limit: int = 10):
    """Get recent email activity."""
    from database import get_db_cursor
    
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT 
                    e.id, e.subject, e.status, e.sent_at, e.opened_at,
                    e.open_count, e.click_count,
                    l.name as lead_name, l.email as lead_email, l.company
                FROM generated_emails e
                JOIN leads l ON e.lead_id = l.id
                ORDER BY e.created_at DESC
                LIMIT %s
            """, (limit,))
            
            emails = cursor.fetchall()
        
        return {
            "success": True,
            "recent_activity": [
                {
                    "id": str(e["id"]),
                    "lead_name": e["lead_name"],
                    "lead_email": e["lead_email"],
                    "company": e["company"],
                    "subject": e["subject"],
                    "status": e["status"],
                    "sent_at": str(e["sent_at"]) if e["sent_at"] else None,
                    "opened_at": str(e["opened_at"]) if e["opened_at"] else None,
                    "open_count": e["open_count"] or 0,
                    "click_count": e["click_count"] or 0
                }
                for e in emails
            ]
        }
    except Exception as e:
        logger.error(f"Recent activity error: {e}")
        return {"success": False, "recent_activity": [], "error": str(e)}


@router.get("/performance")
async def get_performance(days: int = 30):
    """Get email performance over time."""
    from database import get_db_cursor
    
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT 
                    DATE(sent_at) as date,
                    COUNT(*) as emails_sent,
                    COUNT(CASE WHEN opened_at IS NOT NULL OR open_count > 0 THEN 1 END) as opened,
                    COUNT(CASE WHEN click_count > 0 THEN 1 END) as clicked
                FROM generated_emails
                WHERE sent_at >= NOW() - INTERVAL '%s days'
                AND sent_at IS NOT NULL
                GROUP BY DATE(sent_at)
                ORDER BY DATE(sent_at) DESC
            """, (days,))
            
            performance = cursor.fetchall()
        
        return {
            "success": True,
            "performance": [
                {
                    "date": str(p["date"]),
                    "emails_sent": p["emails_sent"],
                    "opened": p["opened"],
                    "clicked": p["clicked"],
                    "open_rate": round((p["opened"] / p["emails_sent"]) * 100, 1) if p["emails_sent"] > 0 else 0
                }
                for p in performance
            ]
        }
    except Exception as e:
        logger.error(f"Performance error: {e}")
        return {"success": False, "performance": [], "error": str(e)}


@router.get("/lead-funnel")
async def get_lead_funnel():
    """Get lead funnel data."""
    from database import get_db_cursor
    
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM leads
                GROUP BY status
                ORDER BY count DESC
            """)
            
            funnel_data = cursor.fetchall()
        
        # Define colors for each status
        colors = {
            'new': '#6B7280',
            'researched': '#3B82F6',
            'contacted': '#8B5CF6',
            'email_sent': '#F59E0B',
            'engaged': '#10B981',
            'interested': '#06B6D4',
            'replied': '#EC4899',
            'converted': '#22C55E',
            'bounced': '#EF4444'
        }
        
        return {
            "success": True,
            "funnel": [
                {
                    "status": row["status"],
                    "label": row["status"].replace("_", " ").title(),
                    "count": row["count"],
                    "color": colors.get(row["status"], '#6B7280')
                }
                for row in funnel_data
            ]
        }
    except Exception as e:
        logger.error(f"Funnel error: {e}")
        return {"success": False, "funnel": [], "error": str(e)}