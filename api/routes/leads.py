"""
Leads Routes - UPDATED with Working Research & Email Generation
================================================================
Now includes:
- POST /{lead_id}/research - Actually performs research
- POST /{lead_id}/generate-email - Generate email for a lead
- POST /{lead_id}/process - One-click: Research + Email generation
- GET /{lead_id}/research - Get research data

Author: Shailesh Hon
Updated: Week 3 - API Integration
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Auth config (same as routes/auth.py)
SECRET_KEY = "salesagent-ai-secret-key-change-in-production-2024"
ALGORITHM = "HS256"
security = HTTPBearer()


# ============================================================
# PYDANTIC MODELS
# ============================================================

class LeadCreate(BaseModel):
    name: str
    email: str
    company: str
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    priority: Optional[str] = "medium"

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class ProcessRequest(BaseModel):
    template: Optional[str] = "default"
    tone: Optional[str] = "professional"


# ============================================================
# AUTHENTICATION
# ============================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token."""
    from database import get_db_cursor
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = TRUE", (user_id,))
        user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return dict(user)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_lead_by_id(lead_id: str, user_id: str):
    """Get lead and verify ownership."""
    from database import get_db_cursor
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))
        lead = cursor.fetchone()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = dict(lead)
    if str(lead["user_id"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return lead


def format_lead_response(lead: dict) -> dict:
    """Format lead for API response."""
    return {
        "id": str(lead["id"]),
        "name": lead["name"],
        "email": lead["email"],
        "company": lead["company"],
        "job_title": lead.get("job_title"),
        "status": lead["status"],
        "priority": lead.get("priority", "medium"),
        "linkedin_url": lead.get("linkedin_url"),
        "created_at": str(lead["created_at"]),
        "updated_at": str(lead.get("updated_at", lead["created_at"]))
    }


# ============================================================
# LEAD CRUD ROUTES
# ============================================================

@router.get("")
async def list_leads(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get all leads for the current user."""
    from database import get_db_cursor
    
    user_id = str(current_user["id"])
    offset = (page - 1) * per_page
    
    # Build query with filters
    query = "SELECT * FROM leads WHERE user_id = %s"
    params = [user_id]
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    if priority:
        query += " AND priority = %s"
        params.append(priority)
    
    if search:
        query += " AND (name ILIKE %s OR email ILIKE %s OR company ILIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, tuple(params))
        leads = cursor.fetchall()
        
        # Get total count
        count_query = "SELECT COUNT(*) as count FROM leads WHERE user_id = %s"
        count_params = [user_id]
        if status:
            count_query += " AND status = %s"
            count_params.append(status)
        if priority:
            count_query += " AND priority = %s"
            count_params.append(priority)
        if search:
            count_query += " AND (name ILIKE %s OR email ILIKE %s OR company ILIKE %s)"
            count_params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        cursor.execute(count_query, tuple(count_params))
        total = cursor.fetchone()["count"]
    
    return {
        "leads": [format_lead_response(dict(lead)) for lead in leads],
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/stats/summary")
async def get_leads_summary(current_user: dict = Depends(get_current_user)):
    """Get lead statistics."""
    from database import get_db_cursor
    
    user_id = str(current_user["id"])
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM leads WHERE user_id = %s 
            GROUP BY status
        """, (user_id,))
        rows = cursor.fetchall()
    
    by_status = {row["status"]: row["count"] for row in rows}
    return {"total": sum(by_status.values()), "by_status": by_status}


@router.get("/{lead_id}")
async def get_lead(lead_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific lead."""
    lead = get_lead_by_id(lead_id, str(current_user["id"]))
    return format_lead_response(lead)


@router.post("")
async def create_lead(
    lead_data: LeadCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new lead."""
    from database import get_db_cursor
    
    user_id = str(current_user["id"])
    
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO leads (user_id, name, email, company, job_title, linkedin_url, priority, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'api')
            RETURNING *
        """, (user_id, lead_data.name, lead_data.email.lower(), lead_data.company, 
              lead_data.job_title, lead_data.linkedin_url, lead_data.priority))
        lead = dict(cursor.fetchone())
    
    return format_lead_response(lead)


@router.put("/{lead_id}")
async def update_lead(
    lead_id: str,
    lead_data: LeadUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a lead."""
    from database import get_db_cursor
    
    # Verify ownership
    get_lead_by_id(lead_id, str(current_user["id"]))
    
    # Build update query
    updates = []
    params = []
    
    if lead_data.name is not None:
        updates.append("name = %s")
        params.append(lead_data.name)
    if lead_data.email is not None:
        updates.append("email = %s")
        params.append(lead_data.email.lower())
    if lead_data.company is not None:
        updates.append("company = %s")
        params.append(lead_data.company)
    if lead_data.job_title is not None:
        updates.append("job_title = %s")
        params.append(lead_data.job_title)
    if lead_data.status is not None:
        updates.append("status = %s")
        params.append(lead_data.status)
    if lead_data.priority is not None:
        updates.append("priority = %s")
        params.append(lead_data.priority)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    updates.append("updated_at = NOW()")
    params.append(lead_id)
    
    with get_db_cursor() as cursor:
        cursor.execute(f"""
            UPDATE leads SET {', '.join(updates)}
            WHERE id = %s
            RETURNING *
        """, tuple(params))
        lead = dict(cursor.fetchone())
    
    return format_lead_response(lead)


@router.delete("/{lead_id}")
async def delete_lead(lead_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a lead."""
    from database import get_db_cursor
    
    # Verify ownership
    get_lead_by_id(lead_id, str(current_user["id"]))
    
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
    
    return {"success": True, "message": "Lead deleted"}


# ============================================================
# RESEARCH ROUTES (NEW - WORKING!)
# ============================================================

@router.post("/{lead_id}/research")
async def research_lead(
    lead_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    🔬 Perform research on a lead's company.
    
    This actually calls the research function from sales_agent.py!
    """
    from database import get_db_cursor, ResearchDB, LeadDB
    
    # Get lead and verify ownership
    lead = get_lead_by_id(lead_id, str(current_user["id"]))
    company = lead["company"]
    
    logger.info(f"🔬 Starting research for lead {lead_id}: {lead['name']} at {company}")
    
    try:
        # Import the research function from sales_agent
        from sales_agent import research_company, CONFIG
        
        # Perform research (this calls Serper API + Claude Haiku)
        research_data = research_company(company, str(current_user["id"]))
        
        # Check if it was cached
        was_cached = research_data.get('cached', False)
        
        if was_cached:
            logger.info(f"📦 Research loaded from cache for {company}")
        else:
            # Save fresh research to database
            ResearchDB.create(
                lead_id=lead_id,
                company_name=company,
                ai_summary=research_data.get('summary', ''),
                company_description=research_data.get('details', {}).get('description'),
                industry=research_data.get('details', {}).get('industry'),
                company_size=research_data.get('details', {}).get('size'),
                funding_info=research_data.get('details', {}).get('funding'),
                search_results=research_data.get('search_results', []),
                news_items=research_data.get('news', []),
                research_depth=CONFIG.get('research_settings', {}).get('depth', 'standard')
            )
            logger.info(f"✅ Fresh research saved for {company}")
        
        # Update lead status
        LeadDB.update_status(lead_id, 'researched')
        
        return {
            "success": True,
            "lead_id": lead_id,
            "company": company,
            "cached": was_cached,
            "summary": research_data.get('summary', ''),
            "details": research_data.get('details', {}),
            "news": research_data.get('news', [])[:3],
            "message": f"Research {'loaded from cache' if was_cached else 'completed'} for {company}"
        }
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Could not import sales_agent module. Make sure sales_agent.py is in the project root."
        )
    except Exception as e:
        logger.error(f"Research failed for {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@router.get("/{lead_id}/research")
async def get_research(lead_id: str, current_user: dict = Depends(get_current_user)):
    """
    📊 Get existing research data for a lead.
    """
    from database import ResearchDB
    
    # Verify ownership
    get_lead_by_id(lead_id, str(current_user["id"]))
    
    # Get research from database
    research = ResearchDB.get_by_lead_id(lead_id)
    
    if not research:
        return {
            "success": False,
            "lead_id": lead_id,
            "message": "No research data found. Run POST /{lead_id}/research first."
        }
    
    return {
        "success": True,
        "lead_id": lead_id,
        "research_id": str(research["id"]),
        "company_name": research.get("company_name"),
        "summary": research.get("ai_summary"),
        "industry": research.get("industry"),
        "company_size": research.get("company_size"),
        "funding_info": research.get("funding_info"),
        "news": research.get("news_items", []),
        "created_at": str(research.get("created_at"))
    }


# ============================================================
# EMAIL GENERATION ROUTE (NEW!)
# ============================================================

@router.post("/{lead_id}/generate-email")
async def generate_email_for_lead(
    lead_id: str,
    request: ProcessRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    ✉️ Generate a personalized email for a lead.
    
    Requires research to be done first!
    """
    from database import ResearchDB, EmailDB, LeadDB
    
    # Get lead and verify ownership
    lead = get_lead_by_id(lead_id, str(current_user["id"]))
    
    # Check if research exists
    research = ResearchDB.get_by_lead_id(lead_id)
    if not research:
        raise HTTPException(
            status_code=400,
            detail="Lead must be researched first. Call POST /{lead_id}/research first."
        )
    
    logger.info(f"✉️ Generating email for lead {lead_id}: {lead['name']}")
    
    try:
        # Import email generation function
        from sales_agent import generate_personalized_email, CONFIG
        
        # Prepare data
        lead_data = {
            'name': lead['name'],
            'email': lead['email'],
            'company': lead['company'],
            'job_title': lead.get('job_title', '')
        }
        
        research_data = {
            'summary': research.get('ai_summary', ''),
            'details': {
                'description': research.get('company_description', ''),
                'industry': research.get('industry', ''),
                'funding': research.get('funding_info', '')
            }
        }
        
        # Generate email (uses Claude Sonnet for best quality)
        email_result = generate_personalized_email(lead_data, research_data)
        
        if not email_result:
            raise HTTPException(status_code=500, detail="Email generation failed")
        
        # Save to database
        email_record = EmailDB.create(
            lead_id=lead_id,
            subject=email_result.get('subject', ''),
            body=email_result['body'],
            template_used=request.template if request else CONFIG['email_settings']['template'],
            tone=request.tone if request else CONFIG['email_settings']['tone'],
            research_id=str(research['id'])
        )
        
        # Update lead status
        LeadDB.update_status(lead_id, 'email_drafted')
        
        logger.info(f"✅ Email generated for {lead['name']}")
        
        return {
            "success": True,
            "lead_id": lead_id,
            "email_id": str(email_record['id']) if email_record else None,
            "subject": email_result.get('subject', ''),
            "body": email_result['body'],
            "message": f"Email generated for {lead['name']}"
        }
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(status_code=500, detail="Could not import sales_agent module")
    except Exception as e:
        logger.error(f"Email generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email generation failed: {str(e)}")


# ============================================================
# ONE-CLICK PROCESS ROUTE (NEW!)
# ============================================================

@router.post("/{lead_id}/process")
async def process_lead(
    lead_id: str,
    request: ProcessRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    🚀 ONE-CLICK: Research + Email Generation
    
    This is the magic endpoint that does everything in one call!
    """
    from database import ResearchDB, EmailDB, LeadDB
    
    # Get lead and verify ownership
    lead = get_lead_by_id(lead_id, str(current_user["id"]))
    user_id = str(current_user["id"])
    
    logger.info(f"🚀 Processing lead {lead_id}: {lead['name']} at {lead['company']}")
    
    results = {
        "lead_id": lead_id,
        "lead_name": lead["name"],
        "company": lead["company"],
        "research": None,
        "email": None,
        "success": False
    }
    
    try:
        from sales_agent import research_company, generate_personalized_email, CONFIG
        
        # Step 1: Research
        logger.info(f"Step 1: Researching {lead['company']}...")
        research_data = research_company(lead["company"], user_id)
        was_cached = research_data.get('cached', False)
        
        if not was_cached:
            ResearchDB.create(
                lead_id=lead_id,
                company_name=lead["company"],
                ai_summary=research_data.get('summary', ''),
                company_description=research_data.get('details', {}).get('description'),
                industry=research_data.get('details', {}).get('industry'),
                company_size=research_data.get('details', {}).get('size'),
                funding_info=research_data.get('details', {}).get('funding'),
                search_results=research_data.get('search_results', []),
                news_items=research_data.get('news', []),
                research_depth=CONFIG.get('research_settings', {}).get('depth', 'standard')
            )
        
        LeadDB.update_status(lead_id, 'researched')
        
        results["research"] = {
            "success": True,
            "cached": was_cached,
            "summary": research_data.get('summary', '')[:200] + "..."
        }
        logger.info(f"✅ Research {'loaded from cache' if was_cached else 'completed'}")
        
        # Step 2: Generate Email
        logger.info(f"Step 2: Generating email for {lead['name']}...")
        
        lead_data = {
            'name': lead['name'],
            'email': lead['email'],
            'company': lead['company'],
            'job_title': lead.get('job_title', '')
        }
        
        email_result = generate_personalized_email(lead_data, research_data)
        
        if email_result:
            research_record = ResearchDB.get_by_lead_id(lead_id)
            research_id = str(research_record['id']) if research_record else None
            
            email_record = EmailDB.create(
                lead_id=lead_id,
                subject=email_result.get('subject', ''),
                body=email_result['body'],
                template_used=request.template if request else CONFIG['email_settings']['template'],
                tone=request.tone if request else CONFIG['email_settings']['tone'],
                research_id=research_id
            )
            
            LeadDB.update_status(lead_id, 'email_drafted')
            
            results["email"] = {
                "success": True,
                "email_id": str(email_record['id']) if email_record else None,
                "subject": email_result.get('subject', ''),
                "preview": email_result['body'][:150] + "..."
            }
            logger.info(f"✅ Email generated")
        else:
            results["email"] = {"success": False, "error": "Email generation returned empty"}
        
        results["success"] = True
        results["message"] = f"Successfully processed {lead['name']}"
        
        return results
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(status_code=500, detail="Could not import sales_agent module")
    except Exception as e:
        logger.error(f"Process failed: {e}")
        results["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ============================================================
# BULK OPERATIONS
# ============================================================

@router.post("/bulk/status")
async def bulk_update_status(
    lead_ids: list,
    status: str,
    current_user: dict = Depends(get_current_user)
):
    """Update status for multiple leads."""
    from database import get_db_cursor
    
    user_id = str(current_user["id"])
    updated = 0
    
    with get_db_cursor() as cursor:
        for lead_id in lead_ids:
            cursor.execute("""
                UPDATE leads SET status = %s, updated_at = NOW()
                WHERE id = %s AND user_id = %s
            """, (status, lead_id, user_id))
            updated += cursor.rowcount
    
    return {"success": True, "updated": updated}


@router.post("/bulk/delete")
async def bulk_delete_leads(
    lead_ids: list,
    current_user: dict = Depends(get_current_user)
):
    """Delete multiple leads."""
    from database import get_db_cursor
    
    user_id = str(current_user["id"])
    deleted = 0
    
    with get_db_cursor() as cursor:
        for lead_id in lead_ids:
            cursor.execute("""
                DELETE FROM leads WHERE id = %s AND user_id = %s
            """, (lead_id, user_id))
            deleted += cursor.rowcount
    
    return {"success": True, "deleted": deleted}


# ============================================================
# IMPORT ROUTES (Placeholders for now)
# ============================================================

@router.post("/import/csv")
async def import_csv(current_user: dict = Depends(get_current_user)):
    """Import leads from CSV file."""
    return {"message": "CSV import - coming soon"}


@router.post("/import/bulk")
async def import_bulk(current_user: dict = Depends(get_current_user)):
    """Bulk import leads."""
    return {"message": "Bulk import - coming soon"}
