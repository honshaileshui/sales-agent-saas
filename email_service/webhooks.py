"""
SendGrid Webhook Handler for SalesAgent AI
===========================================
Processes incoming webhooks from SendGrid for:
- Email deliveries
- Opens
- Clicks
- Bounces
- Spam reports
- Unsubscribes

Author: Shailesh
Week 5: Email Infrastructure
"""

import json
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class EmailEvent(Enum):
    """SendGrid event types."""
    PROCESSED = "processed"
    DROPPED = "dropped"
    DELIVERED = "delivered"
    DEFERRED = "deferred"
    BOUNCE = "bounce"
    OPEN = "open"
    CLICK = "click"
    SPAM_REPORT = "spamreport"
    UNSUBSCRIBE = "unsubscribe"
    GROUP_UNSUBSCRIBE = "group_unsubscribe"
    GROUP_RESUBSCRIBE = "group_resubscribe"


class WebhookHandler:
    """
    Handler for SendGrid webhook events.
    
    Usage:
        handler = WebhookHandler(db_session=db)
        
        # In your FastAPI route:
        @app.post("/webhooks/sendgrid")
        async def handle_webhook(request: Request):
            body = await request.body()
            events = json.loads(body)
            results = handler.process_events(events)
            return {"processed": len(results)}
    """
    
    def __init__(self, webhook_key: str = None):
        """
        Initialize webhook handler.
        
        Args:
            webhook_key: SendGrid webhook verification key (optional)
        """
        self.webhook_key = webhook_key
        self.event_handlers = {
            EmailEvent.DELIVERED: self._handle_delivered,
            EmailEvent.OPEN: self._handle_open,
            EmailEvent.CLICK: self._handle_click,
            EmailEvent.BOUNCE: self._handle_bounce,
            EmailEvent.SPAM_REPORT: self._handle_spam_report,
            EmailEvent.UNSUBSCRIBE: self._handle_unsubscribe,
            EmailEvent.DROPPED: self._handle_dropped,
            EmailEvent.DEFERRED: self._handle_deferred,
        }
        
        # In-memory event log (replace with database in production)
        self.processed_events = []
    
    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: str
    ) -> bool:
        """
        Verify SendGrid webhook signature.
        
        Args:
            payload: Raw request body
            signature: X-Twilio-Email-Event-Webhook-Signature header
            timestamp: X-Twilio-Email-Event-Webhook-Timestamp header
        
        Returns:
            True if signature is valid
        """
        if not self.webhook_key:
            logger.warning("Webhook key not configured, skipping verification")
            return True
        
        try:
            timestamped_payload = timestamp + payload.decode('utf-8')
            expected_signature = hmac.new(
                self.webhook_key.encode('utf-8'),
                timestamped_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def process_events(self, events: List[Dict]) -> List[Dict]:
        """
        Process a batch of SendGrid events.
        
        Args:
            events: List of event dictionaries from SendGrid
        
        Returns:
            List of processing results
        """
        results = []
        
        for event in events:
            try:
                result = self.process_single_event(event)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'event': event
                })
        
        logger.info(f"Processed {len(results)} webhook events")
        return results
    
    def process_single_event(self, event: Dict) -> Dict:
        """
        Process a single SendGrid event.
        
        Args:
            event: Event dictionary from SendGrid
        
        Returns:
            Processing result
        """
        event_type = event.get('event', '').lower()
        
        try:
            event_enum = EmailEvent(event_type)
        except ValueError:
            logger.warning(f"Unknown event type: {event_type}")
            return {
                'success': False,
                'error': f'Unknown event type: {event_type}',
                'event_type': event_type
            }
        
        handler = self.event_handlers.get(event_enum)
        
        if handler:
            result = handler(event)
            self.processed_events.append({
                'type': event_type,
                'data': event,
                'result': result,
                'processed_at': datetime.now().isoformat()
            })
            return result
        else:
            logger.debug(f"No handler for event type: {event_type}")
            return {
                'success': True,
                'event_type': event_type,
                'action': 'ignored'
            }
    
    def _extract_common_fields(self, event: Dict) -> Dict:
        """Extract common fields from event."""
        return {
            'email': event.get('email'),
            'timestamp': event.get('timestamp'),
            'sg_message_id': event.get('sg_message_id'),
            'sg_event_id': event.get('sg_event_id'),
            # Custom args we added when sending
            'email_id': event.get('email_id'),
            'lead_id': event.get('lead_id'),
            'campaign_id': event.get('campaign_id'),
        }
    
    def _handle_delivered(self, event: Dict) -> Dict:
        """Handle email delivered event."""
        fields = self._extract_common_fields(event)
        
        logger.info(f"Email delivered to {fields['email']}")
        
        # TODO: Update email status in database
        # EmailDB.update_status(fields['email_id'], 'delivered')
        
        return {
            'success': True,
            'event_type': 'delivered',
            'email': fields['email'],
            'email_id': fields['email_id'],
            'action': 'status_updated'
        }
    
    def _handle_open(self, event: Dict) -> Dict:
        """Handle email open event."""
        fields = self._extract_common_fields(event)
        
        # Additional open-specific fields
        user_agent = event.get('useragent', '')
        ip = event.get('ip', '')
        
        logger.info(f"Email opened by {fields['email']}")
        
        # TODO: Update email status and record open
        # EmailDB.record_open(fields['email_id'], ip=ip, user_agent=user_agent)
        # LeadDB.update_status(fields['lead_id'], 'engaged')
        
        return {
            'success': True,
            'event_type': 'open',
            'email': fields['email'],
            'email_id': fields['email_id'],
            'user_agent': user_agent,
            'ip': ip,
            'action': 'open_recorded'
        }
    
    def _handle_click(self, event: Dict) -> Dict:
        """Handle link click event."""
        fields = self._extract_common_fields(event)
        
        # Click-specific fields
        url = event.get('url', '')
        user_agent = event.get('useragent', '')
        ip = event.get('ip', '')
        
        logger.info(f"Link clicked by {fields['email']}: {url}")
        
        # TODO: Record click in database
        # EmailDB.record_click(fields['email_id'], url=url)
        # LeadDB.update_engagement_score(fields['lead_id'], 'click')
        
        return {
            'success': True,
            'event_type': 'click',
            'email': fields['email'],
            'email_id': fields['email_id'],
            'url': url,
            'action': 'click_recorded'
        }
    
    def _handle_bounce(self, event: Dict) -> Dict:
        """Handle email bounce event."""
        fields = self._extract_common_fields(event)
        
        # Bounce-specific fields
        bounce_type = event.get('type', '')  # 'bounce' or 'blocked'
        reason = event.get('reason', '')
        status = event.get('status', '')
        
        logger.warning(f"Email bounced for {fields['email']}: {reason}")
        
        # TODO: Mark email as bounced, potentially blacklist address
        # EmailDB.update_status(fields['email_id'], 'bounced', reason=reason)
        # LeadDB.mark_invalid_email(fields['lead_id'], reason=reason)
        
        return {
            'success': True,
            'event_type': 'bounce',
            'email': fields['email'],
            'email_id': fields['email_id'],
            'bounce_type': bounce_type,
            'reason': reason,
            'action': 'bounce_recorded'
        }
    
    def _handle_spam_report(self, event: Dict) -> Dict:
        """Handle spam report event."""
        fields = self._extract_common_fields(event)
        
        logger.warning(f"Spam report from {fields['email']}")
        
        # TODO: Add to suppression list, this is serious!
        # LeadDB.add_to_suppression_list(fields['lead_id'], reason='spam_report')
        # SuppressionList.add(fields['email'], reason='spam_report')
        
        return {
            'success': True,
            'event_type': 'spam_report',
            'email': fields['email'],
            'email_id': fields['email_id'],
            'action': 'added_to_suppression_list'
        }
    
    def _handle_unsubscribe(self, event: Dict) -> Dict:
        """Handle unsubscribe event."""
        fields = self._extract_common_fields(event)
        
        logger.info(f"Unsubscribe from {fields['email']}")
        
        # TODO: Mark lead as unsubscribed
        # LeadDB.update_status(fields['lead_id'], 'unsubscribed')
        # SuppressionList.add(fields['email'], reason='unsubscribed')
        
        return {
            'success': True,
            'event_type': 'unsubscribe',
            'email': fields['email'],
            'email_id': fields['email_id'],
            'action': 'unsubscribed'
        }
    
    def _handle_dropped(self, event: Dict) -> Dict:
        """Handle dropped event (email not sent)."""
        fields = self._extract_common_fields(event)
        reason = event.get('reason', '')
        
        logger.warning(f"Email dropped for {fields['email']}: {reason}")
        
        return {
            'success': True,
            'event_type': 'dropped',
            'email': fields['email'],
            'email_id': fields['email_id'],
            'reason': reason,
            'action': 'drop_recorded'
        }
    
    def _handle_deferred(self, event: Dict) -> Dict:
        """Handle deferred event (temporary failure)."""
        fields = self._extract_common_fields(event)
        
        logger.info(f"Email deferred for {fields['email']}")
        
        return {
            'success': True,
            'event_type': 'deferred',
            'email': fields['email'],
            'email_id': fields['email_id'],
            'action': 'deferred_recorded'
        }
    
    def get_event_summary(self) -> Dict:
        """Get summary of processed events."""
        summary = {
            'total': len(self.processed_events),
            'by_type': {}
        }
        
        for event in self.processed_events:
            event_type = event['type']
            if event_type not in summary['by_type']:
                summary['by_type'][event_type] = 0
            summary['by_type'][event_type] += 1
        
        return summary
    
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Get most recent processed events."""
        return sorted(
            self.processed_events,
            key=lambda x: x['processed_at'],
            reverse=True
        )[:limit]


# Global instance
_handler = None

def get_webhook_handler(webhook_key: str = None) -> WebhookHandler:
    """Get or create webhook handler instance."""
    global _handler
    if _handler is None:
        _handler = WebhookHandler(webhook_key=webhook_key)
    return _handler


if __name__ == "__main__":
    # Test webhook handler
    handler = get_webhook_handler()
    
    # Simulate some events
    test_events = [
        {
            'event': 'delivered',
            'email': 'test@example.com',
            'timestamp': 1234567890,
            'sg_message_id': 'msg-123',
            'email_id': 'email-001',
            'lead_id': 'lead-001',
        },
        {
            'event': 'open',
            'email': 'test@example.com',
            'timestamp': 1234567900,
            'sg_message_id': 'msg-123',
            'email_id': 'email-001',
            'useragent': 'Mozilla/5.0',
            'ip': '192.168.1.1',
        },
        {
            'event': 'click',
            'email': 'test@example.com',
            'timestamp': 1234567910,
            'sg_message_id': 'msg-123',
            'email_id': 'email-001',
            'url': 'https://example.com/demo',
        },
    ]
    
    results = handler.process_events(test_events)
    
    print("Processed events:")
    for result in results:
        print(f"  - {result['event_type']}: {result['action']}")
    
    print("\nSummary:")
    print(handler.get_event_summary())
