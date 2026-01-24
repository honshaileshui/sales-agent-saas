#!/usr/bin/env python3
"""
🚀 SalesAgent CLI - Command Line Interface for SalesAgent AI

Usage:
    salesagent <command> [options]

Commands:
    leads       Manage leads (list, add, import, delete)
    campaigns   Manage campaigns (list, create, start, pause)
    emails      Manage emails (list, generate, send, approve)
    stats       View dashboard statistics
    config      Configure CLI settings
    
Examples:
    salesagent leads list
    salesagent leads import contacts.csv
    salesagent campaigns create "Q1 Outreach"
    salesagent emails generate --lead 5
    salesagent stats
"""

import argparse
import sys
import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Add color support
try:
    from colorama import init, Fore, Style
    init()
    COLORS_ENABLED = True
except ImportError:
    COLORS_ENABLED = False
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = WHITE = RESET = ''
    class Style:
        BRIGHT = DIM = RESET_ALL = ''

# Configuration
CONFIG_DIR = Path.home() / '.salesagent'
CONFIG_FILE = CONFIG_DIR / 'config.json'
DEFAULT_API_URL = 'http://localhost:8000'

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def load_config():
    """Load CLI configuration from file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {'api_url': DEFAULT_API_URL, 'token': None}

def save_config(config):
    """Save CLI configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_headers():
    """Get authorization headers."""
    config = load_config()
    headers = {'Content-Type': 'application/json'}
    if config.get('token'):
        headers['Authorization'] = f"Bearer {config['token']}"
    return headers

def api_request(method, endpoint, data=None, files=None):
    """Make API request with error handling."""
    config = load_config()
    url = f"{config['api_url']}{endpoint}"
    headers = get_headers()
    
    try:
        if files:
            # Remove Content-Type for file uploads
            del headers['Content-Type']
            response = requests.request(method, url, headers=headers, files=files)
        else:
            response = requests.request(method, url, headers=headers, json=data)
        
        if response.status_code == 401:
            print_error("Authentication required. Run: salesagent config login")
            sys.exit(1)
        
        return response
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to API at {config['api_url']}")
        print_info("Make sure the backend is running: uvicorn api.main:app --reload --port 8000")
        sys.exit(1)

def print_success(message):
    """Print success message in green."""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message):
    """Print error message in red."""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def print_info(message):
    """Print info message in cyan."""
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")

def print_warning(message):
    """Print warning message in yellow."""
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")

def print_header(title):
    """Print section header."""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'═' * 50}")
    print(f"  {title}")
    print(f"{'═' * 50}{Style.RESET_ALL}\n")

