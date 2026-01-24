"""
SalesAgent AI - API Server
===========================
FastAPI backend for the SalesAgent AI dashboard.

Run with: uvicorn api.main:app --reload --port 8000

Created: Week 3
Author: Shailesh Hon
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import test_connection

# Import email service router
from email_service.routes import router as email_router

# Import each route module individually (prevents circular imports)
from api.routes.auth import router as auth_router
from api.routes.leads import router as leads_router
from api.routes.emails import router as emails_router
from api.routes.campaigns import router as campaigns_router
from api.routes.analytics import router as analytics_router
from api.routes.webhooks import router as webhooks_router
from api.routes.dashboard import router as dashboard_router

# ============================================================================
# APP LIFESPAN (Startup/Shutdown)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("=" * 50)
    print("SalesAgent AI API Starting...")
    print("=" * 50)
    
    # Test database connection
    if test_connection():
        print("✓ Database connected successfully")
    else:
        print("✗ Database connection failed!")
        print("  Make sure PostgreSQL is running")
    
    print("=" * 50)
    print("API is ready at http://localhost:8000")
    print("API Docs at http://localhost:8000/docs")
    print("=" * 50)
    
    yield  # App runs here
    
    # Shutdown
    print("\n" + "=" * 50)
    print("SalesAgent AI API shutting down...")
    print("=" * 50)


# ============================================================================
# CREATE APP
# ============================================================================

app = FastAPI(
    title="SalesAgent AI",
    description="""
    AI-Powered Sales Outreach Platform
    
    ## Features
    - **Lead Management**: Import, view, and manage leads
    - **AI Research**: Automatic company research
    - **Email Generation**: Personalized AI-written emails
    - **Campaign Management**: Organize outreach campaigns
    - **Analytics**: Track performance and ROI
    - **Webhooks**: Email tracking events
    - **Dashboard**: Real-time stats
    
    ## Authentication
    All endpoints (except /auth/*) require a valid JWT token.
    Include in header: `Authorization: Bearer <your_token>`
    """,
    version="2.0.0",
    lifespan=lifespan
)

# ============================================================================
# CORS MIDDLEWARE (MUST BE BEFORE ROUTERS!)
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ============================================================================
# INCLUDE ROUTERS (Fixed prefixes - removed /api)
# ============================================================================

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(leads_router, prefix="/leads", tags=["Leads"])
app.include_router(emails_router, prefix="/emails", tags=["Emails"])
app.include_router(campaigns_router, prefix="/campaigns", tags=["Campaigns"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(email_router)


# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Welcome endpoint - API health check."""
    return {
        "message": "Welcome to SalesAgent AI API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """Check API and database health."""
    db_status = "connected" if test_connection() else "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "api": "running"
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail
        }
    )


# ============================================================================
# RUN SERVER (for direct execution)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )