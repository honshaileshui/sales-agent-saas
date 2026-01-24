"""
Email Tracking Service for SalesAgent AI
=========================================
Handles open tracking, click tracking, and analytics.

Features:
- Generate tracking pixels for open detection
- Rewrite links for click tracking
- Record and query tracking events
- Generate tracking reports

Author: Shailesh
Week 5: Email Infrastructure
"""

import uuid
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlencode, urlparse, parse_qs

logger = logging.getLogger(__name__)


class EmailTracker:
    """
    Email tracking service for opens and clicks.
    
    Usage:
        tracker = EmailTracker(base_url="https://yourdomain.com")
        
        # Add tracking to email
        tracked_html = tracker.add_tracking(
            html_body=original_html,
            email_id="email-123",
            lead_id="lead-456"
        )
        
        # Record events (called by webhook handler)
        tracker.record_open(email_id="email-123")
        tracker.record_click(email_id="email-123", url="https://...")
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize tracker.
        
        Args:
            base_url: Base URL for tracking endpoints
        """
        self.base_url = base_url.rstrip('/')
        self.tracking_endpoint = f"{self.base_url}/api/track"
        
    def generate_tracking_pixel(
        self,
        email_id: str,
        lead_id: str = None,
        campaign_id: str = None
    ) -> str:
        """
        Generate a 1x1 tracking pixel for open detection.
        
        Args:
            email_id: Unique email identifier
            lead_id: Optional lead ID
            campaign_id: Optional campaign ID
        
        Returns:
            HTML img tag with tracking pixel
        """
        params = {
            'type': 'open',
            'eid': email_id,
        }
        
        if lead_id:
            params['lid'] = lead_id
        if campaign_id:
            params['cid'] = campaign_id
        
        # Add timestamp to prevent caching
        params['t'] = str(int(datetime.now().timestamp()))
        
        tracking_url = f"{self.tracking_endpoint}/pixel?{urlencode(params)}"
        
        # Return invisible 1x1 pixel
        return f'<img src="{tracking_url}" width="1" height="1" style="display:none;" alt="" />'
    
    def rewrite_links(
        self,
        html_body: str,
        email_id: str,
        lead_id: str = None,
        campaign_id: str = None
    ) -> str:
        """
        Rewrite all links in HTML for click tracking.
        
        Args:
            html_body: Original HTML body
            email_id: Unique email identifier
            lead_id: Optional lead ID
            campaign_id: Optional campaign ID
        
        Returns:
            HTML with rewritten tracking links
        """
        import re
        
        def replace_link(match):
            original_url = match.group(1)
            
            # Skip tracking for certain URLs
            skip_patterns = [
                'mailto:',
                'tel:',
                'unsubscribe',
                self.tracking_endpoint,  # Don't track our own tracking URLs
            ]
            
            for pattern in skip_patterns:
                if pattern in original_url.lower():
                    return match.group(0)
            
            # Build tracking URL
            params = {
                'type': 'click',
                'eid': email_id,
                'url': original_url,
            }
            
            if lead_id:
                params['lid'] = lead_id
            if campaign_id:
                params['cid'] = campaign_id
            
            tracking_url = f"{self.tracking_endpoint}/click?{urlencode(params)}"
            
            return f'href="{tracking_url}"'
        
        # Replace all href attributes
        pattern = r'href="([^"]+)"'
        tracked_html = re.sub(pattern, replace_link, html_body)
        
        return tracked_html
    
    def add_tracking(
        self,
        html_body: str,
        email_id: str,
        lead_id: str = None,
        campaign_id: str = None,
        track_opens: bool = True,
        track_clicks: bool = True
    ) -> str:
        """
        Add both open and click tracking to an email.
        
        Args:
            html_body: Original HTML body
            email_id: Unique email identifier
            lead_id: Optional lead ID
            campaign_id: Optional campaign ID
            track_opens: Enable open tracking
            track_clicks: Enable click tracking
        
        Returns:
            HTML with all tracking added
        """
        result = html_body
        
        # Add click tracking
        if track_clicks:
            result = self.rewrite_links(
                result,
                email_id=email_id,
                lead_id=lead_id,
                campaign_id=campaign_id
            )
        
        # Add open tracking pixel before </body>
        if track_opens:
            pixel = self.generate_tracking_pixel(
                email_id=email_id,
                lead_id=lead_id,
                campaign_id=campaign_id
            )
            
            if '</body>' in result.lower():
                # Insert before closing body tag
                result = result.replace('</body>', f'{pixel}</body>')
                result = result.replace('</BODY>', f'{pixel}</BODY>')
            else:
                # Append at end
                result = result + pixel
        
        return result
    
    def add_unsubscribe_link(
        self,
        html_body: str,
        email_id: str,
        lead_id: str
    ) -> str:
        """
        Add unsubscribe link to email footer.
        
        Args:
            html_body: Original HTML body
            email_id: Unique email identifier
            lead_id: Lead ID
        
        Returns:
            HTML with unsubscribe link added
        """
        params = {
            'eid': email_id,
            'lid': lead_id,
        }
        
        unsubscribe_url = f"{self.base_url}/api/unsubscribe?{urlencode(params)}"
        
        unsubscribe_html = f'''
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; text-align: center;">
            <p>
                Don't want to receive these emails? 
                <a href="{unsubscribe_url}" style="color: #666;">Unsubscribe</a>
            </p>
        </div>
        '''
        
        if '</body>' in html_body.lower():
            result = html_body.replace('</body>', f'{unsubscribe_html}</body>')
            result = result.replace('</BODY>', f'{unsubscribe_html}</BODY>')
        else:
            result = html_body + unsubscribe_html
        
        return result


