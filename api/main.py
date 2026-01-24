"""
SalesAgent AI - API Server - FRESH BUILD
=========================================
FastAPI backend for the SalesAgent AI dashboard.

Run with: uvicorn api.main:app --reload --port 8000

Version: 3.0 (Fresh Build)
Author: Shailesh Hon
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import test_connection

# Import route modules
from api.routes.auth import router as auth_router
from api.routes.leads import router as leads_router
from api.routes.emails import router as emails_router
from api.routes.campaigns import router as campaigns_router
from api.routes.analytics import router as analytics_router
from api.routes.webhooks import router as webhooks_router
from api.routes.dashboard import router as dashboard_router
from api.routes.research import router as research_router

# Import email service router
from email_service.routes import router as email_router

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
        print("Database connected successfully")
    else:
        print("Database connection failed!")
        print("   Make sure PostgreSQL is running")
    
    print("=" * 50)
    print("API is ready at http://localhost:8000")
    print("API Docs at http://localhost:8000/docs")
    print("=" * 50)
    
    yield  # App runs here
    
    # Shutdown
    print("\nSalesAgent AI API shutting down...")


# ============================================================================
# CREATE APP
# ============================================================================

app = FastAPI(
    title="SalesAgent AI",
    description="AI-Powered Sales Outreach Platform",
    version="3.0.0",
    lifespan=lifespan
)

# ============================================================================
# CORS MIDDLEWARE (Allow frontend to connect)
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
)

# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

# Auth routes at /auth (no /api prefix)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# API routes at /api/*
app.include_router(leads_router, prefix="/api/leads", tags=["Leads"])
app.include_router(emails_router, prefix="/api/emails", tags=["Emails"])
app.include_router(campaigns_router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(webhooks_router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(research_router, prefix="/api/research", tags=["research"])

# Email service router
app.include_router(email_router)

# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Welcome endpoint - API health check."""
    return {
        "message": "Welcome to SalesAgent AI API",
        "version": "3.0.0",
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
# ERROR HANDLERS - FIXED!
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions properly."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": str(exc)
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