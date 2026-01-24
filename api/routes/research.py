"""
Research Routes for SalesAgent AI
==================================
Handles company research operations using Claude AI.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional
from pydantic import BaseModel
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ResearchRequest(BaseModel):
    lead_id: str
    force_refresh: bool = False


class BulkResearchRequest(BaseModel):
    lead_ids: list[str]
    force_refresh: bool = False


# ============================================================================
# RESEARCH ENDPOINTS
# ============================================================================

@router.post("/research/{lead_id}")
async def research_lead(
    lead_id: str,
    background_tasks: BackgroundTasks,
    force_refresh: bool = False
):
    """Research a single lead's company using AI."""
    try:
        from database import LeadDB, ResearchDB
        from sales_agent import research_company
        
        # Get lead from database
        lead = LeadDB.get_by_id(lead_id)
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Check if research already exists
        if not force_refresh:
            existing_research = ResearchDB.get_by_lead_id(lead_id)
            if existing_research:
                return {
                    "success": True,
                    "message": "Research already exists",
                    "research": {
                        "id": str(existing_research["id"]),
                        "lead_id": lead_id,
                        "company": lead["company"],
                        "summary": existing_research.get("ai_summary", ""),
                        "cached": True
                    }
                }
        
        logger.info(f"Starting research for {lead['company']}")
        
        # Perform research
        research_result = research_company(
            company_name=lead["company"],
            user_id=str(lead.get("user_id", "default"))
        )
        
        # Save to database
        saved_research = ResearchDB.create(
            lead_id=lead_id,
            company_info=research_result.get("details", {}),
            ai_summary=research_result.get("summary", ""),
            search_results=research_result.get("search_results", []),
            news_items=research_result.get("news", [])
        )
        
        # Update lead status
        LeadDB.update_status(lead_id, "researched")
        
        return {
            "success": True,
            "message": f"Research completed for {lead['company']}",
            "research": {
                "id": str(saved_research["id"]),
                "lead_id": lead_id,
                "company": lead["company"],
                "summary": saved_research.get("ai_summary", ""),
                "cached": False
            }
        }
        
    except Exception as e:
        logger.error(f"Research error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/research/{lead_id}")
async def get_research(lead_id: str):
    """Get existing research for a lead."""
    try:
        from database import ResearchDB, LeadDB
        
        lead = LeadDB.get_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        research = ResearchDB.get_by_lead_id(lead_id)
        if not research:
            raise HTTPException(status_code=404, detail="No research found")
        
        return {
            "success": True,
            "research": {
                "id": str(research["id"]),
                "company": lead["company"],
                "summary": research.get("ai_summary", ""),
                "created_at": str(research["created_at"])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
