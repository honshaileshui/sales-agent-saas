"""
Add Sample Leads to Database
Run this once to populate your database with test leads.
"""

from database import test_connection, UserDB, LeadDB

def add_sample_leads():
    print("=" * 50)
    print("Adding Sample Leads to Database")
    print("=" * 50)
    
    # Check connection
    if not test_connection():
        print("❌ Database connection failed!")
        return
    
    # Get user
    user = UserDB.get_first_user()
    if not user:
        print("❌ No user found in database!")
        return
    
    user_id = str(user['id'])
    print(f"✅ Using user: {user['full_name']}")
    
    # Sample leads to add
    sample_leads = [
        {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@techstartup.io",
            "company": "TechStartup Inc",
            "job_title": "VP of Sales"
        },
        {
            "name": "Michael Chen",
            "email": "m.chen@innovatecorp.com",
            "company": "InnovateCorp",
            "job_title": "Director of Business Development"
        },
        {
            "name": "Emily Rodriguez",
            "email": "emily.r@cloudsoft.com",
            "company": "CloudSoft Solutions",
            "job_title": "Head of Partnerships"
        },
        {
            "name": "David Kim",
            "email": "david.kim@datadriven.ai",
            "company": "DataDriven AI",
            "job_title": "Chief Revenue Officer"
        },
        {
            "name": "Jessica Williams",
            "email": "jwilliams@growthventures.com",
            "company": "Growth Ventures",
            "job_title": "Sales Manager"
        }
    ]
    
    print(f"\nAdding {len(sample_leads)} sample leads...")
    
    added = 0
    for lead in sample_leads:
        try:
            result = LeadDB.create(
                user_id=user_id,
                name=lead['name'],
                email=lead['email'],
                company=lead['company'],
                job_title=lead['job_title'],
                source='sample_data'
            )
            if result:
                print(f"  ✅ Added: {lead['name']} ({lead['company']})")
                added += 1
            else:
                print(f"  ⚠️ Skipped (may already exist): {lead['name']}")
        except Exception as e:
            print(f"  ❌ Failed: {lead['name']} - {e}")
    
    print(f"\n{'=' * 50}")
    print(f"✅ Successfully added {added} leads!")
    print(f"{'=' * 50}")
    
    # Show current lead count
    leads = LeadDB.get_all_for_user(user_id)
    print(f"\n📊 Total leads in database: {len(leads)}")
    
    print("\n🚀 Now you can run: python sales_agent.py")
    print("   This will process all new leads!")

if __name__ == "__main__":
    add_sample_leads()