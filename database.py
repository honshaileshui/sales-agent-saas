"""
Database Module for SalesAgent AI
==================================
Handles all PostgreSQL database operations.
Replaces Google Sheets as the primary data store.

Created: Week 2 - Database Integration
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
import logging
import json
import os

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'salesagent_db',
    'user': 'postgres',
    'password': os.getenv('DB_PASSWORD', '')
}

# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

class DatabaseConnection:
    """Manages PostgreSQL database connections."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connection = None
        return cls._instance
    
    def get_connection(self):
        """Get or create a database connection."""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(**DB_CONFIG)
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        return self._connection
    
    def close(self):
        """Close the database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed")


@contextmanager
def get_db_cursor(commit=True):
    """
    Context manager for database operations.
    Automatically handles commits and rollbacks.
    
    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
    """
    db = DatabaseConnection()
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        cursor.close()


def test_connection() -> bool:
    """Test if database connection works."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


# ============================================================================
# USER OPERATIONS
# ============================================================================

class UserDB:
    """Database operations for users table."""
    
    @staticmethod
    def create(email: str, password_hash: str, full_name: str, 
               company_name: str = None, plan_type: str = 'free') -> Optional[Dict]:
        """Create a new user."""
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, company_name, plan_type)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            """, (email, password_hash, full_name, company_name, plan_type))
            user = cursor.fetchone()
            logger.info(f"Created user: {email}")
            return dict(user) if user else None
    
    @staticmethod
    def get_by_id(user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    @staticmethod
    def get_by_email(email: str) -> Optional[Dict]:
        """Get user by email."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    @staticmethod
    def update_last_login(user_id: str) -> bool:
        """Update user's last login timestamp."""
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s
            """, (user_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def get_first_user() -> Optional[Dict]:
        """Get the first user (for testing/single-user mode)."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM users ORDER BY created_at LIMIT 1")
            user = cursor.fetchone()
            return dict(user) if user else None


# ============================================================================
# LEAD OPERATIONS
# ============================================================================

