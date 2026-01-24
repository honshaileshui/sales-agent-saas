"""
Email Dashboard Stats API - Week 6 Day 5-6
==========================================
Provides analytics and statistics for email performance.

Endpoints:
- GET /api/dashboard/stats - Overall email statistics
- GET /api/dashboard/recent - Recent email activity
- GET /api/dashboard/performance - Performance over time
- GET /api/dashboard/leads - Lead status breakdown

Author: Shailesh Hon
Week 6: Dashboard Stats
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timedelta
import logging

from api.auth import get_current_user
from database import get_db_cursor

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """
    Get overall email statistics for the dashboard.
    
    Returns:
    - Total emails sent
    - Delivery rate
    - Open rate
    - Click rate
    - Bounce rate
    """
    user_id = str(current_user["id"])
    
    with get_db_cursor(commit=False) as cursor:
        # Get email stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_emails,
                SUM(CASE WHEN status = 'sent' OR status = 'delivered' THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN open_count > 0 THEN 1 ELSE 0 END) as opened,
                SUM(CASE WHEN click_count > 0 THEN 1 ELSE 0 END) as clicked,
                SUM(CASE WHEN bounced = TRUE THEN 1 ELSE 0 END) as bounced,
                SUM(COALESCE(open_count, 0)) as total_opens,
                SUM(COALESCE(click_count, 0)) as total_clicks
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s AND e.is_current = TRUE
        """, (user_id,))
        
        stats = cursor.fetchone()
        
        # Get lead stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_leads,
                SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END) as new,
                SUM(CASE WHEN status = 'researched' THEN 1 ELSE 0 END) as researched,
                SUM(CASE WHEN status = 'email_drafted' THEN 1 ELSE 0 END) as drafted,
                SUM(CASE WHEN status = 'email_sent' THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN status = 'engaged' THEN 1 ELSE 0 END) as engaged,
                SUM(CASE WHEN status = 'interested' THEN 1 ELSE 0 END) as interested,
                SUM(CASE WHEN status = 'bounced' THEN 1 ELSE 0 END) as bounced
            FROM leads
            WHERE user_id = %s
        """, (user_id,))
        
        lead_stats = cursor.fetchone()
    
    # Calculate rates
    sent = stats["sent"] or 0
    delivered = stats["delivered"] or 0
    opened = stats["opened"] or 0
    clicked = stats["clicked"] or 0
    bounced = stats["bounced"] or 0
    
    # Avoid division by zero
    sent_for_calc = sent if sent > 0 else 1
    
    return {
        "emails": {
            "total": stats["total_emails"] or 0,
            "sent": sent,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "bounced": bounced,
            "total_opens": stats["total_opens"] or 0,
            "total_clicks": stats["total_clicks"] or 0
        },
        "rates": {
            "delivery_rate": round((delivered / sent_for_calc) * 100, 1) if sent > 0 else 0,
            "open_rate": round((opened / sent_for_calc) * 100, 1) if sent > 0 else 0,
            "click_rate": round((clicked / sent_for_calc) * 100, 1) if sent > 0 else 0,
            "bounce_rate": round((bounced / sent_for_calc) * 100, 1) if sent > 0 else 0,
            "click_to_open": round((clicked / opened) * 100, 1) if opened > 0 else 0
        },
        "leads": {
            "total": lead_stats["total_leads"] or 0,
            "new": lead_stats["new"] or 0,
            "researched": lead_stats["researched"] or 0,
            "drafted": lead_stats["drafted"] or 0,
            "sent": lead_stats["sent"] or 0,
            "engaged": lead_stats["engaged"] or 0,
            "interested": lead_stats["interested"] or 0,
            "bounced": lead_stats["bounced"] or 0
        }
    }


@router.get("/recent")
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent email activity (opens, clicks, sends).
    """
    user_id = str(current_user["id"])
    
    with get_db_cursor(commit=False) as cursor:
        # Recent sent emails
        cursor.execute("""
            SELECT 
                e.id, e.subject, e.status, e.sent_at, e.opened_at,
                e.open_count, e.click_count,
                l.name as lead_name, l.email as lead_email, l.company
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s AND e.is_current = TRUE
            AND e.status IN ('sent', 'delivered', 'bounced')
            ORDER BY e.sent_at DESC NULLS LAST
            LIMIT %s
        """, (user_id, limit))
        
        recent_emails = cursor.fetchall()
    
    activity = []
    for email in recent_emails:
        activity.append({
            "id": str(email["id"]),
            "type": "email",
            "lead_name": email["lead_name"],
            "lead_email": email["lead_email"],
            "company": email["company"],
            "subject": email["subject"],
            "status": email["status"],
            "sent_at": str(email["sent_at"]) if email["sent_at"] else None,
            "opened_at": str(email["opened_at"]) if email["opened_at"] else None,
            "open_count": email["open_count"] or 0,
            "click_count": email["click_count"] or 0
        })
    
    return {"recent_activity": activity}


