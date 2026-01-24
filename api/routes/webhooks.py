"""
SendGrid Webhooks Handler - Week 6
===================================
Receives and processes email events from SendGrid.

Events handled:
- delivered: Email reached recipient's server
- open: Recipient opened the email
- click: Recipient clicked a link
- bounce: Email bounced (hard or soft)
- dropped: SendGrid dropped the email
- spam_report: Recipient marked as spam
- unsubscribe: Recipient unsubscribed

Author: Shailesh Hon
Week 6: Email Tracking
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from datetime import datetime
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# WEBHOOK ENDPOINT
# ============================================================================

@router.post("/sendgrid")
async def handle_sendgrid_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receive webhook events from SendGrid.
    
    SendGrid sends events as a JSON array.
    Each event contains information about email delivery, opens, clicks, etc.
    
    Setup in SendGrid:
    1. Go to Settings -> Mail Settings -> Event Webhook
    2. Set HTTP POST URL to: https://yourdomain.com/api/webhooks/sendgrid
    3. Select events: Delivered, Opened, Clicked, Bounced, Dropped, Spam Reports
    4. Enable the webhook
    """
    try:
        # Get the raw body
        body = await request.body()
        events = json.loads(body)
        
        if not isinstance(events, list):
            events = [events]
        
        logger.info(f"[SendGrid Webhook] Received {len(events)} events")
        
        # Process events in background to respond quickly
        background_tasks.add_task(process_sendgrid_events, events)
        
        return {"status": "ok", "received": len(events)}
        
    except json.JSONDecodeError as e:
        logger.error(f"[SendGrid Webhook] Invalid JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"[SendGrid Webhook] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_sendgrid_events(events: List[Dict[str, Any]]):
    """
    Process SendGrid events and update database.
    """
    from database import get_db_cursor
    
    for event in events:
        try:
            event_type = event.get("event")
            email_id = event.get("email_id")  # From custom_args
            sg_message_id = event.get("sg_message_id")
            timestamp = event.get("timestamp")
            
            # Convert timestamp to datetime
            event_time = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
            
            logger.info(f"[SendGrid Event] {event_type} for email_id={email_id}")
            
            # Find the email record
            if not email_id and sg_message_id:
                # Try to find by SendGrid message ID
                with get_db_cursor(commit=False) as cursor:
                    cursor.execute(
                        "SELECT id FROM generated_emails WHERE sendgrid_message_id = %s",
                        (sg_message_id.split('.')[0],)  # SendGrid adds suffix
                    )
                    result = cursor.fetchone()
                    if result:
                        email_id = str(result["id"])
            
            if not email_id:
                logger.warning(f"[SendGrid Event] Could not find email for event: {event_type}")
                continue
            
            # Handle different event types
            if event_type == "delivered":
                await handle_delivered(email_id, event_time, event)
                
            elif event_type == "open":
                await handle_open(email_id, event_time, event)
                
            elif event_type == "click":
                url = event.get("url", "")
                await handle_click(email_id, event_time, url, event)
                
            elif event_type == "bounce":
                bounce_type = event.get("type", "unknown")  # "bounce" or "blocked"
                reason = event.get("reason", "Unknown reason")
                await handle_bounce(email_id, event_time, bounce_type, reason, event)
                
            elif event_type == "dropped":
                reason = event.get("reason", "Unknown reason")
                await handle_dropped(email_id, event_time, reason, event)
                
            elif event_type == "spamreport":
                await handle_spam_report(email_id, event_time, event)
                
            elif event_type == "unsubscribe":
                await handle_unsubscribe(email_id, event_time, event)
                
            else:
                logger.debug(f"[SendGrid Event] Unhandled event type: {event_type}")
                
        except Exception as e:
            logger.error(f"[SendGrid Event] Error processing event: {e}")
            continue


# ============================================================================
# EVENT HANDLERS
# ============================================================================

async def handle_delivered(email_id: str, event_time: datetime, event: dict):
    """Handle email delivered event."""
    from database import get_db_cursor
    
    logger.info(f"[DELIVERED] Email {email_id} delivered at {event_time}")
    
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE generated_emails 
            SET status = 'delivered',
                delivered_at = %s
            WHERE id = %s AND status = 'sent'
        """, (event_time, email_id))


async def handle_open(email_id: str, event_time: datetime, event: dict):
    """Handle email open event."""
    from database import get_db_cursor, LeadDB
    
    logger.info(f"[OPENED] Email {email_id} opened at {event_time}")
    
    with get_db_cursor() as cursor:
        # Update email record
        cursor.execute("""
            UPDATE generated_emails 
            SET open_count = COALESCE(open_count, 0) + 1,
                opened_at = COALESCE(opened_at, %s),
                last_opened_at = %s
            WHERE id = %s
            RETURNING lead_id
        """, (event_time, event_time, email_id))
        
        result = cursor.fetchone()
        
        # Update lead status to show engagement
        if result:
            lead_id = str(result["lead_id"])
            LeadDB.update_status(lead_id, "engaged")
            
            # Log to email_events table if exists
            try:
                cursor.execute("""
                    INSERT INTO email_events (email_id, event_type, event_time, event_data)
                    VALUES (%s, 'open', %s, %s)
                """, (email_id, event_time, json.dumps(event)))
            except:
                pass  # Table might not exist


async def handle_click(email_id: str, event_time: datetime, url: str, event: dict):
    """Handle link click event."""
    from database import get_db_cursor, LeadDB
    
    logger.info(f"[CLICKED] Email {email_id} link clicked: {url[:50]}...")
    
    with get_db_cursor() as cursor:
        # Update email record
        cursor.execute("""
            UPDATE generated_emails 
            SET click_count = COALESCE(click_count, 0) + 1,
                last_clicked_at = %s
            WHERE id = %s
            RETURNING lead_id
        """, (event_time, email_id))
        
        result = cursor.fetchone()
        
        # Update lead status - clicks show high interest
        if result:
            lead_id = str(result["lead_id"])
            LeadDB.update_status(lead_id, "interested")
            
            # Log to email_events table if exists
            try:
                cursor.execute("""
                    INSERT INTO email_events (email_id, event_type, event_time, url, event_data)
                    VALUES (%s, 'click', %s, %s, %s)
                """, (email_id, event_time, url, json.dumps(event)))
            except:
                pass


async def handle_bounce(email_id: str, event_time: datetime, bounce_type: str, reason: str, event: dict):
    """Handle bounce event."""
    from database import get_db_cursor, LeadDB
    
    logger.warning(f"[BOUNCED] Email {email_id} bounced: {bounce_type} - {reason}")
    
    with get_db_cursor() as cursor:
        # Update email record
        cursor.execute("""
            UPDATE generated_emails 
            SET status = 'bounced',
                bounced = TRUE,
                bounce_reason = %s,
                bounced_at = %s
            WHERE id = %s
            RETURNING lead_id
        """, (f"{bounce_type}: {reason}", event_time, email_id))
        
        result = cursor.fetchone()
        
        # Update lead status
        if result:
            lead_id = str(result["lead_id"])
            LeadDB.update_status(lead_id, "bounced")


async def handle_dropped(email_id: str, event_time: datetime, reason: str, event: dict):
    """Handle dropped event (SendGrid refused to send)."""
    from database import get_db_cursor
    
    logger.warning(f"[DROPPED] Email {email_id} dropped: {reason}")
    
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE generated_emails 
            SET status = 'dropped',
                bounce_reason = %s
            WHERE id = %s
        """, (f"Dropped: {reason}", email_id))