def print_table(headers, rows):
    """Print formatted table."""
    if not rows:
        print_info("No data to display")
        return
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    
    # Print header
    header_row = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(f"{Fore.CYAN}{Style.BRIGHT}{header_row}{Style.RESET_ALL}")
    print("-" * len(header_row))
    
    # Print rows
    for row in rows:
        print(" | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))

def format_date(date_string):
    """Format ISO date string to readable format."""
    if not date_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_string[:10] if date_string else "N/A"

def format_status(status):
    """Format status with color."""
    colors = {
        'new': Fore.BLUE,
        'researched': Fore.YELLOW,
        'email_drafted': Fore.CYAN,
        'email_sent': Fore.MAGENTA,
        'replied': Fore.GREEN,
        'converted': Fore.GREEN + Style.BRIGHT,
        'draft': Fore.WHITE,
        'active': Fore.GREEN,
        'paused': Fore.YELLOW,
        'completed': Fore.CYAN,
        'approved': Fore.GREEN,
        'sent': Fore.MAGENTA,
        'opened': Fore.YELLOW,
        'bounced': Fore.RED,
    }
    color = colors.get(status, Fore.WHITE)
    return f"{color}{status}{Style.RESET_ALL}"

# ============================================================
# LEADS COMMANDS
# ============================================================

def leads_list(args):
    """List all leads."""
    print_header("📋 LEADS")
    
    params = []
    if args.status:
        params.append(f"status={args.status}")
    if args.limit:
        params.append(f"per_page={args.limit}")
    
    query = f"?{'&'.join(params)}" if params else ""
    response = api_request('GET', f'/api/leads{query}')
    
    if response.status_code == 200:
        data = response.json()
        leads = data.get('leads', data) if isinstance(data, dict) else data
        
        if not leads:
            print_info("No leads found. Import some leads first!")
            print(f"\n  {Fore.CYAN}salesagent leads import your_file.csv{Style.RESET_ALL}")
            return
        
        rows = []
        for lead in leads:
            rows.append([
                lead.get('id', ''),
                lead.get('name', '')[:25],
                lead.get('email', '')[:30],
                lead.get('company', '')[:20],
                format_status(lead.get('status', '')),
                lead.get('priority', ''),
            ])
        
        print_table(['ID', 'Name', 'Email', 'Company', 'Status', 'Priority'], rows)
        print(f"\n{Style.DIM}Total: {len(leads)} leads{Style.RESET_ALL}")
    else:
        print_error(f"Failed to fetch leads: {response.text}")

def leads_add(args):
    """Add a new lead."""
    print_header("➕ ADD LEAD")
    
    data = {
        'name': args.name,
        'email': args.email,
        'company': args.company,
    }
    if args.title:
        data['job_title'] = args.title
    if args.priority:
        data['priority'] = args.priority
    if args.linkedin:
        data['linkedin_url'] = args.linkedin
    
    response = api_request('POST', '/api/leads', data)
    
    if response.status_code in [200, 201]:
        lead = response.json()
        print_success(f"Lead created successfully!")
        print(f"  ID: {lead.get('id')}")
        print(f"  Name: {lead.get('name')}")
        print(f"  Email: {lead.get('email')}")
        print(f"  Company: {lead.get('company')}")
    else:
        print_error(f"Failed to create lead: {response.text}")

def leads_import(args):
    """Import leads from CSV file."""
    print_header("📥 IMPORT LEADS")
    
    file_path = Path(args.file)
    if not file_path.exists():
        print_error(f"File not found: {args.file}")
        return
    
    if not file_path.suffix.lower() == '.csv':
        print_error("Only CSV files are supported")
        return
    
    print_info(f"Importing from: {file_path.name}")
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'text/csv')}
        response = api_request('POST', '/api/leads/import/csv', files=files)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print_success(f"Import completed!")
        print(f"  ✓ Imported: {result.get('imported', 0)}")
        if result.get('skipped', 0) > 0:
            print(f"  ⚠ Skipped: {result.get('skipped', 0)} (duplicates)")
        if result.get('failed', 0) > 0:
            print(f"  ✗ Failed: {result.get('failed', 0)}")
    else:
        print_error(f"Import failed: {response.text}")

def leads_delete(args):
    """Delete a lead."""
    if not args.force:
        confirm = input(f"Delete lead {args.id}? (y/N): ")
        if confirm.lower() != 'y':
            print_info("Cancelled")
            return
    
    response = api_request('DELETE', f'/api/leads/{args.id}')
    
    if response.status_code in [200, 204]:
        print_success(f"Lead {args.id} deleted")
    else:
        print_error(f"Failed to delete lead: {response.text}")

def leads_view(args):
    """View lead details."""
    response = api_request('GET', f'/api/leads/{args.id}')
    
    if response.status_code == 200:
        lead = response.json()
        print_header(f"👤 LEAD: {lead.get('name')}")
        
        print(f"  {Fore.CYAN}ID:{Style.RESET_ALL}         {lead.get('id')}")
        print(f"  {Fore.CYAN}Email:{Style.RESET_ALL}      {lead.get('email')}")
        print(f"  {Fore.CYAN}Company:{Style.RESET_ALL}    {lead.get('company')}")
        print(f"  {Fore.CYAN}Title:{Style.RESET_ALL}      {lead.get('job_title', 'N/A')}")
        print(f"  {Fore.CYAN}Status:{Style.RESET_ALL}     {format_status(lead.get('status', ''))}")
        print(f"  {Fore.CYAN}Priority:{Style.RESET_ALL}   {lead.get('priority', 'N/A')}")
        print(f"  {Fore.CYAN}LinkedIn:{Style.RESET_ALL}   {lead.get('linkedin_url', 'N/A')}")
        print(f"  {Fore.CYAN}Created:{Style.RESET_ALL}    {format_date(lead.get('created_at'))}")
    else:
        print_error(f"Lead not found: {response.text}")

