"""
Email Scheduling Worker - DAY 2: SendGrid Integration
=====================================================
Background process that automatically sends scheduled campaign emails.

NEW IN DAY 2:
- Real SendGrid email sending
- Email status tracking
- Error handling & retry
- Rate limiting
"""

import time
import sys
import os
import json
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import psycopg2
from psycopg2.extras import RealDictCursor
import pytz
import logging

# SendGrid imports
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    """Load SendGrid API key from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config
    except Exception as e:
        logger.error(f"[ERROR] Could not load config.json: {e}")
        return {}

CONFIG = load_config()
SENDGRID_API_KEY = "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"
SENDER_EMAIL = "shaileshon13@gmail.com" # Default sender

if not SENDGRID_API_KEY:
    logger.warning("[WARN] SendGrid API key not found in config.json!")

# Database connection
def get_db_connection():
    """Get database connection"""
    db_url = CONFIG.get('database_url', '')
    
    if db_url.startswith('postgresql://'):
        # Parse postgresql://user:pass@host:port/dbname
        parts = db_url.replace('postgresql://', '').split('@')
        user_pass = parts[0].split(':')
        host_port_db = parts[1].split('/')
        host_port = host_port_db[0].split(':')
        
        return psycopg2.connect(
            dbname=host_port_db[1] if len(host_port_db) > 1 else 'salesagent_db',
            user=user_pass[0],
            password=user_pass[1] if len(user_pass) > 1 else '',
            host=host_port[0],
            port=host_port[1] if len(host_port) > 1 else '5432'
        )
    
    # Fallback
    return psycopg2.connect(
        dbname="salesagent_db",
        user="postgres",
        password="Roger12@H",
        host="localhost",
        port="5432"
    )

def check_and_send_campaigns():
    """
    Main function that runs every minute.
    Checks for scheduled campaigns and sends emails.
    """
    logger.info("[CHECK] Checking for campaigns to send...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        campaigns = get_scheduled_campaigns(cursor)
        logger.info(f"[INFO] Found {len(campaigns)} active scheduled campaigns")
        
        for campaign in campaigns:
            process_campaign(campaign, cursor, conn)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"[ERROR] Error in check_and_send_campaigns: {e}", exc_info=True)

def get_scheduled_campaigns(cursor):
    """Get scheduled campaigns from database"""
    cursor.execute("""
        SELECT id, name, scheduled_start_date, scheduled_start_time,
               timezone, daily_send_limit, emails_sent_today, last_send_date,
               status
        FROM email_campaigns
        WHERE status = 'active'
          AND scheduled_start_date IS NOT NULL
          AND scheduled_start_time IS NOT NULL
    """)
    
    return cursor.fetchall()

def process_campaign(campaign, cursor, conn):
    """Process a single campaign"""
    campaign_id = campaign['id']
    campaign_name = campaign['name']
    
    logger.info(f"[EMAIL] Processing campaign: {campaign_name} ({campaign_id})")
    
    # Check if it's time to send
    if not should_send_now(campaign):
        logger.info(f"[TIME] Not time yet for campaign {campaign_name}")
        return
    
    # Check daily limit
    if has_reached_daily_limit(campaign):
        logger.info(f"[LIMIT] Daily limit reached for campaign {campaign_name}")
        return
    
    # Get emails ready to send
    emails_to_send = get_emails_to_send(campaign_id, cursor)
    
    if not emails_to_send:
        logger.info(f"[EMPTY] No emails to send for campaign {campaign_name}")
        return
    
    # Calculate how many we can send today
    remaining = campaign['daily_send_limit'] - campaign['emails_sent_today']
    emails_to_send = emails_to_send[:remaining]
    
    logger.info(f"[SEND] Sending {len(emails_to_send)} emails for campaign {campaign_name}")
    
    # Send emails via SendGrid
    sent_count = send_campaign_emails(emails_to_send, campaign, cursor, conn)
    
    # Update campaign stats
    update_campaign_stats(campaign_id, sent_count, cursor, conn)
    
    logger.info(f"[OK] Sent {sent_count}/{len(emails_to_send)} emails for campaign {campaign_name}")

def should_send_now(campaign):
    """Check if campaign should send now based on schedule and timezone"""
    scheduled_date = campaign['scheduled_start_date']
    scheduled_time = campaign['scheduled_start_time']
    tz_name = campaign.get('timezone', 'UTC')
    
    try:
        # Get current time in campaign's timezone
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        
        # Campaign scheduled time
        scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
        scheduled_datetime = tz.localize(scheduled_datetime)
        
        # Should send if current time >= scheduled time
        return now >= scheduled_datetime
    except Exception as e:
        logger.error(f"[ERROR] Error checking time: {e}")
        return False

def has_reached_daily_limit(campaign):
    """Check if campaign has reached daily send limit"""
    today = date.today()
    last_send = campaign.get('last_send_date')
    
    # Reset counter if it's a new day
    if last_send != today:
        return False
    
    # Check if limit reached
    emails_sent = campaign.get('emails_sent_today', 0)
    daily_limit = campaign.get('daily_send_limit', 50)
    
    return emails_sent >= daily_limit

def get_emails_to_send(campaign_id, cursor):
    """Get emails that are ready to send for this campaign"""
    cursor.execute("""
        SELECT e.id, e.lead_id, e.subject, e.body, 
               l.email as lead_email, l.name as lead_name
        FROM generated_emails e
        JOIN leads l ON e.lead_id = l.id
        JOIN campaign_leads cl ON l.id = cl.lead_id
        WHERE cl.campaign_id = %s
          AND e.status = 'approved'
        ORDER BY e.created_at ASC
        LIMIT 100
    """, (campaign_id,))
    
    return cursor.fetchall()

def send_campaign_emails(emails, campaign, cursor, conn):
    """
    Send emails via SendGrid - REAL IMPLEMENTATION
    
    Returns: Number of successfully sent emails
    """
    if not SENDGRID_API_KEY:
        logger.error("[ERROR] SendGrid API key not configured!")
        return 0
    
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sent_count = 0
    
    for email_data in emails:
        try:
            # Create SendGrid message
            message = Mail(
                from_email=Email(SENDER_EMAIL),
                to_emails=To(email_data['lead_email']),
                subject=email_data['subject'],
                html_content=Content("text/html", email_data['body'])
            )
            
            # Send via SendGrid
            logger.info(f"  [OUT] Sending to: {email_data['lead_name']} <{email_data['lead_email']}>")
            response = sg.send(message)
            
            # Check response
            if response.status_code in [200, 201, 202]:
                logger.info(f"  [OK] Sent successfully (status: {response.status_code})")
                
                # Update email status in database
                update_email_status(
                    email_data['id'],
                    'sent',
                    cursor,
                    conn
                )
                
                sent_count += 1
            else:
                logger.warning(f"  [WARN] Unexpected status: {response.status_code}")
            
            # Rate limiting (don't overwhelm SendGrid)
            time.sleep(0.2)  # 200ms between emails
            
        except Exception as e:
            logger.error(f"  [ERROR] Failed to send to {email_data['lead_email']}: {e}")
            
            # Mark as failed in database
            update_email_status(
                email_data['id'],
                'failed',
                cursor,
                conn,
                error=str(e)
            )
    
    return sent_count

def update_email_status(email_id, status, cursor, conn, error=None):
    """Update email status in database after sending"""
    try:
        if status == 'sent':
            cursor.execute("""
                UPDATE generated_emails
                SET status = %s, sent_at = NOW()
                WHERE id = %s
            """, (status, email_id))
        else:
            cursor.execute("""
                UPDATE generated_emails
                SET status = %s
                WHERE id = %s
            """, (status, email_id))
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to update email status: {e}")

def update_campaign_stats(campaign_id, sent_count, cursor, conn):
    """Update campaign statistics after sending"""
    try:
        cursor.execute("""
            UPDATE email_campaigns
            SET emails_sent_today = emails_sent_today + %s,
                last_send_date = CURRENT_DATE,
                emails_sent = emails_sent + %s,
                updated_at = NOW()
            WHERE id = %s
        """, (sent_count, sent_count, campaign_id))
        conn.commit()
        
        logger.info(f"[INFO] Updated campaign stats: +{sent_count} emails")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to update campaign stats: {e}")

def start_scheduler():
    """Start the background scheduler"""
    logger.info("[START] Starting Email Scheduling Worker (Day 2 - SendGrid)...")
    
    # Test database connection
    try:
        conn = get_db_connection()
        logger.info("[OK] Database connection successful!")
        conn.close()
    except Exception as e:
        logger.error(f"[ERROR] Database connection failed: {e}")
        return
    
    # Test SendGrid API key
    if SENDGRID_API_KEY:
        logger.info("[OK] SendGrid API key found")
    else:
        logger.warning("[WARN] SendGrid API key missing - emails won't send!")
    
    scheduler = BackgroundScheduler()
    
    # Run check_and_send_campaigns every 1 minute
    scheduler.add_job(
        func=check_and_send_campaigns,
        trigger=IntervalTrigger(minutes=1),
        id='campaign_sender',
        name='Check and send scheduled campaigns',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("[OK] Scheduler started! Checking every minute...")
    logger.info("[INFO] Press Ctrl+C to stop")
    
    # Keep the script running
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("[STOP] Shutting down scheduler...")
        scheduler.shutdown()
        logger.info("[OK] Scheduler stopped")

if __name__ == "__main__":
    start_scheduler()