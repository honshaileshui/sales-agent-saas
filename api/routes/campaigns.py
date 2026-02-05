"""
Campaigns Routes
================
Manage email campaigns (groups of leads for organized outreach).
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.models import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignAddLeads, CampaignScheduleSet, CampaignScheduleUpdate, SuccessResponse
)
from api.auth import get_current_user
from database import CampaignDB, LeadDB, get_db_cursor

router = APIRouter()


# ============================================================================
# CAMPAIGN CRUD
# ============================================================================

@router.get("")
async def list_campaigns(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user)
):
    """Get all campaigns for the current user."""
    user_id = str(current_user["id"])
    
    campaigns = CampaignDB.get_all_for_user(user_id)
    
    # Filter by status if provided
    if status:
        campaigns = [c for c in campaigns if c["status"] == status]
    
    return {
        "campaigns": [
            {
                "id": str(c["id"]),
                "name": c["name"],
                "description": c.get("description"),
                "template": c["template"],
                "tone": c["tone"],
                "status": c["status"],
                "total_leads": c.get("total_leads", 0),
                "emails_sent": c.get("emails_sent", 0),
                "emails_opened": c.get("emails_opened", 0),
                "replies_received": c.get("replies_received", 0),
                "created_at": c["created_at"],
                "updated_at": c["updated_at"]
            }
            for c in campaigns
        ]
    }


@router.get("/scheduled")
async def list_scheduled_campaigns(
    upcoming_only: bool = Query(True, description="Only return campaigns with schedule in the future"),
    current_user: dict = Depends(get_current_user)
):
    """Get all campaigns that have a schedule set. Optionally filter to upcoming only."""
    user_id = str(current_user["id"])
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT id, name, status, scheduled_start_date, scheduled_start_time,
                   timezone, daily_send_limit, emails_sent_today, last_send_date
            FROM email_campaigns
            WHERE user_id = %s
              AND scheduled_start_date IS NOT NULL
              AND scheduled_start_time IS NOT NULL
        """, (user_id,))
        rows = cursor.fetchall()
    campaigns = [dict(r) for r in rows]
    if upcoming_only:
        from datetime import date, time, datetime
        now = datetime.utcnow()
        today = now.date()
        current_time = now.time()
        filtered = []
        for c in campaigns:
            sd = c.get("scheduled_start_date")
            st = c.get("scheduled_start_time")
            if sd and st:
                if sd > today or (sd == today and st > current_time):
                    filtered.append(c)
        campaigns = filtered
    return {
        "campaigns": [
            {
                "id": str(c["id"]),
                "name": c["name"],
                "status": c["status"],
                "scheduled_start_date": c.get("scheduled_start_date"),
                "scheduled_start_time": str(c["scheduled_start_time"]) if c.get("scheduled_start_time") else None,
                "timezone": c.get("timezone", "UTC"),
                "daily_send_limit": c.get("daily_send_limit", 50),
                "emails_sent_today": c.get("emails_sent_today", 0),
                "last_send_date": c.get("last_send_date"),
            }
            for c in campaigns
        ]
    }


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific campaign with details."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT * FROM email_campaigns WHERE id = %s",
            (campaign_id,)
        )
        campaign = cursor.fetchone()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get leads in this campaign
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT l.*, cl.status as campaign_status, cl.sequence_position
            FROM campaign_leads cl
            JOIN leads l ON cl.lead_id = l.id
            WHERE cl.campaign_id = %s
            ORDER BY cl.sequence_position
        """, (campaign_id,))
        leads = [dict(row) for row in cursor.fetchall()]
    
    return {
        "id": str(campaign["id"]),
        "name": campaign["name"],
        "description": campaign.get("description"),
        "template": campaign["template"],
        "tone": campaign["tone"],
        "status": campaign["status"],
        "total_leads": campaign.get("total_leads", 0),
        "emails_sent": campaign.get("emails_sent", 0),
        "emails_opened": campaign.get("emails_opened", 0),
        "replies_received": campaign.get("replies_received", 0),
        "created_at": campaign["created_at"],
        "updated_at": campaign["updated_at"],
        "leads": [
            {
                "id": str(l["id"]),
                "name": l["name"],
                "email": l["email"],
                "company": l["company"],
                "status": l["status"],
                "campaign_status": l["campaign_status"],
                "sequence_position": l["sequence_position"]
            }
            for l in leads
        ]
    }


@router.post("", status_code=201)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new campaign."""
    user_id = str(current_user["id"])
    
    campaign = CampaignDB.create(
        user_id=user_id,
        name=campaign_data.name,
        description=campaign_data.description,
        template=campaign_data.template or "default",
        tone=campaign_data.tone or "professional"
    )
    
    if not campaign:
        raise HTTPException(status_code=500, detail="Failed to create campaign")
    
    return {
        "id": str(campaign["id"]),
        "name": campaign["name"],
        "description": campaign.get("description"),
        "template": campaign["template"],
        "tone": campaign["tone"],
        "status": campaign["status"],
        "created_at": campaign["created_at"]
    }


