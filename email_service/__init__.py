"""
SalesAgent AI - Email Service
==============================
Complete email infrastructure including:
- SendGrid integration
- Open/click tracking
- Webhook handling
- Analytics

Usage:
    from email_service import get_email_service
    
    service = get_email_service()
    service.send_email(
        to_email="john@example.com",
        to_name="John Doe",
        subject="Hello!",
        body="Your email body here..."
    )
"""

from email_service.sendgrid_client import (
    SendGridEmailClient,
    get_email_client,
    test_connection
)

from email_service.tracker import (
    EmailTracker,
    TrackingEventStore,
    get_tracker,
    get_event_store
)

from email_service.webhooks import (
    WebhookHandler,
    EmailEvent,
    get_webhook_handler
)

from email_service.service import (
    EmailService,
    get_email_service,
    send_test,
    check_config
)

__all__ = [
    # Main service
    'EmailService',
    'get_email_service',
    
    # SendGrid client
    'SendGridEmailClient',
    'get_email_client',
    'test_connection',
    
    # Tracking
    'EmailTracker',
    'TrackingEventStore',
    'get_tracker',
    'get_event_store',
    
    # Webhooks
    'WebhookHandler',
    'EmailEvent',
    'get_webhook_handler',
    
    # Utilities
    'send_test',
    'check_config',
]

__version__ = '1.0.0'