class LeadDB:
    """Database operations for leads table."""
    
    @staticmethod
    def create(user_id: str, name: str, email: str, company: str,
               job_title: str = None, phone: str = None,
               linkedin_url: str = None, source: str = 'manual',
               tags: List[str] = None, custom_fields: Dict = None) -> Optional[Dict]:
        """Create a new lead."""
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO leads (user_id, name, email, company, job_title, 
                                   phone, linkedin_url, source, tags, custom_fields)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (user_id, name, email, company, job_title, phone, 
                  linkedin_url, source, tags, Json(custom_fields or {})))
            lead = cursor.fetchone()
            logger.info(f"Created lead: {name} ({email})")
            return dict(lead) if lead else None
    
    @staticmethod
    def get_by_id(lead_id: str) -> Optional[Dict]:
        """Get lead by ID."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))
            lead = cursor.fetchone()
            return dict(lead) if lead else None
    
    @staticmethod
    def get_all_for_user(user_id: str, status: str = None, 
                         limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all leads for a user, optionally filtered by status."""
        with get_db_cursor(commit=False) as cursor:
            if status:
                cursor.execute("""
                    SELECT * FROM leads 
                    WHERE user_id = %s AND status = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (user_id, status, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM leads 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (user_id, limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_unprocessed(user_id: str, limit: int = 50) -> List[Dict]:
        """Get leads that haven't been processed yet."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM leads 
                WHERE user_id = %s AND status = 'new'
                ORDER BY priority DESC, created_at ASC
                LIMIT %s
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update_status(lead_id: str, status: str) -> bool:
        """Update lead status."""
        valid_statuses = ['new', 'researched', 'email_drafted', 'email_sent', 
                         'replied', 'converted', 'archived']
        if status not in valid_statuses:
            logger.error(f"Invalid status: {status}")
            return False
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE leads SET status = %s WHERE id = %s
            """, (status, lead_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def update(lead_id: str, **fields) -> Optional[Dict]:
        """Update lead fields dynamically."""
        if not fields:
            return None
        
        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        for key, value in fields.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        values.append(lead_id)
        
        query = f"UPDATE leads SET {', '.join(set_clauses)} WHERE id = %s RETURNING *"
        
        with get_db_cursor() as cursor:
            cursor.execute(query, values)
            lead = cursor.fetchone()
            return dict(lead) if lead else None
    
    @staticmethod
    def delete(lead_id: str) -> bool:
        """Delete a lead."""
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted lead: {lead_id}")
            return deleted
    
    @staticmethod
    def count_by_status(user_id: str) -> Dict[str, int]:
        """Get count of leads grouped by status."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM leads 
                WHERE user_id = %s 
                GROUP BY status
            """, (user_id,))
            return {row['status']: row['count'] for row in cursor.fetchall()}
    
    @staticmethod
    def bulk_create(user_id: str, leads_data: List[Dict], source: str = 'csv_import') -> int:
        """
        Bulk insert multiple leads.
        Returns count of successfully inserted leads.
        """
        inserted = 0
        with get_db_cursor() as cursor:
            for lead in leads_data:
                try:
                    cursor.execute("""
                        INSERT INTO leads (user_id, name, email, company, job_title, source)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, email) DO NOTHING
                    """, (user_id, lead.get('name'), lead.get('email'), 
                          lead.get('company'), lead.get('job_title'), source))
                    if cursor.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    logger.warning(f"Failed to insert lead {lead.get('email')}: {e}")
        
        logger.info(f"Bulk inserted {inserted} leads")
        return inserted


# ============================================================================
# RESEARCH RESULTS OPERATIONS
# ============================================================================

class ResearchDB:
    """Database operations for research_results table."""
    
    @staticmethod
    def create(lead_id: str, company_name: str, ai_summary: str,
               company_description: str = None, industry: str = None,
               company_size: str = None, funding_info: str = None,
               search_results: List = None, news_items: List = None,
               research_depth: str = 'standard') -> Optional[Dict]:
        """Create or update research results for a lead."""
        with get_db_cursor() as cursor:
            # Use UPSERT - insert or update if exists
            cursor.execute("""
                INSERT INTO research_results 
                (lead_id, company_name, ai_summary, company_description, industry,
                 company_size, funding_info, search_results, news_items, research_depth)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (lead_id) DO UPDATE SET
                    ai_summary = EXCLUDED.ai_summary,
                    company_description = EXCLUDED.company_description,
                    industry = EXCLUDED.industry,
                    company_size = EXCLUDED.company_size,
                    funding_info = EXCLUDED.funding_info,
                    search_results = EXCLUDED.search_results,
                    news_items = EXCLUDED.news_items,
                    research_depth = EXCLUDED.research_depth,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING *
            """, (lead_id, company_name, ai_summary, company_description, industry,
                  company_size, funding_info, Json(search_results or []), 
                  Json(news_items or []), research_depth))
            result = cursor.fetchone()
            logger.info(f"Saved research for lead: {lead_id}")
            return dict(result) if result else None
    
    @staticmethod
    def get_by_lead_id(lead_id: str) -> Optional[Dict]:
        """Get research results for a specific lead."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM research_results WHERE lead_id = %s
            """, (lead_id,))
            result = cursor.fetchone()
            return dict(result) if result else None


# ============================================================================
# GENERATED EMAILS OPERATIONS
# ============================================================================

class EmailDB:
    """Database operations for generated_emails table."""
    
    @staticmethod
    def create(lead_id: str, body: str, subject: str = None,
               template_used: str = 'default', tone: str = 'professional',
               research_id: str = None) -> Optional[Dict]:
        """Create a new generated email."""
        with get_db_cursor() as cursor:
            # First, mark any existing emails for this lead as not current
            cursor.execute("""
                UPDATE generated_emails SET is_current = FALSE 
                WHERE lead_id = %s AND is_current = TRUE
            """, (lead_id,))
            
            # Get the next version number
            cursor.execute("""
                SELECT COALESCE(MAX(version), 0) + 1 as next_version 
                FROM generated_emails WHERE lead_id = %s
            """, (lead_id,))
            next_version = cursor.fetchone()['next_version']
            
            # Insert new email
            cursor.execute("""
                INSERT INTO generated_emails 
                (lead_id, research_id, subject, body, template_used, tone, version, is_current)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                RETURNING *
            """, (lead_id, research_id, subject, body, template_used, tone, next_version))
            
            email = cursor.fetchone()
            logger.info(f"Created email v{next_version} for lead: {lead_id}")
            return dict(email) if email else None
    
    @staticmethod
    def get_current_for_lead(lead_id: str) -> Optional[Dict]:
        """Get the current (latest) email for a lead."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM generated_emails 
                WHERE lead_id = %s AND is_current = TRUE
            """, (lead_id,))
            email = cursor.fetchone()
            return dict(email) if email else None
    
    @staticmethod
    def get_all_versions(lead_id: str) -> List[Dict]:
        """Get all email versions for a lead."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM generated_emails 
                WHERE lead_id = %s 
                ORDER BY version DESC
            """, (lead_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update_status(email_id: str, status: str) -> bool:
        """Update email status."""
        valid_statuses = ['draft', 'approved', 'sent', 'delivered', 
                         'opened', 'replied', 'bounced']
        if status not in valid_statuses:
            return False
        
        with get_db_cursor() as cursor:
            update_fields = "status = %s"
            values = [status]
            
            # Set timestamp based on status
            if status == 'sent':
                update_fields += ", sent_at = CURRENT_TIMESTAMP"
            elif status == 'opened':
                update_fields += ", opened_at = CURRENT_TIMESTAMP, open_count = open_count + 1"
            elif status == 'replied':
                update_fields += ", replied_at = CURRENT_TIMESTAMP"
            
            values.append(email_id)
            cursor.execute(f"""
                UPDATE generated_emails SET {update_fields} WHERE id = %s
            """, values)
            return cursor.rowcount > 0


# ============================================================================
# AGENT RUNS OPERATIONS
# ============================================================================

class AgentRunDB:
    """Database operations for agent_runs table."""
    
    @staticmethod
    def create(user_id: str, run_id: str, config_snapshot: Dict = None) -> Optional[Dict]:
        """Create a new agent run record."""
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO agent_runs (user_id, run_id, started_at, config_snapshot, status)
                VALUES (%s, %s, CURRENT_TIMESTAMP, %s, 'running')
                RETURNING *
            """, (user_id, run_id, Json(config_snapshot or {})))
            run = cursor.fetchone()
            logger.info(f"Started agent run: {run_id}")
            return dict(run) if run else None
    
    @staticmethod
    def complete(run_id: str, metrics: Dict) -> Optional[Dict]:
        """Mark an agent run as complete with metrics."""
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE agent_runs SET
                    ended_at = CURRENT_TIMESTAMP,
                    duration_seconds = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)),
                    leads_processed = %s,
                    leads_skipped = %s,
                    leads_failed = %s,
                    research_successes = %s,
                    research_failures = %s,
                    email_gen_successes = %s,
                    email_gen_failures = %s,
                    success_rate = %s,
                    avg_lead_processing_time = %s,
                    errors = %s,
                    status = 'completed'
                WHERE run_id = %s
                RETURNING *
            """, (
                metrics.get('leads_processed', 0),
                metrics.get('leads_skipped', 0),
                metrics.get('leads_failed', 0),
                metrics.get('research_successes', 0),
                metrics.get('research_failures', 0),
                metrics.get('email_gen_successes', 0),
                metrics.get('email_gen_failures', 0),
                metrics.get('success_rate', 0),
                metrics.get('avg_lead_processing_time', 0),
                Json(metrics.get('errors', [])),
                run_id
            ))
            run = cursor.fetchone()
            logger.info(f"Completed agent run: {run_id}")
            return dict(run) if run else None
    
    @staticmethod
    def get_recent(user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent agent runs for a user."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM agent_runs 
                WHERE user_id = %s 
                ORDER BY started_at DESC 
                LIMIT %s
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_summary_stats(user_id: str) -> Dict:
        """Get aggregate statistics across all runs."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_runs,
                    SUM(leads_processed) as total_leads_processed,
                    SUM(leads_skipped) as total_leads_skipped,
                    SUM(leads_failed) as total_leads_failed,
                    AVG(success_rate) as avg_success_rate,
                    AVG(avg_lead_processing_time) as avg_processing_time,
                    MIN(started_at) as first_run,
                    MAX(started_at) as last_run
                FROM agent_runs 
                WHERE user_id = %s AND status = 'completed'
            """, (user_id,))
            result = cursor.fetchone()
            return dict(result) if result else {}


# ============================================================================
# CAMPAIGN OPERATIONS
# ============================================================================

class CampaignDB:
    """Database operations for email_campaigns table."""
    
    @staticmethod
    def create(user_id: str, name: str, description: str = None,
               template: str = 'default', tone: str = 'professional') -> Optional[Dict]:
        """Create a new campaign."""
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO email_campaigns (user_id, name, description, template, tone)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            """, (user_id, name, description, template, tone))
            campaign = cursor.fetchone()
            logger.info(f"Created campaign: {name}")
            return dict(campaign) if campaign else None
    
    @staticmethod
    def get_all_for_user(user_id: str) -> List[Dict]:
        """Get all campaigns for a user."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM email_campaigns 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def add_leads(campaign_id: str, lead_ids: List[str]) -> int:
        """Add leads to a campaign."""
        added = 0
        with get_db_cursor() as cursor:
            for lead_id in lead_ids:
                try:
                    cursor.execute("""
                        INSERT INTO campaign_leads (campaign_id, lead_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (campaign_id, lead_id))
                    if cursor.rowcount > 0:
                        added += 1
                except Exception as e:
                    logger.warning(f"Failed to add lead {lead_id} to campaign: {e}")
            
            # Update campaign lead count
            cursor.execute("""
                UPDATE email_campaigns 
                SET total_leads = (SELECT COUNT(*) FROM campaign_leads WHERE campaign_id = %s)
                WHERE id = %s
            """, (campaign_id, campaign_id))
        
        return added


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def init_database():
    """Initialize database connection and verify it works."""
    if test_connection():
        logger.info("Database initialized successfully")
        return True
    else:
        logger.error("Database initialization failed")
        return False


