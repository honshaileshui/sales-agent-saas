"""
Email Service for SalesAgent AI
================================
High-level email service that integrates:
- SendGrid sending
- Database updates
- Tracking
- Analytics

This is the main interface for sending emails from the application.

Author: Shailesh
Week 5: Email Infrastructure
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_service.sendgrid_client import SendGridEmailClient, get_email_client
from email_service.tracker import EmailTracker, get_tracker, get_event_store

logger = logging.getLogger(__name__)


class EmailService:
    """
    Main email service for SalesAgent AI.
    
    This service handles:
    - Sending emails via SendGrid
    - Adding tracking pixels and link tracking
    - Updating database status
    - Recording analytics
    
    Usage:
        service = EmailService()
        
        # Send a single email
        result = service.send_email(email_id="...")
        
        # Send campaign emails
        results = service.send_campaign_emails(campaign_id="...")
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize email service.
        
        Args:
            base_url: Base URL for tracking endpoints
        """
        self.sendgrid = get_email_client()
        self.tracker = get_tracker(base_url=base_url)
        self.event_store = get_event_store()
        
        logger.info("Email service initialized")
    
    def send_email_by_id(
        self,
        email_id: str,
        db_session = None
    ) -> Dict:
        """
        Send an email by its database ID.
        
        Args:
            email_id: Email ID from database
            db_session: Database session (optional)
        
        Returns:
            Dict with send result
        """
        # TODO: Fetch email from database
        # For now, return a placeholder
        logger.info(f"Would send email {email_id} from database")
        
        return {
            'success': False,
            'error': 'Database integration pending',
            'email_id': email_id
        }
    
    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
        email_id: str = None,
        lead_id: str = None,
        campaign_id: str = None,
        add_tracking: bool = True,
        add_unsubscribe: bool = True
    ) -> Dict:
        """
        Send a single email with full tracking.
        
        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            body: Email body (plain text)
            email_id: Internal email ID
            lead_id: Lead ID
            campaign_id: Campaign ID
            add_tracking: Add open/click tracking
            add_unsubscribe: Add unsubscribe link
        
        Returns:
            Dict with send result
        """
        try:
            # Convert plain text to HTML
            html_body = self._text_to_html(body)
            
            # Add tracking
            if add_tracking:
                html_body = self.tracker.add_tracking(
                    html_body=html_body,
                    email_id=email_id or "unknown",
                    lead_id=lead_id,
                    campaign_id=campaign_id
                )
            
            # Add unsubscribe link
            if add_unsubscribe and lead_id:
                html_body = self.tracker.add_unsubscribe_link(
                    html_body=html_body,
                    email_id=email_id or "unknown",
                    lead_id=lead_id
                )
            
            # Send via SendGrid
            result = self.sendgrid.send_email(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                body=body,
                html_body=html_body,
                email_id=email_id,
                lead_id=lead_id,
                campaign_id=campaign_id,
                track_opens=True,
                track_clicks=True
            )
            
            if result['success']:
                logger.info(f"Email sent successfully to {to_email}")
                # TODO: Update database status
                # EmailDB.update_status(email_id, 'sent', message_id=result['message_id'])
                # LeadDB.update_status(lead_id, 'email_sent')
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                'success': False,
                'error': str(e),
                'email_id': email_id
            }
    
    def send_bulk(
        self,
        emails: List[Dict],
        campaign_id: str = None,
        add_tracking: bool = True
    ) -> Dict:
        """
        Send multiple emails.
        
        Args:
            emails: List of email dicts with keys:
                - to_email, to_name, subject, body
                - Optional: email_id, lead_id
            campaign_id: Campaign ID to associate with all emails
            add_tracking: Add tracking to emails
        
        Returns:
            Dict with bulk send results
        """
        results = []
        sent = 0
        failed = 0
        
        for email_data in emails:
            result = self.send_email(
                to_email=email_data['to_email'],
                to_name=email_data.get('to_name', ''),
                subject=email_data['subject'],
                body=email_data['body'],
                email_id=email_data.get('email_id'),
                lead_id=email_data.get('lead_id'),
                campaign_id=campaign_id or email_data.get('campaign_id'),
                add_tracking=add_tracking
            )
            
            results.append(result)
            
            if result['success']:
                sent += 1
            else:
                failed += 1
        
        logger.info(f"Bulk send complete: {sent} sent, {failed} failed")
        
        return {
            'sent': sent,
            'failed': failed,
            'total': len(emails),
            'results': results
        }
    
    def send_test_email(self, to_email: str) -> Dict:
        """
        Send a test email to verify configuration.
        
        Args:
            to_email: Email address to send test to
        
        Returns:
            Dict with send result
        """
        return self.send_email(
            to_email=to_email,
            to_name="Test User",
            subject="🚀 SalesAgent AI - Test Email",
            body="""Hi there!

This is a test email from SalesAgent AI.

If you're seeing this, your email configuration is working correctly!

Here's what we can track:
✓ Email delivery
✓ Opens (when you open this email)
✓ Clicks (when you click links)

Test link: https://salesagentai.com

Best regards,
SalesAgent AI

---
This is an automated test email.""",
            email_id="test-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            add_tracking=True,
            add_unsubscribe=False
        )
    
    def _text_to_html(self, text: str) -> str:
        """Convert plain text to HTML email."""
        # Escape HTML
        html = text.replace('&', '&amp;')
        html = html.replace('<', '&lt;')
        html = html.replace('>', '&gt;')
        
        # Convert line breaks
        html = html.replace('\n', '<br>\n')
        
        # Wrap in HTML template
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        a {{
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html}
    </div>
</body>
</html>
"""
    
    def get_tracking_stats(self, email_id: str) -> Dict:
        """Get tracking statistics for an email."""
        return self.event_store.get_email_stats(email_id)
    
    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """Get tracking statistics for a campaign."""
        return self.event_store.get_campaign_stats(campaign_id)


# Global instance
_service = None

def get_email_service(base_url: str = "http://localhost:8000") -> EmailService:
    """Get or create email service instance."""
    global _service
    if _service is None:
        _service = EmailService(base_url=base_url)
    return _service


# ============================================================
# CLI FUNCTIONS
# ============================================================

def send_test(to_email: str):
    """Send a test email from CLI."""
    print(f"📧 Sending test email to {to_email}...")
    
    service = get_email_service()
    result = service.send_test_email(to_email)
    
    if result['success']:
        print(f"✅ Test email sent successfully!")
        print(f"   Message ID: {result['message_id']}")
    else:
        print(f"❌ Failed to send test email: {result['error']}")
    
    return result


def check_config():
    """Check email configuration."""
    print("🔍 Checking email configuration...")
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    
    if not os.path.exists(config_path):
        print("❌ config.json not found")
        return False
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    sendgrid_key = config.get('credentials', {}).get('sendgrid_api_key', '')
    
    if not sendgrid_key:
        print("❌ SendGrid API key not found in config.json")
        return False
    
    if not sendgrid_key.startswith('SG.'):
        print("❌ SendGrid API key appears invalid (should start with 'SG.')")
        return False
    
    print("✅ SendGrid API key found")
    print(f"   Key: {sendgrid_key[:10]}...{sendgrid_key[-5:]}")
    
    try:
        service = get_email_service()
        print("✅ Email service initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize email service: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test' and len(sys.argv) > 2:
            send_test(sys.argv[2])
        elif command == 'check':
            check_config()
        else:
            print("Usage:")
            print("  python service.py check           - Check configuration")
            print("  python service.py test <email>    - Send test email")
    else:
        check_config()