# ============================================================
# CAMPAIGNS COMMANDS
# ============================================================

def campaigns_list(args):
    """List all campaigns."""
    print_header("📢 CAMPAIGNS")
    
    params = []
    if args.status:
        params.append(f"status={args.status}")
    
    query = f"?{'&'.join(params)}" if params else ""
    response = api_request('GET', f'/api/campaigns{query}')
    
    if response.status_code == 200:
        data = response.json()
        campaigns = data.get('campaigns', data) if isinstance(data, dict) else data
        
        if not campaigns:
            print_info("No campaigns found. Create one!")
            print(f"\n  {Fore.CYAN}salesagent campaigns create \"My Campaign\"{Style.RESET_ALL}")
            return
        
        rows = []
        for c in campaigns:
            rows.append([
                c.get('id', ''),
                c.get('name', '')[:30],
                format_status(c.get('status', '')),
                c.get('lead_count', 0),
                c.get('email_count', 0),
                format_date(c.get('created_at')),
            ])
        
        print_table(['ID', 'Name', 'Status', 'Leads', 'Emails', 'Created'], rows)
        print(f"\n{Style.DIM}Total: {len(campaigns)} campaigns{Style.RESET_ALL}")
    else:
        print_error(f"Failed to fetch campaigns: {response.text}")

def campaigns_create(args):
    """Create a new campaign."""
    print_header("➕ CREATE CAMPAIGN")
    
    data = {
        'name': args.name,
        'description': args.description or '',
        'template': args.template or 'default',
        'settings': {
            'daily_limit': args.daily_limit or 50,
            'send_time': args.send_time or '09:00',
        }
    }
    
    response = api_request('POST', '/api/campaigns', data)
    
    if response.status_code in [200, 201]:
        campaign = response.json()
        print_success(f"Campaign created!")
        print(f"  ID: {campaign.get('id')}")
        print(f"  Name: {campaign.get('name')}")
        print(f"  Status: {campaign.get('status')}")
        print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
        print(f"  1. Add leads: salesagent campaigns add-leads {campaign.get('id')} --lead-ids 1,2,3")
        print(f"  2. Start: salesagent campaigns start {campaign.get('id')}")
    else:
        print_error(f"Failed to create campaign: {response.text}")

def campaigns_start(args):
    """Start a campaign."""
    response = api_request('POST', f'/api/campaigns/{args.id}/start')
    
    if response.status_code == 200:
        print_success(f"Campaign {args.id} started! 🚀")
    else:
        print_error(f"Failed to start campaign: {response.text}")

def campaigns_pause(args):
    """Pause a campaign."""
    response = api_request('POST', f'/api/campaigns/{args.id}/pause')
    
    if response.status_code == 200:
        print_success(f"Campaign {args.id} paused ⏸️")
    else:
        print_error(f"Failed to pause campaign: {response.text}")

def campaigns_delete(args):
    """Delete a campaign."""
    if not args.force:
        confirm = input(f"Delete campaign {args.id}? (y/N): ")
        if confirm.lower() != 'y':
            print_info("Cancelled")
            return
    
    response = api_request('DELETE', f'/api/campaigns/{args.id}')
    
    if response.status_code in [200, 204]:
        print_success(f"Campaign {args.id} deleted")
    else:
        print_error(f"Failed to delete campaign: {response.text}")

# ============================================================
# EMAILS COMMANDS
# ============================================================

