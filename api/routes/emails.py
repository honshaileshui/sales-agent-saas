"""
Emails Routes - Week 6 Update
==============================
Now with REAL email sending via SendGrid!

Features:
- Send single email
- Send bulk emails
- Track opens/clicks
- Bounce handling

Author: Shailesh Hon
Updated: Week 6 - Email Sending
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.models import (
    EmailGenerate, EmailUpdate, EmailResponse, 
    EmailWithLeadResponse, SuccessResponse
)
from api.auth import get_current_user
from database import LeadDB, EmailDB, ResearchDB, get_db_cursor

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class BulkSendRequest(BaseModel):
    email_ids: List[str]

class BulkApproveRequest(BaseModel):
    email_ids: List[str]


# ============================================================================
# EMAIL CRUD OPERATIONS
# ============================================================================

@router.get("")
async def list_emails(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get all emails for the current user's leads."""
    user_id = str(current_user["id"])
    offset = (page - 1) * per_page
    
    with get_db_cursor(commit=False) as cursor:
        query = """
            SELECT e.*, l.name as lead_name, l.email as lead_email, l.company
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s AND e.is_current = TRUE
        """
        params = [user_id]
        
        if status:
            query += " AND e.status = %s"
            params.append(status)
        
        query += " ORDER BY e.created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        emails = [dict(row) for row in cursor.fetchall()]
        
        count_query = """
            SELECT COUNT(*) FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s AND e.is_current = TRUE
        """
        count_params = [user_id]
        if status:
            count_query += " AND e.status = %s"
            count_params.append(status)
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()["count"]
    
    return {
        "emails": [
            {
                "id": str(e["id"]),
                "lead_id": str(e["lead_id"]),
                "lead_name": e["lead_name"],
                "lead_email": e["lead_email"],
                "company": e["company"],
                "subject": e.get("subject"),
                "body": e["body"],
                "template_used": e["template_used"],
                "tone": e["tone"],
                "version": e["version"],
                "status": e["status"],
                "sent_at": str(e["sent_at"]) if e.get("sent_at") else None,
                "opened_at": str(e["opened_at"]) if e.get("opened_at") else None,
                "open_count": e.get("open_count", 0),
                "click_count": e.get("click_count", 0),
                "created_at": str(e["created_at"])
            }
            for e in emails
        ],
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/stats/summary")
async def get_email_stats(current_user: dict = Depends(get_current_user)):
    """Get email statistics for dashboard."""
    user_id = str(current_user["id"])
    
    with get_db_cursor(commit=False) as cursor:
        # Get counts by status
        cursor.execute("""
            SELECT e.status, COUNT(*) as count
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s AND e.is_current = TRUE
            GROUP BY e.status
        """, (user_id,))
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
        
        # Get open/click rates
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sent,
                SUM(CASE WHEN open_count > 0 THEN 1 ELSE 0 END) as opened,
                SUM(CASE WHEN click_count > 0 THEN 1 ELSE 0 END) as clicked,
                SUM(open_count) as total_opens,
                SUM(click_count) as total_clicks
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE l.user_id = %s AND e.status = 'sent'
        """, (user_id,))
        performance = cursor.fetchone()
    
    total_sent = performance["total_sent"] or 0
    opened = performance["opened"] or 0
    clicked = performance["clicked"] or 0
    
    return {
        "by_status": status_counts,
        "total": sum(status_counts.values()),
        "performance": {
            "sent": total_sent,
            "opened": opened,
            "clicked": clicked,
            "open_rate": round((opened / total_sent * 100), 1) if total_sent > 0 else 0,
            "click_rate": round((clicked / total_sent * 100), 1) if total_sent > 0 else 0,
            "total_opens": performance["total_opens"] or 0,
            "total_clicks": performance["total_clicks"] or 0
        }
    }


@router.get("/{email_id}")
async def get_email(
    email_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific email with full details."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT e.*, l.name as lead_name, l.email as lead_email, 
                   l.company, l.job_title, l.user_id
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE e.id = %s
        """, (email_id,))
        email = cursor.fetchone()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if str(email["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": str(email["id"]),
        "lead_id": str(email["lead_id"]),
        "lead_name": email["lead_name"],
        "lead_email": email["lead_email"],
        "company": email["company"],
        "job_title": email.get("job_title"),
        "subject": email.get("subject"),
        "body": email["body"],
        "template_used": email["template_used"],
        "tone": email["tone"],
        "version": email["version"],
        "is_current": email["is_current"],
        "status": email["status"],
        "sent_at": str(email["sent_at"]) if email.get("sent_at") else None,
        "opened_at": str(email["opened_at"]) if email.get("opened_at") else None,
        "replied_at": str(email["replied_at"]) if email.get("replied_at") else None,
        "open_count": email.get("open_count", 0),
        "click_count": email.get("click_count", 0),
        "sendgrid_message_id": email.get("sendgrid_message_id"),
        "created_at": str(email["created_at"])
    }


@router.put("/{email_id}")
async def update_email(
    email_id: str,
    email_data: EmailUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an email (edit subject/body before sending)."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT e.*, l.user_id
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE e.id = %s
        """, (email_id,))
        email = cursor.fetchone()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if str(email["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if email["status"] not in ["draft", "approved"]:
        raise HTTPException(
            status_code=400, 
            detail="Can only edit draft or approved emails"
        )
    
    update_fields = []
    params = []
    
    if email_data.subject is not None:
        update_fields.append("subject = %s")
        params.append(email_data.subject)
    
    if email_data.body is not None:
        update_fields.append("body = %s")
        params.append(email_data.body)
    
    if email_data.status is not None:
        update_fields.append("status = %s")
        params.append(email_data.status.value if hasattr(email_data.status, 'value') else email_data.status)
    
    if update_fields:
        params.append(email_id)
        with get_db_cursor() as cursor:
            cursor.execute(
                f"UPDATE generated_emails SET {', '.join(update_fields)} WHERE id = %s RETURNING *",
                params
            )
            updated = cursor.fetchone()
        
        return {
            "success": True,
            "message": "Email updated successfully",
            "email": {
                "id": str(updated["id"]),
                "subject": updated.get("subject"),
                "body": updated["body"],
                "status": updated["status"]
            }
        }
    
    return {"success": True, "message": "No changes made"}


@router.delete("/{email_id}")
async def delete_email(
    email_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an email."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT e.*, l.user_id
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE e.id = %s
        """, (email_id,))
        email = cursor.fetchone()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if str(email["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM generated_emails WHERE id = %s", (email_id,))
    
    return {"success": True, "message": "Email deleted successfully"}


# ============================================================================
# EMAIL GENERATION
# ============================================================================

@router.post("/generate")
async def generate_email(
    request: EmailGenerate,
    current_user: dict = Depends(get_current_user)
):
    """Generate a new email for a lead using AI."""
    lead = LeadDB.get_by_id(request.lead_id)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if str(lead["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    research = ResearchDB.get_by_lead_id(request.lead_id)
    
    if not research:
        raise HTTPException(
            status_code=400,
            detail="Lead must be researched before generating email. Run research first."
        )
    
    try:
        from sales_agent import generate_personalized_email, CONFIG
        
        lead_data = {
            'name': lead['name'],
            'email': lead['email'],
            'company': lead['company'],
            'job_title': lead.get('job_title', '')
        }
        
        research_data = {
            'summary': research.get('ai_summary', f"Company: {lead['company']}")
        }
        
        original_template = CONFIG['email_settings']['template']
        original_tone = CONFIG['email_settings']['tone']
        
        CONFIG['email_settings']['template'] = request.template or 'default'
        CONFIG['email_settings']['tone'] = request.tone or 'professional'
        
        email_result = generate_personalized_email(lead_data, research_data)
        
        CONFIG['email_settings']['template'] = original_template
        CONFIG['email_settings']['tone'] = original_tone
        
        if not email_result:
            raise HTTPException(status_code=500, detail="Failed to generate email")
        
        saved_email = EmailDB.create(
            lead_id=request.lead_id,
            subject=email_result.get('subject', ''),
            body=email_result['body'],
            template_used=request.template or 'default',
            tone=request.tone or 'professional',
            research_id=str(research['id'])
        )
        
        LeadDB.update_status(request.lead_id, 'email_drafted')
        
        return {
            "success": True,
            "email": {
                "id": str(saved_email["id"]),
                "subject": saved_email.get("subject"),
                "body": saved_email["body"],
                "version": saved_email["version"],
                "status": saved_email["status"]
            }
        }
        
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not import sales_agent module: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating email: {str(e)}"
        )


@router.post("/{email_id}/regenerate")
async def regenerate_email(
    email_id: str,
    template: Optional[str] = Query("default"),
    tone: Optional[str] = Query("professional"),
    current_user: dict = Depends(get_current_user)
):
    """Regenerate an email with different settings."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT e.lead_id, l.user_id
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE e.id = %s
        """, (email_id,))
        result = cursor.fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if str(result["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    request = EmailGenerate(
        lead_id=str(result["lead_id"]),
        template=template,
        tone=tone
    )
    
    return await generate_email(request, current_user)


# ============================================================================
# EMAIL ACTIONS - APPROVE
# ============================================================================

@router.post("/{email_id}/approve")
async def approve_email(
    email_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark an email as approved and ready to send."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT e.*, l.user_id
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE e.id = %s
        """, (email_id,))
        email = cursor.fetchone()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if str(email["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    EmailDB.update_status(email_id, "approved")
    
    return {"success": True, "message": "Email approved and ready to send"}


@router.post("/approve/bulk")
async def bulk_approve_emails(
    request: BulkApproveRequest,
    current_user: dict = Depends(get_current_user)
):
    """Approve multiple emails at once."""
    user_id = str(current_user["id"])
    approved = 0
    failed = 0
    
    for email_id in request.email_ids:
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT e.*, l.user_id
                    FROM generated_emails e
                    JOIN leads l ON e.lead_id = l.id
                    WHERE e.id = %s
                """, (email_id,))
                email = cursor.fetchone()
            
            if email and str(email["user_id"]) == user_id:
                EmailDB.update_status(email_id, "approved")
                approved += 1
            else:
                failed += 1
        except:
            failed += 1
    
    return {
        "success": True,
        "approved": approved,
        "failed": failed,
        "total": len(request.email_ids)
    }


# ============================================================================
# EMAIL ACTIONS - SEND (NEW! Week 6)
# ============================================================================

@router.post("/{email_id}/send")
async def send_email(
    email_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    ACTUALLY SEND an email via SendGrid!
    
    This is the Week 6 implementation that really sends emails.
    """
    # Get email with lead details
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT e.*, l.user_id, l.email as lead_email, l.name as lead_name,
                   l.company, l.id as lead_id
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE e.id = %s
        """, (email_id,))
        email = cursor.fetchone()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if str(email["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if email["status"] == "sent":
        raise HTTPException(status_code=400, detail="Email already sent")
    
    if email["status"] not in ["draft", "approved"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot send email with status: {email['status']}"
        )
    
    # Import SendGrid client
    try:
        from email_service.sendgrid_client import get_email_client
        
        client = get_email_client()
        
        # Send the email!
        result = client.send_email(
            to_email=email["lead_email"],
            to_name=email["lead_name"],
            subject=email["subject"] or f"Quick question about {email['company']}",
            body=email["body"],
            email_id=str(email["id"]),
            lead_id=str(email["lead_id"]),
            track_opens=True,
            track_clicks=True,
            categories=["salesagent", "outreach"]
        )
        
        if result["success"]:
            # Update database
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE generated_emails 
                    SET status = 'sent', 
                        sent_at = NOW(),
                        sendgrid_message_id = %s
                    WHERE id = %s
                """, (result.get("message_id"), email_id))
            
            # Update lead status
            LeadDB.update_status(str(email["lead_id"]), "email_sent")
            
            logger.info(f"Email sent successfully to {email['lead_email']}")
            
            return {
                "success": True,
                "message": f"Email sent to {email['lead_email']}",
                "message_id": result.get("message_id"),
                "sent_at": datetime.now().isoformat()
            }
        else:
            logger.error(f"SendGrid error: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send email: {result.get('error')}"
            )
            
    except ImportError as e:
        logger.error(f"SendGrid import error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Email service not configured. Check email_service module."
        )
    except Exception as e:
        logger.error(f"Send error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send: {str(e)}")

@router.post("/{email_id}/send")
async def send_single_email(
    email_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a single email by ID.
    This is the endpoint the frontend expects!
    """
    user_id = str(current_user["id"])
    
    # Get email from database
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT e.*, l.user_id, l.email as lead_email, l.name as lead_name,
                   l.company, l.id as lead_id
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE e.id = %s
        """, (email_id,))
        email = cursor.fetchone()
    
    # Verify email exists and user owns it
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if str(email["user_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if already sent
    if email["status"] == "sent":
        raise HTTPException(status_code=400, detail="Email already sent")
    
    # Get email client
    try:
        from email_service.sendgrid_client import get_email_client
        client = get_email_client()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Email service not configured. Check SendGrid setup."
        )
    
    # Send email via SendGrid
    try:
        result = client.send_email(
            to_email=email["lead_email"],
            to_name=email["lead_name"],
            subject=email["subject"] or f"Quick question about {email['company']}",
            body=email["body"],
            email_id=str(email["id"]),
            lead_id=str(email["lead_id"]),
            track_opens=True,
            track_clicks=True
        )
        
        if result["success"]:
            # Update database
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE generated_emails 
                    SET status = 'sent', sent_at = NOW(), sendgrid_message_id = %s
                    WHERE id = %s
                """, (result.get("message_id"), email_id))
            
            # Update lead status
            LeadDB.update_status(str(email["lead_id"]), "email_sent")
            
            logger.info(f"Email {email_id} sent successfully to {email['lead_email']}")
            
            return {
                "success": True,
                "message": f"Email sent to {email['lead_email']}",
                "message_id": result.get("message_id"),
                "sent_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to send email: {result.get('error')}"
            )
            
    except Exception as e:
        logger.error(f"Error sending email {email_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/bulk")
async def bulk_send_emails(
    request: BulkSendRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Send multiple emails at once.
    
    Emails are sent one by one with a small delay to avoid rate limits.
    """
    user_id = str(current_user["id"])
    results = {
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "details": []
    }
    
    try:
        from email_service.sendgrid_client import get_email_client
        client = get_email_client()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Email service not configured"
        )
    
    for email_id in request.email_ids:
        try:
            # Get email
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT e.*, l.user_id, l.email as lead_email, l.name as lead_name,
                           l.company, l.id as lead_id
                    FROM generated_emails e
                    JOIN leads l ON e.lead_id = l.id
                    WHERE e.id = %s
                """, (email_id,))
                email = cursor.fetchone()
            
            # Verify ownership and status
            if not email or str(email["user_id"]) != user_id:
                results["skipped"] += 1
                results["details"].append({"id": email_id, "status": "skipped", "reason": "not found or access denied"})
                continue
            
            if email["status"] == "sent":
                results["skipped"] += 1
                results["details"].append({"id": email_id, "status": "skipped", "reason": "already sent"})
                continue
            
            # Send email
            result = client.send_email(
                to_email=email["lead_email"],
                to_name=email["lead_name"],
                subject=email["subject"] or f"Quick question about {email['company']}",
                body=email["body"],
                email_id=str(email["id"]),
                lead_id=str(email["lead_id"]),
                track_opens=True,
                track_clicks=True
            )
            
            if result["success"]:
                # Update database
                with get_db_cursor() as cursor:
                    cursor.execute("""
                        UPDATE generated_emails 
                        SET status = 'sent', sent_at = NOW(), sendgrid_message_id = %s
                        WHERE id = %s
                    """, (result.get("message_id"), email_id))
                
                LeadDB.update_status(str(email["lead_id"]), "email_sent")
                
                results["sent"] += 1
                results["details"].append({
                    "id": email_id, 
                    "status": "sent", 
                    "to": email["lead_email"],
                    "message_id": result.get("message_id")
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "id": email_id, 
                    "status": "failed", 
                    "error": result.get("error")
                })
                
        except Exception as e:
            results["failed"] += 1
            results["details"].append({"id": email_id, "status": "failed", "error": str(e)})
    
    logger.info(f"Bulk send complete: {results['sent']} sent, {results['failed']} failed, {results['skipped']} skipped")
    
    return {
        "success": True,
        "sent": results["sent"],
        "failed": results["failed"],
        "skipped": results["skipped"],
        "total": len(request.email_ids),
        "details": results["details"]
    }


# ============================================================================
# EMAIL HISTORY
# ============================================================================

@router.get("/{email_id}/versions")
async def get_email_versions(
    email_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all versions of an email (regeneration history)."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT e.lead_id, l.user_id
            FROM generated_emails e
            JOIN leads l ON e.lead_id = l.id
            WHERE e.id = %s
        """, (email_id,))
        result = cursor.fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if str(result["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    versions = EmailDB.get_all_versions(str(result["lead_id"]))
    
    return {
        "versions": [
            {
                "id": str(v["id"]),
                "version": v["version"],
                "is_current": v["is_current"],
                "subject": v.get("subject"),
                "body": v["body"],
                "template_used": v["template_used"],
                "tone": v["tone"],
                "status": v["status"],
                "created_at": str(v["created_at"])
            }
            for v in versions
        ]
    }


# ============================================================================
# TRACKING ENDPOINTS
# ============================================================================

@router.post("/{email_id}/track/open")
async def track_email_open(email_id: str):
    """
    Track when an email is opened.
    Called by tracking pixel in email.
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE generated_emails 
                SET open_count = COALESCE(open_count, 0) + 1,
                    opened_at = COALESCE(opened_at, NOW())
                WHERE id = %s
            """, (email_id,))
        
        logger.info(f"Open tracked for email {email_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to track open: {e}")
        return {"success": False}


@router.post("/{email_id}/track/click")
async def track_email_click(email_id: str, url: str = Query(...)):
    """
    Track when a link in an email is clicked.
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE generated_emails 
                SET click_count = COALESCE(click_count, 0) + 1
                WHERE id = %s
            """, (email_id,))
        
        logger.info(f"Click tracked for email {email_id}: {url}")
        return {"success": True, "redirect": url}
    except Exception as e:
        logger.error(f"Failed to track click: {e}")
        return {"success": False, "redirect": url}


# ============================================================================
# TEST ENDPOINT
# ============================================================================

@router.post("/test-send")
async def test_send_email(
    to_email: str = Query(..., description="Email to send test to"),
    current_user: dict = Depends(get_current_user)
):
    """
    Send a test email to verify SendGrid is working.
    """
    try:
        from email_service.sendgrid_client import get_email_client
        
        client = get_email_client()
        
        result = client.send_email(
            to_email=to_email,
            to_name="Test User",
            subject="SalesAgent AI - Test Email",
            body=f"""Hi!

This is a test email from SalesAgent AI.

If you received this, your email configuration is working correctly!

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best,
SalesAgent AI""",
            email_id=f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            track_opens=True,
            track_clicks=True,
            categories=["test"]
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Test email sent to {to_email}",
                "message_id": result.get("message_id")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Email service not configured"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))