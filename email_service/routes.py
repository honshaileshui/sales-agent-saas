"""
Email API Routes for SalesAgent AI
===================================
FastAPI routes for:
- Sending emails
- Tracking endpoints (pixel, clicks)
- Webhook handling
- Unsubscribe handling

Author: Shailesh
Week 5: Email Infrastructure
"""

import os
import sys
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request, Response, Query, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, EmailStr

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import logging
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["email"])


# ============================================================
# PYDANTIC MODELS
# ============================================================

class SendEmailRequest(BaseModel):
    """Request to send a single email."""
    email_id: str
    
class SendEmailDirectRequest(BaseModel):
    """Request to send email directly with content."""
    to_email: EmailStr
    to_name: str
    subject: str
    body: str
    lead_id: Optional[str] = None
    campaign_id: Optional[str] = None

class SendTestEmailRequest(BaseModel):
    """Request to send a test email."""
    to_email: EmailStr

class BulkSendRequest(BaseModel):
    """Request to send multiple emails."""
    email_ids: List[str]

class SendCampaignRequest(BaseModel):
    """Request to send campaign emails."""
    campaign_id: str
    limit: Optional[int] = 50

class EmailSendResponse(BaseModel):
    """Response from email send operation."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None

class BulkSendResponse(BaseModel):
    """Response from bulk send operation."""
    sent: int
    failed: int
    total: int


# ============================================================
# EMAIL SENDING ROUTES
# ============================================================

@router.post("/emails/{email_id}/send", response_model=EmailSendResponse)
async def send_email(email_id: str, background_tasks: BackgroundTasks):
    """
    Send a single email by ID.
    
    The email must be in 'approved' status to be sent.
    """
    try:
        # Lazy import to avoid circular dependencies
        from email_service import get_email_service
        
        service = get_email_service()
        
        # TODO: Fetch email from database and send
        # For now, return a placeholder
        
        # This would be the actual implementation:
        # email = EmailDB.get(email_id)
        # if not email:
        #     raise HTTPException(status_code=404, detail="Email not found")
        # if email['status'] != 'approved':
        #     raise HTTPException(status_code=400, detail="Email must be approved before sending")
        # 
        # result = service.send_email(
        #     to_email=email['to_email'],
        #     to_name=email['lead_name'],
        #     subject=email['subject'],
        #     body=email['body'],
        #     email_id=email_id,
        #     lead_id=email['lead_id'],
        #     campaign_id=email.get('campaign_id')
        # )
        
        return EmailSendResponse(
            success=True,
            message_id=f"placeholder-{email_id}",
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email {email_id}: {e}")
        return EmailSendResponse(success=False, error=str(e))


@router.post("/emails/send-direct", response_model=EmailSendResponse)
async def send_email_direct(request: SendEmailDirectRequest):
    """
    Send an email directly without database lookup.
    Useful for testing and ad-hoc sends.
    """
    try:
        from email_service import get_email_service
        
        service = get_email_service()
        
        result = service.send_email(
            to_email=request.to_email,
            to_name=request.to_name,
            subject=request.subject,
            body=request.body,
            email_id=f"direct-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            lead_id=request.lead_id,
            campaign_id=request.campaign_id
        )
        
        return EmailSendResponse(
            success=result['success'],
            message_id=result.get('message_id'),
            error=result.get('error')
        )
        
    except Exception as e:
        logger.error(f"Error sending direct email: {e}")
        return EmailSendResponse(success=False, error=str(e))


@router.post("/emails/send-test", response_model=EmailSendResponse)
async def send_test_email(request: SendTestEmailRequest):
    """
    Send a test email to verify configuration.
    """
    try:
        from email_service import get_email_service
        
        service = get_email_service()
        result = service.send_test_email(request.to_email)
        
        return EmailSendResponse(
            success=result['success'],
            message_id=result.get('message_id'),
            error=result.get('error')
        )
        
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        return EmailSendResponse(success=False, error=str(e))


@router.post("/emails/send-bulk", response_model=BulkSendResponse)
async def send_bulk_emails(request: BulkSendRequest, background_tasks: BackgroundTasks):
    """
    Send multiple emails by IDs.
    Emails are sent in the background.
    """
    try:
        # TODO: Implement bulk sending
        # This would fetch emails from database and send them
        
        return BulkSendResponse(
            sent=0,
            failed=0,
            total=len(request.email_ids)
        )
        
    except Exception as e:
        logger.error(f"Error in bulk send: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# TRACKING ROUTES
# ============================================================

# 1x1 transparent GIF for open tracking
TRACKING_PIXEL = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00,
    0x01, 0x00, 0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF,
    0x00, 0x00, 0x00, 0x21, 0xF9, 0x04, 0x01, 0x00,
    0x00, 0x00, 0x00, 0x2C, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3B
])


@router.get("/track/pixel")
async def track_pixel(
    request: Request,
    eid: str = Query(..., description="Email ID"),
    lid: Optional[str] = Query(None, description="Lead ID"),
    cid: Optional[str] = Query(None, description="Campaign ID"),
    t: Optional[str] = Query(None, description="Timestamp")
):
    """
    Tracking pixel endpoint for open detection.
    Returns a 1x1 transparent GIF.
    """
    try:
        from email_service import get_event_store
        
        store = get_event_store()
        
        # Record the open event
        store.record_open(
            email_id=eid,
            lead_id=lid,
            campaign_id=cid,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent')
        )
        
        logger.info(f"Open tracked for email {eid}")
        
    except Exception as e:
        logger.error(f"Error tracking open: {e}")
    
    # Always return the pixel
    return Response(
        content=TRACKING_PIXEL,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@router.get("/track/click")
async def track_click(
    request: Request,
    url: str = Query(..., description="Original URL"),
    eid: str = Query(..., description="Email ID"),
    lid: Optional[str] = Query(None, description="Lead ID"),
    cid: Optional[str] = Query(None, description="Campaign ID")
):
    """
    Click tracking endpoint.
    Records the click and redirects to the original URL.
    """
    try:
        from email_service import get_event_store
        
        store = get_event_store()
        
        # Record the click event
        store.record_click(
            email_id=eid,
            url=url,
            lead_id=lid,
            campaign_id=cid,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent')
        )
        
        logger.info(f"Click tracked for email {eid}: {url}")
        
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
    
    # Redirect to original URL
    return RedirectResponse(url=url, status_code=302)


# ============================================================
# UNSUBSCRIBE ROUTES
# ============================================================

@router.get("/unsubscribe")
async def unsubscribe_page(
    eid: str = Query(..., description="Email ID"),
    lid: str = Query(..., description="Lead ID")
):
    """
    Unsubscribe landing page.
    Shows confirmation form.
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unsubscribe - SalesAgent AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                text-align: center;
            }}
            .card {{
                background: #f9f9f9;
                border-radius: 12px;
                padding: 40px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #333; }}
            p {{ color: #666; line-height: 1.6; }}
            .btn {{
                display: inline-block;
                padding: 12px 30px;
                margin: 10px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                cursor: pointer;
                border: none;
            }}
            .btn-primary {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .btn-secondary {{
                background: #e0e0e0;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>😢 We're sorry to see you go</h1>
            <p>Are you sure you want to unsubscribe from our emails?</p>
            <p>You'll no longer receive personalized outreach from us.</p>
            <form action="/api/unsubscribe/confirm" method="POST">
                <input type="hidden" name="eid" value="{eid}">
                <input type="hidden" name="lid" value="{lid}">
                <button type="submit" class="btn btn-primary">Yes, Unsubscribe</button>
                <a href="javascript:window.close()" class="btn btn-secondary">Cancel</a>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.post("/unsubscribe/confirm")
async def confirm_unsubscribe(request: Request):
    """
    Process unsubscribe confirmation.
    """
    try:
        form_data = await request.form()
        email_id = form_data.get('eid')
        lead_id = form_data.get('lid')
        
        logger.info(f"Unsubscribe confirmed for lead {lead_id}")
        
        # TODO: Update lead status in database
        # LeadDB.update_status(lead_id, 'unsubscribed')
        # SuppressionList.add(lead_email, reason='unsubscribed')
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Unsubscribed - SalesAgent AI</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    text-align: center;
                }
                .card {
                    background: #f9f9f9;
                    border-radius: 12px;
                    padding: 40px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { color: #333; }
                p { color: #666; }
                .success { color: #10b981; font-size: 48px; }
            </style>
        </head>
        <body>
            <div class="card">
                <div class="success">✓</div>
                <h1>You've been unsubscribed</h1>
                <p>You won't receive any more emails from us.</p>
                <p>If you unsubscribed by mistake, please contact us.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
        
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")
        raise HTTPException(status_code=500, detail="Failed to process unsubscribe")


# ============================================================
# WEBHOOK ROUTES
# ============================================================

@router.post("/webhooks/sendgrid")
async def handle_sendgrid_webhook(request: Request):
    """
    Handle incoming SendGrid webhooks.
    
    SendGrid sends events like:
    - delivered
    - open
    - click
    - bounce
    - spam_report
    - unsubscribe
    """
    try:
        from email_service import get_webhook_handler
        
        body = await request.body()
        events = await request.json()
        
        # Verify signature (if configured)
        handler = get_webhook_handler()
        
        # signature = request.headers.get('X-Twilio-Email-Event-Webhook-Signature')
        # timestamp = request.headers.get('X-Twilio-Email-Event-Webhook-Timestamp')
        # if signature and not handler.verify_signature(body, signature, timestamp):
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process events
        results = handler.process_events(events)
        
        logger.info(f"Processed {len(results)} SendGrid webhook events")
        
        return {"processed": len(results)}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Always return 200 to SendGrid to prevent retries
        return {"error": str(e)}


# ============================================================
# STATS ROUTES
# ============================================================

@router.get("/emails/{email_id}/tracking")
async def get_email_tracking(email_id: str):
    """
    Get tracking stats for a specific email.
    """
    try:
        from email_service import get_event_store
        
        store = get_event_store()
        stats = store.get_email_stats(email_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting tracking stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_id}/tracking")
async def get_campaign_tracking(campaign_id: str):
    """
    Get tracking stats for a campaign.
    """
    try:
        from email_service import get_event_store
        
        store = get_event_store()
        stats = store.get_campaign_stats(campaign_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting campaign stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracking/events")
async def get_tracking_events(
    event_type: Optional[str] = None,
    email_id: Optional[str] = None,
    limit: int = 50
):
    """
    Get recent tracking events.
    """
    try:
        from email_service import get_event_store
        
        store = get_event_store()
        events = store.get_all_events(
            event_type=event_type,
            email_id=email_id,
            limit=limit
        )
        
        return {"events": events, "count": len(events)}
        
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