class TrackingEventStore:
    """
    In-memory store for tracking events.
    In production, this would be backed by a database.
    """
    
    def __init__(self):
        self.events = []
        self.opens = {}  # email_id -> [timestamps]
        self.clicks = {}  # email_id -> [{url, timestamp}]
    
    def record_open(
        self,
        email_id: str,
        lead_id: str = None,
        campaign_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Record an email open event."""
        event = {
            'type': 'open',
            'email_id': email_id,
            'lead_id': lead_id,
            'campaign_id': campaign_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.now().isoformat()
        }
        
        self.events.append(event)
        
        if email_id not in self.opens:
            self.opens[email_id] = []
        self.opens[email_id].append(event['timestamp'])
        
        logger.info(f"Open recorded for email {email_id}")
        
        return event
    
    def record_click(
        self,
        email_id: str,
        url: str,
        lead_id: str = None,
        campaign_id: str = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Record a link click event."""
        event = {
            'type': 'click',
            'email_id': email_id,
            'lead_id': lead_id,
            'campaign_id': campaign_id,
            'url': url,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.now().isoformat()
        }
        
        self.events.append(event)
        
        if email_id not in self.clicks:
            self.clicks[email_id] = []
        self.clicks[email_id].append({
            'url': url,
            'timestamp': event['timestamp']
        })
        
        logger.info(f"Click recorded for email {email_id}: {url}")
        
        return event
    
    def get_email_stats(self, email_id: str) -> Dict:
        """Get tracking stats for a specific email."""
        return {
            'email_id': email_id,
            'opens': len(self.opens.get(email_id, [])),
            'unique_opens': 1 if email_id in self.opens else 0,
            'clicks': len(self.clicks.get(email_id, [])),
            'click_details': self.clicks.get(email_id, []),
            'first_open': self.opens.get(email_id, [None])[0],
            'last_open': self.opens.get(email_id, [None])[-1] if email_id in self.opens else None,
        }
    
    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """Get tracking stats for a campaign."""
        campaign_events = [e for e in self.events if e.get('campaign_id') == campaign_id]
        
        opens = [e for e in campaign_events if e['type'] == 'open']
        clicks = [e for e in campaign_events if e['type'] == 'click']
        
        unique_opens = len(set(e['email_id'] for e in opens))
        unique_clicks = len(set(e['email_id'] for e in clicks))
        
        return {
            'campaign_id': campaign_id,
            'total_opens': len(opens),
            'unique_opens': unique_opens,
            'total_clicks': len(clicks),
            'unique_clicks': unique_clicks,
        }
    
    def get_all_events(
        self,
        event_type: str = None,
        email_id: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get filtered list of events."""
        filtered = self.events
        
        if event_type:
            filtered = [e for e in filtered if e['type'] == event_type]
        
        if email_id:
            filtered = [e for e in filtered if e['email_id'] == email_id]
        
        # Return most recent first
        return sorted(filtered, key=lambda x: x['timestamp'], reverse=True)[:limit]


# Global instances
_tracker = None
_event_store = None

def get_tracker(base_url: str = "http://localhost:8000") -> EmailTracker:
    """Get or create tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = EmailTracker(base_url=base_url)
    return _tracker

def get_event_store() -> TrackingEventStore:
    """Get or create event store instance."""
    global _event_store
    if _event_store is None:
        _event_store = TrackingEventStore()
    return _event_store


if __name__ == "__main__":
    # Test tracking
    tracker = get_tracker()
    
    sample_html = """
    <html>
    <body>
        <p>Hi John,</p>
        <p>Check out our <a href="https://example.com/demo">product demo</a>!</p>
        <p>Best regards</p>
    </body>
    </html>
    """
    
    tracked = tracker.add_tracking(
        html_body=sample_html,
        email_id="test-123",
        lead_id="lead-456",
        campaign_id="campaign-789"
    )
    
    print("Original HTML:")
    print(sample_html)
    print("\nTracked HTML:")
    print(tracked)