def get_dashboard_stats(user_id: str) -> Dict:
    """Get statistics for user dashboard."""
    lead_counts = LeadDB.count_by_status(user_id)
    run_stats = AgentRunDB.get_summary_stats(user_id)
    
    return {
        'leads': {
            'total': sum(lead_counts.values()),
            'by_status': lead_counts
        },
        'runs': run_stats
    }


# ============================================================================
# TEST SCRIPT
# ============================================================================

if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    # Test connection
    if test_connection():
        print("✅ Connection successful!")
        
        # Get test user
        user = UserDB.get_first_user()
        if user:
            print(f"✅ Found user: {user['full_name']} ({user['email']})")
            print(f"   User ID: {user['id']}")
            
            # Test creating a lead
            print("\n--- Testing Lead Creation ---")
            lead = LeadDB.create(
                user_id=str(user['id']),
                name="Test Lead",
                email="testlead@example.com",
                company="Test Company Inc",
                job_title="CEO",
                source="test"
            )
            if lead:
                print(f"✅ Created lead: {lead['name']}")
                print(f"   Lead ID: {lead['id']}")
                
                # Clean up test lead
                LeadDB.delete(str(lead['id']))
                print("✅ Cleaned up test lead")
        else:
            print("❌ No user found in database")
    else:
        print("❌ Connection failed!")
    
    print("\n" + "=" * 60)
    print("Database test complete!")
    print("=" * 60)