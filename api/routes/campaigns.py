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
    CampaignAddLeads, SuccessResponse
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
