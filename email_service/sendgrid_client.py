"""
SendGrid Email Client for SalesAgent AI
========================================
Handles all email sending operations via SendGrid API.

Features:
- Send single emails
- Send bulk emails
- Track opens and clicks
- Handle attachments
- Manage sender reputation

Author: Shailesh
Week 5: Email Infrastructure
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, Subject,
    TrackingSettings, ClickTracking, OpenTracking,
    Attachment, FileContent, FileName, FileType, Disposition,
    CustomArg, Category
)

# Setup logging
logger = logging.getLogger(__name__)

# Load config
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

CONFIG = load_config()


class SendGridEmailClient:
    """
    SendGrid email client for SalesAgent AI.
    
    Usage:
        client = SendGridEmailClient()
        result = client.send_email(
            to_email="john@example.com",
            to_name="John Doe",
            subject="Quick question",
            body="Hi John..."
        )
    """
    
    def __init__(self, api_key: str = None):
        """Initialize SendGrid client."""
        self.api_key = api_key or CONFIG.get('credentials', {}).get('sendgrid_api_key')
        
        if not self.api_key:
            raise ValueError("SendGrid API key not found. Add it to config.json")
        
        self.client = SendGridAPIClient(api_key=self.api_key)
        
        # Default sender (verified in SendGrid)
        self.default_from_email = "shaileshon13@gmail.com"
        self.default_from_name = "Shailesh"
        
        logger.info("SendGrid client initialized")
    
    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
        from_email: str = None,
        from_name: str = None,
        html_body: str = None,
        reply_to: str = None,
        email_id: str = None,
        lead_id: str = None,
        campaign_id: str = None,
        track_opens: bool = True,
        track_clicks: bool = True,
        categories: List[str] = None
    ) -> Dict:
        """
        Send a single email via SendGrid.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject line
            body: Plain text email body
            from_email: Sender email (defaults to verified sender)
            from_name: Sender name
            html_body: Optional HTML version of email
            reply_to: Reply-to address
            email_id: Internal email ID for tracking
            lead_id: Lead ID for tracking
            campaign_id: Campaign ID for tracking
            track_opens: Enable open tracking
            track_clicks: Enable click tracking
            categories: SendGrid categories for filtering
        
        Returns:
            Dict with 'success', 'message_id', 'status_code', 'error'
        """
        try:
            # Build the email
            message = Mail()
            
            # From
            message.from_email = Email(
                email=from_email or self.default_from_email,
                name=from_name or self.default_from_name
            )
            
            # To
            message.to = To(email=to_email, name=to_name)
            
            # Subject
            message.subject = Subject(subject)
            
            # Body - prefer HTML if provided
            if html_body:
                message.content = [
                    Content("text/plain", body),
                    Content("text/html", html_body)
                ]
            else:
                # Convert plain text to simple HTML
                html_version = self._text_to_html(body)
                message.content = [
                    Content("text/plain", body),
                    Content("text/html", html_version)
                ]
            
            # Reply-to
            if reply_to:
                message.reply_to = Email(reply_to)
            
            # Tracking settings
            tracking = TrackingSettings()
            tracking.click_tracking = ClickTracking(
                enable=track_clicks,
                enable_text=track_clicks
            )
            tracking.open_tracking = OpenTracking(
                enable=track_opens
            )
            message.tracking_settings = tracking
            
            # Custom args for webhook identification
            if email_id:
                message.custom_arg = CustomArg(key="email_id", value=email_id)
            if lead_id:
                message.custom_arg = CustomArg(key="lead_id", value=lead_id)
            if campaign_id:
                message.custom_arg = CustomArg(key="campaign_id", value=campaign_id)
            
            # Categories
            if categories:
                for cat in categories:
                    message.category = Category(cat)
            else:
                message.category = Category("salesagent")
            
            # Send!
            response = self.client.send(message)
            
            # Extract message ID from headers
            message_id = None
            if response.headers:
                message_id = response.headers.get('X-Message-Id')
            
            logger.info(f"Email sent successfully to {to_email} (ID: {message_id})")
            
            return {
                'success': True,
                'message_id': message_id,
                'status_code': response.status_code,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'status_code': None,
                'error': str(e)
            }
    
    def send_bulk_emails(
        self,
        emails: List[Dict],
        track_opens: bool = True,
        track_clicks: bool = True
    ) -> Dict:
        """
        Send multiple emails.
        
        Args:
            emails: List of email dicts with keys:
                - to_email, to_name, subject, body
                - Optional: email_id, lead_id, campaign_id
            track_opens: Enable open tracking
            track_clicks: Enable click tracking
        
        Returns:
            Dict with 'sent', 'failed', 'results'
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
                html_body=email_data.get('html_body'),
                email_id=email_data.get('email_id'),
                lead_id=email_data.get('lead_id'),
                campaign_id=email_data.get('campaign_id'),
                track_opens=track_opens,
                track_clicks=track_clicks
            )
            
            results.append({
                'to_email': email_data['to_email'],
                **result
            })
            
            if result['success']:
                sent += 1
            else:
                failed += 1
        
        logger.info(f"Bulk send complete: {sent} sent, {failed} failed")
        
        return {
            'sent': sent,
            'failed': failed,
            'results': results
        }
    
    def _text_to_html(self, text: str) -> str:
        """Convert plain text to simple HTML."""
        # Escape HTML characters
        html = text.replace('&', '&amp;')
        html = html.replace('<', '&lt;')
        html = html.replace('>', '&gt;')
        
        # Convert line breaks to <br>
        html = html.replace('\n', '<br>\n')
        
        # Wrap in basic HTML structure
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        {html}
    </div>
</body>
</html>
"""
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation."""
        if not email or '@' not in email or '.' not in email:
            return False
        return True
    
    def get_stats(self) -> Dict:
        """Get SendGrid account statistics."""
        try:
            response = self.client.client.stats.get(
                query_params={'start_date': '2024-01-01'}
            )
            return json.loads(response.body)
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Singleton instance
_client = None

def get_email_client() -> SendGridEmailClient:
    """Get or create SendGrid client instance."""
    global _client
    if _client is None:
        _client = SendGridEmailClient()
    return _client


# Quick test function
def test_connection():
    """Test SendGrid connection."""
    try:
        client = get_email_client()
        print("✅ SendGrid client initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ SendGrid connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
