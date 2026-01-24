"""
API Models (Pydantic Schemas)
=============================
Define the shape of data for API requests and responses.

MENTOR NOTE: Pydantic models give you automatic validation, documentation,
and type hints. This catches errors early and makes your API self-documenting.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class LeadStatus(str, Enum):
    NEW = "new"
    RESEARCHED = "researched"
    EMAIL_DRAFTED = "email_drafted"
    EMAIL_SENT = "email_sent"
    REPLIED = "replied"
    CONVERTED = "converted"
    ARCHIVED = "archived"


class LeadPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EmailStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    REPLIED = "replied"
    BOUNCED = "bounced"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


# ============================================================================
# AUTH MODELS
# ============================================================================

class UserLogin(BaseModel):
    """Login request."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserRegister(BaseModel):
    """Registration request."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Minimum 6 characters")
    full_name: str = Field(..., min_length=2)
    company_name: Optional[str] = None


class Token(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User data response (excludes password)."""
    id: str
    email: str
    full_name: str
    company_name: Optional[str]
    plan_type: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


# ============================================================================
# LEAD MODELS
# ============================================================================

class LeadCreate(BaseModel):
    """Create a new lead."""
    name: str = Field(..., min_length=2)
    email: EmailStr
    company: str = Field(..., min_length=1)
    job_title: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    priority: LeadPriority = LeadPriority.MEDIUM
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class LeadUpdate(BaseModel):
    """Update an existing lead."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    status: Optional[LeadStatus] = None
    priority: Optional[LeadPriority] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class LeadResponse(BaseModel):
    """Lead data response."""
    id: str
    name: str
    email: str
    company: str
    job_title: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    website: Optional[str]
    status: str
    priority: str
    source: Optional[str]
    tags: Optional[List[str]]
    custom_fields: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    last_contacted_at: Optional[datetime]

    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    """Paginated list of leads."""
    leads: List[LeadResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class LeadBulkImport(BaseModel):
    """Bulk import leads."""
    leads: List[LeadCreate]


class LeadBulkImportResponse(BaseModel):
    """Response for bulk import."""
    imported: int
    skipped: int
    errors: List[str]


# ============================================================================
# RESEARCH MODELS
# ============================================================================

class ResearchResponse(BaseModel):
    """Research data for a lead."""
    id: str
    lead_id: str
    company_name: str
    company_description: Optional[str]
    industry: Optional[str]
    company_size: Optional[str]
    funding_info: Optional[str]
    ai_summary: Optional[str]
    news_items: Optional[List[Dict]]
    research_depth: str
    created_at: datetime
    updated_at: datetime


# ============================================================================
# EMAIL MODELS
# ============================================================================

class EmailGenerate(BaseModel):
    """Request to generate email for a lead."""
    lead_id: str
    template: Optional[str] = "default"  # default, brief, consultative, partnership
    tone: Optional[str] = "professional"  # casual, professional, formal


class EmailUpdate(BaseModel):
    """Update an email."""
    subject: Optional[str] = None
    body: Optional[str] = None
    status: Optional[EmailStatus] = None


class EmailResponse(BaseModel):
    """Email data response."""
    id: str
    lead_id: str
    subject: Optional[str]
    body: str
    template_used: str
    tone: str
    version: int
    is_current: bool
    status: str
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    replied_at: Optional[datetime]
    open_count: int
    click_count: int
    created_at: datetime


class EmailWithLeadResponse(BaseModel):
    """Email with associated lead data."""
    email: EmailResponse
    lead: LeadResponse


# ============================================================================
# CAMPAIGN MODELS
# ============================================================================

class CampaignCreate(BaseModel):
    """Create a new campaign."""
    name: str = Field(..., min_length=2)
    description: Optional[str] = None
    template: Optional[str] = "default"
    tone: Optional[str] = "professional"


class CampaignUpdate(BaseModel):
    """Update a campaign."""
    name: Optional[str] = None
    description: Optional[str] = None
    template: Optional[str] = None
    tone: Optional[str] = None
    status: Optional[CampaignStatus] = None


class CampaignResponse(BaseModel):
    """Campaign data response."""
    id: str
    name: str
    description: Optional[str]
    template: str
    tone: str
    status: str
    total_leads: int
    emails_sent: int
    emails_opened: int
    replies_received: int
    created_at: datetime
    updated_at: datetime


class CampaignAddLeads(BaseModel):
    """Add leads to a campaign."""
    lead_ids: List[str]


# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_leads: int
    leads_by_status: Dict[str, int]
    total_emails_sent: int
    total_opens: int
    total_replies: int
    open_rate: float
    reply_rate: float
    total_campaigns: int
    active_campaigns: int


class AgentRunResponse(BaseModel):
    """Agent run history."""
    id: str
    run_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[float]
    leads_processed: int
    leads_skipped: int
    leads_failed: int
    success_rate: Optional[float]
    status: str


class AnalyticsOverview(BaseModel):
    """Analytics overview response."""
    dashboard: DashboardStats
    recent_runs: List[AgentRunResponse]
    performance_trend: Dict[str, Any]


# ============================================================================
# AGENT MODELS
# ============================================================================

class AgentRunRequest(BaseModel):
    """Request to run the agent."""
    lead_ids: Optional[List[str]] = None  # Specific leads, or None for all unprocessed
    limit: Optional[int] = 50
    template: Optional[str] = "default"
    tone: Optional[str] = "professional"


class AgentRunStatusResponse(BaseModel):
    """Status of an agent run."""
    run_id: str
    status: str  # running, completed, failed
    leads_processed: int
    leads_remaining: int
    current_lead: Optional[str]
    started_at: datetime
    estimated_completion: Optional[datetime]


# ============================================================================
# GENERIC RESPONSES
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Generic error response."""
    error: bool = True
    message: str
    details: Optional[Dict[str, Any]] = None