def emails_list(args):
    """List all emails."""
    print_header("📧 EMAILS")
    
    params = []
    if args.status:
        params.append(f"status={args.status}")
    if args.limit:
        params.append(f"per_page={args.limit}")
    
    query = f"?{'&'.join(params)}" if params else ""
    response = api_request('GET', f'/api/emails{query}')
    
    if response.status_code == 200:
        data = response.json()
        emails = data.get('emails', data) if isinstance(data, dict) else data
        
        if not emails:
            print_info("No emails found. Generate some!")
            print(f"\n  {Fore.CYAN}salesagent emails generate --lead 1{Style.RESET_ALL}")
            return
        
        rows = []
        for e in emails:
            rows.append([
                e.get('id', ''),
                e.get('lead_name', e.get('to_email', ''))[:20],
                e.get('subject', '')[:35],
                format_status(e.get('status', '')),
                format_date(e.get('created_at')),
            ])
        
        print_table(['ID', 'To', 'Subject', 'Status', 'Created'], rows)
        print(f"\n{Style.DIM}Total: {len(emails)} emails{Style.RESET_ALL}")
    else:
        print_error(f"Failed to fetch emails: {response.text}")

def emails_generate(args):
    """Generate email for a lead."""
    print_header("✨ GENERATE EMAIL")
    
    print_info(f"Generating email for lead {args.lead}...")
    
    data = {
        'lead_id': args.lead,
        'template': args.template or 'default',
    }
    if args.campaign:
        data['campaign_id'] = args.campaign
    
    response = api_request('POST', '/api/emails/generate', data)
    
    if response.status_code in [200, 201]:
        email = response.json()
        print_success("Email generated!")
        print(f"\n{Fore.CYAN}To:{Style.RESET_ALL} {email.get('to_email')}")
        print(f"{Fore.CYAN}Subject:{Style.RESET_ALL} {email.get('subject')}")
        print(f"\n{Fore.CYAN}Body:{Style.RESET_ALL}")
        print("-" * 40)
        print(email.get('body', ''))
        print("-" * 40)
        print(f"\n{Fore.CYAN}Next:{Style.RESET_ALL} salesagent emails approve {email.get('id')}")
    else:
        print_error(f"Failed to generate email: {response.text}")

def emails_view(args):
    """View email details."""
    response = api_request('GET', f'/api/emails/{args.id}')
    
    if response.status_code == 200:
        email = response.json()
        print_header(f"📧 EMAIL #{email.get('id')}")
        
        print(f"{Fore.CYAN}To:{Style.RESET_ALL} {email.get('to_email')}")
        print(f"{Fore.CYAN}Subject:{Style.RESET_ALL} {email.get('subject')}")
        print(f"{Fore.CYAN}Status:{Style.RESET_ALL} {format_status(email.get('status', ''))}")
        print(f"\n{Fore.CYAN}Body:{Style.RESET_ALL}")
        print("─" * 50)
        print(email.get('body', ''))
        print("─" * 50)
    else:
        print_error(f"Email not found: {response.text}")

def emails_approve(args):
    """Approve email for sending."""
    response = api_request('POST', f'/api/emails/{args.id}/approve')
    
    if response.status_code == 200:
        print_success(f"Email {args.id} approved! ✓")
        print(f"\n{Fore.CYAN}Next:{Style.RESET_ALL} salesagent emails send {args.id}")
    else:
        print_error(f"Failed to approve email: {response.text}")

def emails_send(args):
    """Send an email."""
    if not args.force:
        confirm = input(f"Send email {args.id}? (y/N): ")
        if confirm.lower() != 'y':
            print_info("Cancelled")
            return
    
    response = api_request('POST', f'/api/emails/{args.id}/send')
    
    if response.status_code == 200:
        print_success(f"Email {args.id} sent! 📤")
    else:
        print_error(f"Failed to send email: {response.text}")

# ============================================================
# STATS COMMAND
# ============================================================