@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    campaign_data: CampaignUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a campaign."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT * FROM email_campaigns WHERE id = %s",
            (campaign_id,)
        )
        campaign = cursor.fetchone()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Build update query
    update_fields = []
    params = []
    
    if campaign_data.name is not None:
        update_fields.append("name = %s")
        params.append(campaign_data.name)
    
    if campaign_data.description is not None:
        update_fields.append("description = %s")
        params.append(campaign_data.description)
    
    if campaign_data.template is not None:
        update_fields.append("template = %s")
        params.append(campaign_data.template)
    
    if campaign_data.tone is not None:
        update_fields.append("tone = %s")
        params.append(campaign_data.tone)
    
    if campaign_data.status is not None:
        update_fields.append("status = %s")
        params.append(campaign_data.status.value)
    
    if update_fields:
        params.append(campaign_id)
        with get_db_cursor() as cursor:
            cursor.execute(
                f"UPDATE email_campaigns SET {', '.join(update_fields)} WHERE id = %s RETURNING *",
                params
            )
            updated = cursor.fetchone()
        
        return {
            "success": True,
            "campaign": {
                "id": str(updated["id"]),
                "name": updated["name"],
                "status": updated["status"]
            }
        }
    
    return {"success": True, "message": "No changes made"}


@router.delete("/{campaign_id}", response_model=SuccessResponse)
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a campaign (does not delete the leads)."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT user_id FROM email_campaigns WHERE id = %s",
            (campaign_id,)
        )
        campaign = cursor.fetchone()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM email_campaigns WHERE id = %s", (campaign_id,))
    
    return {"success": True, "message": "Campaign deleted successfully"}


# ============================================================================
# CAMPAIGN LEAD MANAGEMENT
# ============================================================================

@router.post("/{campaign_id}/leads")
async def add_leads_to_campaign(
    campaign_id: str,
    data: CampaignAddLeads,
    current_user: dict = Depends(get_current_user)
):
    """Add leads to a campaign."""
    # Verify campaign ownership
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT user_id FROM email_campaigns WHERE id = %s",
            (campaign_id,)
        )
        campaign = cursor.fetchone()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify all leads belong to user
    user_id = str(current_user["id"])
    valid_lead_ids = []
    
    for lead_id in data.lead_ids:
        lead = LeadDB.get_by_id(lead_id)
        if lead and str(lead["user_id"]) == user_id:
            valid_lead_ids.append(lead_id)
    
    # Add leads to campaign
    added = CampaignDB.add_leads(campaign_id, valid_lead_ids)
    
    return {
        "success": True,
        "added": added,
        "total_requested": len(data.lead_ids),
        "message": f"Added {added} leads to campaign"
    }