@router.get("/performance")
async def get_performance_over_time(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """
    Get email performance over time (daily breakdown).
    """
    user_id = str(current_user["id"])
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                DATE(e.sent_at) as date,
                COUNT(*) as sent,
                SUM(CASE WHEN open_count > 0 THEN 1 ELSE 0 END) as opened,
                SUM(CASE WHEN click_count > 0 THEN 1 ELSE 0 END) as clicked,
                SUM(CASE WHEN bounced = TRUE THEN 1 ELSE 0 END) as bounced
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s 
            AND e.sent_at >= NOW() - INTERVAL '%s days'
            AND e.status IN ('sent', 'delivered', 'bounced')
            GROUP BY DATE(e.sent_at)
            ORDER BY DATE(e.sent_at) ASC
        """, (user_id, days))
        
        daily_stats = cursor.fetchall()
    
    performance = []
    for day in daily_stats:
        sent = day["sent"] or 0
        performance.append({
            "date": str(day["date"]),
            "sent": sent,
            "opened": day["opened"] or 0,
            "clicked": day["clicked"] or 0,
            "bounced": day["bounced"] or 0,
            "open_rate": round((day["opened"] / sent) * 100, 1) if sent > 0 else 0,
            "click_rate": round((day["clicked"] / sent) * 100, 1) if sent > 0 else 0
        })
    
    return {"performance": performance, "days": days}


@router.get("/top-performers")
async def get_top_performing_emails(
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    """
    Get top performing emails by engagement.
    """
    user_id = str(current_user["id"])
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                e.id, e.subject, e.open_count, e.click_count,
                l.name as lead_name, l.company
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s 
            AND e.is_current = TRUE
            AND (e.open_count > 0 OR e.click_count > 0)
            ORDER BY e.click_count DESC, e.open_count DESC
            LIMIT %s
        """, (user_id, limit))
        
        top_emails = cursor.fetchall()
    
    return {
        "top_performers": [
            {
                "id": str(e["id"]),
                "subject": e["subject"],
                "lead_name": e["lead_name"],
                "company": e["company"],
                "open_count": e["open_count"] or 0,
                "click_count": e["click_count"] or 0
            }
            for e in top_emails
        ]
    }


@router.get("/lead-funnel")
async def get_lead_funnel(current_user: dict = Depends(get_current_user)):
    """
    Get lead funnel breakdown showing conversion through stages.
    """
    user_id = str(current_user["id"])
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM leads
            WHERE user_id = %s
            GROUP BY status
            ORDER BY 
                CASE status
                    WHEN 'new' THEN 1
                    WHEN 'researched' THEN 2
                    WHEN 'email_drafted' THEN 3
                    WHEN 'email_sent' THEN 4
                    WHEN 'engaged' THEN 5
                    WHEN 'interested' THEN 6
                    WHEN 'replied' THEN 7
                    WHEN 'meeting_booked' THEN 8
                    WHEN 'converted' THEN 9
                    ELSE 10
                END
        """, (user_id,))
        
        funnel_data = cursor.fetchall()
    
    # Define funnel stages with colors
    stage_config = {
        'new': {'label': 'New Leads', 'color': '#6B7280'},
        'researched': {'label': 'Researched', 'color': '#3B82F6'},
        'email_drafted': {'label': 'Email Drafted', 'color': '#8B5CF6'},
        'email_sent': {'label': 'Email Sent', 'color': '#F59E0B'},
        'engaged': {'label': 'Engaged (Opened)', 'color': '#10B981'},
        'interested': {'label': 'Interested (Clicked)', 'color': '#06B6D4'},
        'replied': {'label': 'Replied', 'color': '#EC4899'},
        'meeting_booked': {'label': 'Meeting Booked', 'color': '#14B8A6'},
        'converted': {'label': 'Converted', 'color': '#22C55E'},
        'bounced': {'label': 'Bounced', 'color': '#EF4444'},
        'unsubscribed': {'label': 'Unsubscribed', 'color': '#9CA3AF'},
        'do_not_contact': {'label': 'Do Not Contact', 'color': '#DC2626'}
    }
    
    funnel = []
    for row in funnel_data:
        status = row["status"]
        config = stage_config.get(status, {'label': status.title(), 'color': '#6B7280'})
        funnel.append({
            "status": status,
            "label": config['label'],
            "count": row["count"],
            "color": config['color']
        })
    
    return {"funnel": funnel}