def show_stats(args):
    """Show dashboard statistics."""
    print_header("📊 SALESAGENT DASHBOARD")
    
    # Get leads stats
    leads_response = api_request('GET', '/api/leads/stats/summary')
    campaigns_response = api_request('GET', '/api/campaigns')
    emails_response = api_request('GET', '/api/emails')
    
    print(f"{Fore.CYAN}{Style.BRIGHT}LEADS{Style.RESET_ALL}")
    if leads_response.status_code == 200:
        stats = leads_response.json()
        print(f"  Total:         {stats.get('total', 0)}")
        by_status = stats.get('by_status', {})
        for status, count in by_status.items():
            print(f"  {status.replace('_', ' ').title():13} {count}")
    else:
        print(f"  {Fore.RED}Unable to fetch{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}CAMPAIGNS{Style.RESET_ALL}")
    if campaigns_response.status_code == 200:
        data = campaigns_response.json()
        campaigns = data.get('campaigns', data) if isinstance(data, dict) else data
        total = len(campaigns) if isinstance(campaigns, list) else 0
        active = len([c for c in campaigns if c.get('status') == 'active']) if isinstance(campaigns, list) else 0
        print(f"  Total:         {total}")
        print(f"  Active:        {active}")
    else:
        print(f"  {Fore.RED}Unable to fetch{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}EMAILS{Style.RESET_ALL}")
    if emails_response.status_code == 200:
        data = emails_response.json()
        emails = data.get('emails', data) if isinstance(data, dict) else data
        if isinstance(emails, list):
            total = len(emails)
            drafts = len([e for e in emails if e.get('status') == 'draft'])
            sent = len([e for e in emails if e.get('status') == 'sent'])
            print(f"  Total:         {total}")
            print(f"  Drafts:        {drafts}")
            print(f"  Sent:          {sent}")
    else:
        print(f"  {Fore.RED}Unable to fetch{Style.RESET_ALL}")
    
    print(f"\n{Style.DIM}{'─' * 50}{Style.RESET_ALL}")
    print(f"  Dashboard: http://localhost:5173")
    print(f"  API Docs:  http://localhost:8000/docs{Style.RESET_ALL}")

# ============================================================
# CONFIG COMMANDS
# ============================================================

def config_show(args):
    """Show current configuration."""
    print_header("⚙️ CONFIGURATION")
    
    config = load_config()
    print(f"  API URL: {config.get('api_url', DEFAULT_API_URL)}")
    print(f"  Token:   {'✓ Set' if config.get('token') else '✗ Not set'}")
    print(f"  Config:  {CONFIG_FILE}")

def config_login(args):
    """Login and save token."""
    print_header("🔐 LOGIN")
    
    email = args.email or input("Email: ")
    password = args.password or input("Password: ")
    
    config = load_config()
    url = f"{config['api_url']}/auth/login"
    
    try:
        response = requests.post(url, json={'email': email, 'password': password})
        
        if response.status_code == 200:
            data = response.json()
            config['token'] = data.get('access_token')
            save_config(config)
            print_success("Login successful! Token saved.")
        else:
            print_error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to API at {config['api_url']}")

def config_set_url(args):
    """Set API URL."""
    config = load_config()
    config['api_url'] = args.url.rstrip('/')
    save_config(config)
    print_success(f"API URL set to: {config['api_url']}")

def config_logout(args):
    """Clear saved token."""
    config = load_config()
    config['token'] = None
    save_config(config)
    print_success("Logged out. Token cleared.")