@router.delete("/{campaign_id}/leads/{lead_id}", response_model=SuccessResponse)
async def remove_lead_from_campaign(
    campaign_id: str,
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a lead from a campaign."""
    # Verify campaign ownership
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT user_id FROM email_campaigns WHERE id = %s",
            (campaign_id,)
        )
        campaign = cursor.fetchone()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    with get_db_cursor() as cursor:
        cursor.execute(
            "DELETE FROM campaign_leads WHERE campaign_id = %s AND lead_id = %s",
            (campaign_id, lead_id)
        )
        deleted = cursor.rowcount > 0
        
        # Update campaign lead count
        cursor.execute("""
            UPDATE email_campaigns 
            SET total_leads = (SELECT COUNT(*) FROM campaign_leads WHERE campaign_id = %s)
            WHERE id = %s
        """, (campaign_id, campaign_id))
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Lead not found in campaign")
    
    return {"success": True, "message": "Lead removed from campaign"}


# ============================================================================
# CAMPAIGN ACTIONS
# ============================================================================

@router.post("/{campaign_id}/start", response_model=SuccessResponse)
async def start_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Start a campaign (begin processing leads)."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT * FROM email_campaigns WHERE id = %s",
            (campaign_id,)
        )
        campaign = cursor.fetchone()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if campaign["status"] == "active":
        raise HTTPException(status_code=400, detail="Campaign is already active")
    
    # Update status
    with get_db_cursor() as cursor:
        cursor.execute(
            "UPDATE email_campaigns SET status = 'active' WHERE id = %s",
            (campaign_id,)
        )
    
    # TODO: Trigger background processing of campaign leads
    
    return {
        "success": True,
        "message": f"Campaign '{campaign['name']}' started. Leads will be processed automatically."
    }


@router.post("/{campaign_id}/pause", response_model=SuccessResponse)
async def pause_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Pause a running campaign."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT * FROM email_campaigns WHERE id = %s",
            (campaign_id,)
        )
        campaign = cursor.fetchone()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    with get_db_cursor() as cursor:
        cursor.execute(
            "UPDATE email_campaigns SET status = 'paused' WHERE id = %s",
            (campaign_id,)
        )
    
    return {"success": True, "message": "Campaign paused"}


# ============================================================================
# CAMPAIGN SCHEDULE
# ============================================================================

def _validate_schedule(scheduled_start_date, scheduled_start_time):
    """Ensure schedule is in the future (UTC). Handles both str and date/time objects."""
    from datetime import datetime, date, time

    now = datetime.utcnow()
    today = now.date()
    current_time = now.time()

    # Convert date if it's a string
    if isinstance(scheduled_start_date, str):
        scheduled_start_date = datetime.strptime(scheduled_start_date, "%Y-%m-%d").date()

    # Convert time if it's a string
    if isinstance(scheduled_start_time, str):
        # Handle HH:MM:SS or HH:MM
        parts = scheduled_start_time.split(":")
        if len(parts) == 3:
            scheduled_start_time = time(int(parts[0]), int(parts[1]), int(parts[2]))
        elif len(parts) == 2:
            scheduled_start_time = time(int(parts[0]), int(parts[1]))

    if scheduled_start_date < today:
        raise HTTPException(status_code=400, detail="scheduled_start_date must be today or in the future")
    if scheduled_start_date == today and scheduled_start_time <= current_time:
        raise HTTPException(status_code=400, detail="scheduled_start_time must be in the future when date is today")


def _get_campaign_for_user(campaign_id: str, current_user: dict):
    """Return campaign dict if found and owned by user; else raise 404/403."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM email_campaigns WHERE id = %s", (campaign_id,))
        campaign = cursor.fetchone()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if str(campaign["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    return dict(campaign)


@router.post("/{campaign_id}/schedule", response_model=SuccessResponse)
async def set_campaign_schedule(
    campaign_id: str,
    data: CampaignScheduleSet,
    current_user: dict = Depends(get_current_user)
):
    """Set scheduled_start_date, scheduled_start_time, timezone, daily_send_limit. Validates schedule."""
    _get_campaign_for_user(campaign_id, current_user)
    _validate_schedule(data.scheduled_start_date, data.scheduled_start_time)
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE email_campaigns
            SET scheduled_start_date = %s, scheduled_start_time = %s,
                timezone = %s, daily_send_limit = %s
            WHERE id = %s
        """, (data.scheduled_start_date, data.scheduled_start_time, data.timezone, data.daily_send_limit, campaign_id))
    return {"success": True, "message": "Schedule set successfully"}


@router.put("/{campaign_id}/schedule", response_model=SuccessResponse)
async def update_campaign_schedule(
    campaign_id: str,
    data: CampaignScheduleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update existing schedule (partial update)."""
    campaign = _get_campaign_for_user(campaign_id, current_user)
    if not any([data.scheduled_start_date is not None, data.scheduled_start_time is not None,
                data.timezone is not None, data.daily_send_limit is not None]):
        return {"success": True, "message": "No schedule changes provided"}
    update_fields = []
    params = []
    if data.scheduled_start_date is not None:
        update_fields.append("scheduled_start_date = %s")
        params.append(data.scheduled_start_date)
    if data.scheduled_start_time is not None:
        update_fields.append("scheduled_start_time = %s")
        params.append(data.scheduled_start_time)
    if data.timezone is not None:
        update_fields.append("timezone = %s")
        params.append(data.timezone)
    if data.daily_send_limit is not None:
        update_fields.append("daily_send_limit = %s")
        params.append(data.daily_send_limit)
    if update_fields:
        params.append(campaign_id)
        new_date = data.scheduled_start_date if data.scheduled_start_date is not None else campaign.get("scheduled_start_date")
        new_time = data.scheduled_start_time if data.scheduled_start_time is not None else campaign.get("scheduled_start_time")
        if new_date is not None and new_time is not None:
            _validate_schedule(new_date, new_time)
        with get_db_cursor() as cursor:
            cursor.execute(
                f"UPDATE email_campaigns SET {', '.join(update_fields)} WHERE id = %s",
                params
            )
    return {"success": True, "message": "Schedule updated successfully"}


@router.get("/{campaign_id}/schedule")
async def get_campaign_schedule(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get schedule for a campaign."""
    campaign = _get_campaign_for_user(campaign_id, current_user)
    return {
        "campaign_id": campaign_id,
        "scheduled_start_date": campaign.get("scheduled_start_date"),
        "scheduled_start_time": str(campaign["scheduled_start_time"]) if campaign.get("scheduled_start_time") else None,
        "timezone": campaign.get("timezone", "UTC"),
        "daily_send_limit": campaign.get("daily_send_limit", 50),
        "emails_sent_today": campaign.get("emails_sent_today", 0),
        "last_send_date": campaign.get("last_send_date"),
    }


@router.delete("/{campaign_id}/schedule", response_model=SuccessResponse)
async def delete_campaign_schedule(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel/remove schedule for a campaign."""
    _get_campaign_for_user(campaign_id, current_user)
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE email_campaigns
            SET scheduled_start_date = NULL, scheduled_start_time = NULL,
                timezone = 'UTC', daily_send_limit = 50
            WHERE id = %s
        """, (campaign_id,))
    return {"success": True, "message": "Schedule removed successfully"}


@router.post("/{campaign_id}/generate-emails")
async def generate_campaign_emails(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Generates personalized emails for all leads in a given campaign.

    This endpoint verifies campaign ownership, retrieves all leads associated with the campaign,
    obtains the latest research data for each lead, and uses the core AI email generation engine
    to create tailored outreach emails in bulk. Returns a status summary upon completion.
    Only accessible by the campaign's owner.
    """
    """Generate emails for all leads in a campaign."""
    import uuid
    from sales_agent import generate_personalized_email
    
    # Verify campaign ownership
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT * FROM email_campaigns WHERE id = %s",
            (campaign_id,)
        )
        campaign = cursor.fetchone()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get leads in campaign
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT l.* FROM leads l
            JOIN campaign_leads cl ON l.id = cl.lead_id
            WHERE cl.campaign_id = %s 
        """, (campaign_id,))
        leads = [dict(row) for row in cursor.fetchall()]
    
    if not leads:
        raise HTTPException(status_code=400, detail="No leads in this campaign")
    
    results = []
    user_id = str(current_user["id"])
    
    for lead in leads:
        try:
            # Get research for lead
            with get_db_cursor(commit=False) as cursor:
                cursor.execute(
                    "SELECT * FROM research WHERE lead_id = %s ORDER BY created_at DESC LIMIT 1",
                    (lead['id'],)
                )
                research = cursor.fetchone()
            
            # Generate email
            email_content = generate_personalized_email(
                lead_data={
                    'name': lead['name'],
                    'email': lead['email'],
                    'company': lead.get('company', ''),
                    'title': lead.get('title', '')
                },
                research_data=dict(research) if research else None
            )
            
            # Check if email generation succeeded
            if not email_content:
                raise Exception("generate_personalized_email returned None")
                
            if not isinstance(email_content, dict):
                raise Exception(f"generate_personalized_email returned invalid type: {type(email_content)}")
            
            # Save email - matching actual database schema
            email_id = str(uuid.uuid4())
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO generated_emails 
                    (id, lead_id, subject, body, status, user_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (
                    email_id,
                    lead['id'],
                    email_content.get('subject') or email_content.get('email_subject', 'Follow-up'),
                    email_content.get('body') or email_content.get('email_body', ''),
                    'draft',
                    user_id
                ))
            
            results.append({
                'lead_id': str(lead['id']),
                'lead_name': lead['name'],
                'email_id': email_id,
                'status': 'success'
            })
            
        except Exception as e:
            print(f"Error generating email for {lead['name']}: {str(e)}")
            results.append({
                'lead_id': str(lead['id']),
                'lead_name': lead['name'],
                'status': 'error',
                'error': str(e)
            })
    
    successful = len([r for r in results if r['status'] == 'success'])
    
    return {
        'campaign_id': campaign_id,
        'campaign_name': campaign['name'],
        'total_leads': len(leads),
        'successful': successful,
        'failed': len([r for r in results if r['status'] == 'error']),
        'results': results
    }


@router.get("/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed statistics for a campaign."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT * FROM email_campaigns WHERE id = %s",
            (campaign_id,)
        )
        campaign = cursor.fetchone()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if str(campaign["user_id"]) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get lead status breakdown
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT l.status, COUNT(*) as count
            FROM campaign_leads cl
            JOIN leads l ON cl.lead_id = l.id
            WHERE cl.campaign_id = %s
            GROUP BY l.status
        """, (campaign_id,))
        status_breakdown = {row["status"]: row["count"] for row in cursor.fetchall()}
    
    total = sum(status_breakdown.values())
    
    return {
        "campaign_id": str(campaign["id"]),
        "name": campaign["name"],
        "status": campaign["status"],
        "total_leads": total,
        "leads_by_status": status_breakdown,
        "emails_sent": campaign.get("emails_sent", 0),
        "emails_opened": campaign.get("emails_opened", 0),
        "replies_received": campaign.get("replies_received", 0),
        "open_rate": (campaign.get("emails_opened", 0) / campaign.get("emails_sent", 1)) * 100 if campaign.get("emails_sent", 0) > 0 else 0,
        "reply_rate": (campaign.get("replies_received", 0) / campaign.get("emails_sent", 1)) * 100 if campaign.get("emails_sent", 0) > 0 else 0
    }