async def handle_spam_report(email_id: str, event_time: datetime, event: dict):
    """Handle spam report event."""
    from database import get_db_cursor, LeadDB
    
    logger.warning(f"[SPAM REPORT] Email {email_id} marked as spam!")
    
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE generated_emails 
            SET status = 'spam_reported'
            WHERE id = %s
            RETURNING lead_id
        """, (email_id,))
        
        result = cursor.fetchone()
        
        # Mark lead as do-not-contact
        if result:
            lead_id = str(result["lead_id"])
            LeadDB.update_status(lead_id, "do_not_contact")


async def handle_unsubscribe(email_id: str, event_time: datetime, event: dict):
    """Handle unsubscribe event."""
    from database import get_db_cursor, LeadDB
    
    logger.info(f"[UNSUBSCRIBE] Email {email_id} - recipient unsubscribed")
    
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE generated_emails 
            SET status = 'unsubscribed'
            WHERE id = %s
            RETURNING lead_id
        """, (email_id,))
        
        result = cursor.fetchone()
        
        # Mark lead as unsubscribed
        if result:
            lead_id = str(result["lead_id"])
            LeadDB.update_status(lead_id, "unsubscribed")


# ============================================================================
# STATS ENDPOINTS
# ============================================================================

@router.get("/stats/email/{email_id}")
async def get_email_tracking_stats(email_id: str):
    """Get tracking stats for a specific email."""
    from database import get_db_cursor
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                id, lead_id, subject, status,
                sent_at, delivered_at, opened_at, last_opened_at,
                open_count, click_count, 
                bounced, bounce_reason
            FROM generated_emails
            WHERE id = %s
        """, (email_id,))
        
        email = cursor.fetchone()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return {
        "email_id": str(email["id"]),
        "lead_id": str(email["lead_id"]),
        "subject": email["subject"],
        "status": email["status"],
        "tracking": {
            "sent_at": str(email["sent_at"]) if email.get("sent_at") else None,
            "delivered_at": str(email["delivered_at"]) if email.get("delivered_at") else None,
            "opened_at": str(email["opened_at"]) if email.get("opened_at") else None,
            "last_opened_at": str(email["last_opened_at"]) if email.get("last_opened_at") else None,
            "open_count": email.get("open_count", 0),
            "click_count": email.get("click_count", 0)
        },
        "bounced": email.get("bounced", False),
        "bounce_reason": email.get("bounce_reason")
    }


@router.get("/stats/summary")
async def get_tracking_summary():
    """Get overall email tracking statistics."""
    from database import get_db_cursor
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sent,
                SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN open_count > 0 THEN 1 ELSE 0 END) as opened,
                SUM(CASE WHEN click_count > 0 THEN 1 ELSE 0 END) as clicked,
                SUM(CASE WHEN bounced = TRUE THEN 1 ELSE 0 END) as bounced,
                SUM(open_count) as total_opens,
                SUM(click_count) as total_clicks
            FROM generated_emails
            WHERE status IN ('sent', 'delivered', 'bounced')
        """)
        
        stats = cursor.fetchone()
    
    total = stats["total_sent"] or 1  # Avoid division by zero
    delivered = stats["delivered"] or 0
    opened = stats["opened"] or 0
    clicked = stats["clicked"] or 0
    bounced = stats["bounced"] or 0
    
    return {
        "emails": {
            "total_sent": stats["total_sent"] or 0,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "bounced": bounced
        },
        "rates": {
            "delivery_rate": round((delivered / total) * 100, 1),
            "open_rate": round((opened / total) * 100, 1),
            "click_rate": round((clicked / total) * 100, 1),
            "bounce_rate": round((bounced / total) * 100, 1)
        },
        "totals": {
            "total_opens": stats["total_opens"] or 0,
            "total_clicks": stats["total_clicks"] or 0
        }
    }