# ============================================================
# MAIN CLI SETUP
# ============================================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='🚀 SalesAgent CLI - AI-Powered Sales Outreach',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  salesagent leads list
  salesagent leads import contacts.csv
  salesagent leads add --name "John Doe" --email "john@example.com" --company "TechCorp"
  salesagent campaigns create "Q1 Outreach" --template friendly
  salesagent campaigns start 1
  salesagent emails generate --lead 5
  salesagent emails approve 1
  salesagent stats
  salesagent config login
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # ─────────────────────────────────────────────────────────
    # LEADS COMMANDS
    # ─────────────────────────────────────────────────────────
    leads_parser = subparsers.add_parser('leads', help='Manage leads')
    leads_subparsers = leads_parser.add_subparsers(dest='subcommand')
    
    # leads list
    leads_list_parser = leads_subparsers.add_parser('list', help='List all leads')
    leads_list_parser.add_argument('--status', help='Filter by status')
    leads_list_parser.add_argument('--limit', type=int, help='Limit results')
    leads_list_parser.set_defaults(func=leads_list)
    
    # leads add
    leads_add_parser = leads_subparsers.add_parser('add', help='Add a new lead')
    leads_add_parser.add_argument('--name', required=True, help='Lead name')
    leads_add_parser.add_argument('--email', required=True, help='Lead email')
    leads_add_parser.add_argument('--company', required=True, help='Company name')
    leads_add_parser.add_argument('--title', help='Job title')
    leads_add_parser.add_argument('--priority', choices=['high', 'medium', 'low'], help='Priority')
    leads_add_parser.add_argument('--linkedin', help='LinkedIn URL')
    leads_add_parser.set_defaults(func=leads_add)
    
    # leads import
    leads_import_parser = leads_subparsers.add_parser('import', help='Import leads from CSV')
    leads_import_parser.add_argument('file', help='CSV file path')
    leads_import_parser.set_defaults(func=leads_import)
    
    # leads view
    leads_view_parser = leads_subparsers.add_parser('view', help='View lead details')
    leads_view_parser.add_argument('id', type=int, help='Lead ID')
    leads_view_parser.set_defaults(func=leads_view)
    
    # leads delete
    leads_delete_parser = leads_subparsers.add_parser('delete', help='Delete a lead')
    leads_delete_parser.add_argument('id', type=int, help='Lead ID')
    leads_delete_parser.add_argument('-f', '--force', action='store_true', help='Skip confirmation')
    leads_delete_parser.set_defaults(func=leads_delete)
    
    # ─────────────────────────────────────────────────────────
    # CAMPAIGNS COMMANDS
    # ─────────────────────────────────────────────────────────
    campaigns_parser = subparsers.add_parser('campaigns', help='Manage campaigns')
    campaigns_subparsers = campaigns_parser.add_subparsers(dest='subcommand')
    
    # campaigns list
    campaigns_list_parser = campaigns_subparsers.add_parser('list', help='List all campaigns')
    campaigns_list_parser.add_argument('--status', help='Filter by status')
    campaigns_list_parser.set_defaults(func=campaigns_list)
    
    # campaigns create
    campaigns_create_parser = campaigns_subparsers.add_parser('create', help='Create a campaign')
    campaigns_create_parser.add_argument('name', help='Campaign name')
    campaigns_create_parser.add_argument('--description', '-d', help='Description')
    campaigns_create_parser.add_argument('--template', '-t', choices=['default', 'friendly', 'direct', 'value'], help='Email template')
    campaigns_create_parser.add_argument('--daily-limit', type=int, help='Daily send limit')
    campaigns_create_parser.add_argument('--send-time', help='Send time (HH:MM)')
    campaigns_create_parser.set_defaults(func=campaigns_create)
    
    # campaigns start
    campaigns_start_parser = campaigns_subparsers.add_parser('start', help='Start a campaign')
    campaigns_start_parser.add_argument('id', type=int, help='Campaign ID')
    campaigns_start_parser.set_defaults(func=campaigns_start)
    
    # campaigns pause
    campaigns_pause_parser = campaigns_subparsers.add_parser('pause', help='Pause a campaign')
    campaigns_pause_parser.add_argument('id', type=int, help='Campaign ID')
    campaigns_pause_parser.set_defaults(func=campaigns_pause)
    
    # campaigns delete
    campaigns_delete_parser = campaigns_subparsers.add_parser('delete', help='Delete a campaign')
    campaigns_delete_parser.add_argument('id', type=int, help='Campaign ID')
    campaigns_delete_parser.add_argument('-f', '--force', action='store_true', help='Skip confirmation')
    campaigns_delete_parser.set_defaults(func=campaigns_delete)
    
    # ─────────────────────────────────────────────────────────
    # EMAILS COMMANDS
    # ─────────────────────────────────────────────────────────
    emails_parser = subparsers.add_parser('emails', help='Manage emails')
    emails_subparsers = emails_parser.add_subparsers(dest='subcommand')
    
    # emails list
    emails_list_parser = emails_subparsers.add_parser('list', help='List all emails')
    emails_list_parser.add_argument('--status', help='Filter by status')
    emails_list_parser.add_argument('--limit', type=int, help='Limit results')
    emails_list_parser.set_defaults(func=emails_list)
    
    # emails generate
    emails_generate_parser = emails_subparsers.add_parser('generate', help='Generate email for a lead')
    emails_generate_parser.add_argument('--lead', '-l', type=int, required=True, help='Lead ID')
    emails_generate_parser.add_argument('--campaign', '-c', type=int, help='Campaign ID')
    emails_generate_parser.add_argument('--template', '-t', choices=['default', 'friendly', 'direct', 'value'], help='Template')
    emails_generate_parser.set_defaults(func=emails_generate)
    
    # emails view
    emails_view_parser = emails_subparsers.add_parser('view', help='View email details')
    emails_view_parser.add_argument('id', type=int, help='Email ID')
    emails_view_parser.set_defaults(func=emails_view)
    
    # emails approve
    emails_approve_parser = emails_subparsers.add_parser('approve', help='Approve email for sending')
    emails_approve_parser.add_argument('id', type=int, help='Email ID')
    emails_approve_parser.set_defaults(func=emails_approve)
    
    # emails send
    emails_send_parser = emails_subparsers.add_parser('send', help='Send an email')
    emails_send_parser.add_argument('id', type=int, help='Email ID')
    emails_send_parser.add_argument('-f', '--force', action='store_true', help='Skip confirmation')
    emails_send_parser.set_defaults(func=emails_send)
    
    # ─────────────────────────────────────────────────────────
    # STATS COMMAND
    # ─────────────────────────────────────────────────────────
    stats_parser = subparsers.add_parser('stats', help='View dashboard statistics')
    stats_parser.set_defaults(func=show_stats)
    
    # ─────────────────────────────────────────────────────────
    # CONFIG COMMANDS
    # ─────────────────────────────────────────────────────────
    config_parser = subparsers.add_parser('config', help='Configure CLI settings')
    config_subparsers = config_parser.add_subparsers(dest='subcommand')
    
    # config show
    config_show_parser = config_subparsers.add_parser('show', help='Show current configuration')
    config_show_parser.set_defaults(func=config_show)
    
    # config login
    config_login_parser = config_subparsers.add_parser('login', help='Login and save token')
    config_login_parser.add_argument('--email', '-e', help='Email')
    config_login_parser.add_argument('--password', '-p', help='Password')
    config_login_parser.set_defaults(func=config_login)
    
    # config logout
    config_logout_parser = config_subparsers.add_parser('logout', help='Clear saved token')
    config_logout_parser.set_defaults(func=config_logout)
    
    # config set-url
    config_url_parser = config_subparsers.add_parser('set-url', help='Set API URL')
    config_url_parser.add_argument('url', help='API URL')
    config_url_parser.set_defaults(func=config_set_url)
    
    # ─────────────────────────────────────────────────────────
    # PARSE AND EXECUTE
    # ─────────────────────────────────────────────────────────
    args = parser.parse_args()
    
    if not args.command:
        # Show banner
        print(f"""
{Fore.MAGENTA}{Style.BRIGHT}
  ╔═══════════════════════════════════════════════════════╗
  ║                                                       ║
  ║   🚀 SalesAgent CLI                                   ║
  ║   AI-Powered Sales Outreach from Your Terminal        ║
  ║                                                       ║
  ╚═══════════════════════════════════════════════════════╝
{Style.RESET_ALL}
{Fore.CYAN}Commands:{Style.RESET_ALL}
  leads       Manage leads (list, add, import, delete)
  campaigns   Manage campaigns (list, create, start, pause)
  emails      Manage emails (list, generate, approve, send)
  stats       View dashboard statistics
  config      Configure CLI settings

{Fore.CYAN}Quick Start:{Style.RESET_ALL}
  salesagent config login          # Login first
  salesagent leads list            # View your leads
  salesagent stats                 # See overview

{Fore.CYAN}Help:{Style.RESET_ALL}
  salesagent <command> --help      # Get help for a command
        """)
        return
    
    # Handle subcommands that need a subcommand
    if args.command in ['leads', 'campaigns', 'emails', 'config'] and not args.subcommand:
        parser.parse_args([args.command, '--help'])
        return
    
    # Execute the command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
