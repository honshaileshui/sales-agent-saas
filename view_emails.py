"""
View Drafted Emails
===================
Displays all generated emails in a readable format.
"""

from database import test_connection, UserDB, LeadDB, EmailDB, get_db_cursor

def view_all_emails():
    """Display all drafted emails."""
    
    if not test_connection():
        print("❌ Database connection failed!")
        return
    
    print("\n" + "=" * 70)
    print("📧 ALL DRAFTED EMAILS")
    print("=" * 70)
    
    # Query to get all emails with lead info
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                l.name,
                l.email as lead_email,
                l.company,
                l.job_title,
                e.subject,
                e.body,
                e.template_used,
                e.tone,
                e.status,
                e.created_at
            FROM leads l
            JOIN generated_emails e ON l.id = e.lead_id
            WHERE e.is_current = TRUE
            ORDER BY e.created_at
        """)
        emails = cursor.fetchall()
    
    if not emails:
        print("\nNo emails found in database.")
        return
    
    print(f"\nFound {len(emails)} drafted emails:\n")
    
    for i, email in enumerate(emails, 1):
        print("=" * 70)
        print(f"📧 EMAIL #{i}")
        print("=" * 70)
        print(f"TO: {email['name']} <{email['lead_email']}>")
        print(f"COMPANY: {email['company']}")
        print(f"TITLE: {email['job_title'] or 'N/A'}")
        print(f"TEMPLATE: {email['template_used']} | TONE: {email['tone']}")
        print(f"STATUS: {email['status']}")
        print("-" * 70)
        print(f"SUBJECT: {email['subject']}")
        print("-" * 70)
        print("BODY:")
        print(email['body'])
        print("\n")
    
    print("=" * 70)
    print(f"Total: {len(emails)} emails ready to send")
    print("=" * 70)


def view_single_email(lead_name: str):
    """View email for a specific lead."""
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                l.name,
                l.email as lead_email,
                l.company,
                e.subject,
                e.body
            FROM leads l
            JOIN generated_emails e ON l.id = e.lead_id
            WHERE l.name ILIKE %s AND e.is_current = TRUE
        """, (f"%{lead_name}%",))
        email = cursor.fetchone()
    
    if not email:
        print(f"No email found for '{lead_name}'")
        return
    
    print("\n" + "=" * 70)
    print(f"📧 EMAIL FOR: {email['name']}")
    print("=" * 70)
    print(f"TO: {email['name']} <{email['lead_email']}>")
    print(f"COMPANY: {email['company']}")
    print("-" * 70)
    print(f"SUBJECT: {email['subject']}")
    print("-" * 70)
    print("BODY:")
    print(email['body'])
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # View specific lead's email
        lead_name = " ".join(sys.argv[1:])
        view_single_email(lead_name)
    else:
        # View all emails
        view_all_emails()