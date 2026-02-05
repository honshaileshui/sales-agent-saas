"""
SalesAgent AI - Version 2.1 (No Emojis)
========================================
Production-grade AI sales agent with PostgreSQL database integration.
Fixed for Windows console compatibility (removed all emojis).

Changes from v2.0:
- Removed all emoji characters for Windows compatibility
- Added user_id parameter to research_company for caching
- Optimized model selection (Haiku for research, Sonnet for emails)

Created: Week 1
Updated: Week 6 - Windows Compatibility Fix

Author: Shailesh Hon
Mentor guidance: 30+ years IT experience
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import anthropic
import requests
import time
import logging
from datetime import datetime
import os
import json
from typing import Dict, Optional, List

# Database imports
from database import (
    init_database, test_connection,
    UserDB, LeadDB, ResearchDB, EmailDB, AgentRunDB,
    get_dashboard_stats
)

# Optional: Google Sheets for importing leads
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False
    print("Note: gspread not installed. Google Sheets import disabled.")

# ============================================================================
# CONFIGURATION LOADING
# ============================================================================

def load_config(config_path='config.json'):
    """
    Load configuration from JSON file.
    
    MENTOR NOTE: External configuration is crucial for production apps.
    Never hardcode credentials or settings that might change between
    environments (dev, staging, production).
    """
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found at {config_path}. Using defaults.")
        return get_default_config()
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"[load_config] Configuration loaded from {config_path}")
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return get_default_config()
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return get_default_config()


def get_default_config():
    """Returns default configuration if config file is missing."""
    return {
        "credentials": {
            "google_sheets_credentials_path": "credentials.json",
            "sheet_name": "SalesLeads",
            "anthropic_api_key": "",
            "serper_api_key": ""
        },
        "agent_settings": {
            "max_retries": 3,
            "retry_delay_seconds": 2,
            "max_leads_per_run": 50,
            "delay_between_leads_seconds": 2
        },
        "research_settings": {
            "depth": "standard",
            "include_news": True,
            "include_funding_info": True,
            "max_search_results": 5,
            "cache_hours": 24
        },
        "email_settings": {
            "tone": "professional",
            "template": "default",
            "max_length_words": 150,
            "include_signature": True,
            "sender_name": "[Your Name]"
        },
        "feature_flags": {
            "enable_research": True,
            "enable_email_generation": True,
            "auto_send_emails": False,
            "enable_analytics": True,
            "use_database": True,
            "sync_to_sheets": False,
            "cost_optimized": True
        },
        "model_settings": {
            "research_model": "claude-3-haiku-20240307",
            "email_model": "claude-sonnet-4-20250514",
            "fallback_model": "claude-sonnet-4-20250514"
        }
    }


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """
    Configure logging to write to both file and console.
    
    MENTOR NOTE: Good logging is your best friend in production.
    When something breaks at 3 AM, logs are all you have.
    Always log: timestamps, severity levels, and context.
    """
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_filename = f"logs/sales_agent_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Create formatter (no emojis)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Configure root logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Initialize logging first
logger = setup_logging()

# Load configuration
CONFIG = load_config()

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=CONFIG['credentials']['anthropic_api_key'])


# ============================================================================
# EMAIL TEMPLATES
# ============================================================================

EMAIL_TEMPLATES = {
    "default": {
        "structure": """Hi {name},

{opening_line}

{value_proposition}

{call_to_action}

Best regards,
{sender_name}""",
        "opening_style": "reference_research",
        "cta_style": "meeting_request"
    },
    
    "brief": {
        "structure": """Hi {name},

{opening_line}

{value_proposition}

{call_to_action}

{sender_name}""",
        "opening_style": "direct",
        "cta_style": "quick_question"
    },
    
    "consultative": {
        "structure": """Dear {name},

{opening_line}

{value_proposition}

{social_proof}

{call_to_action}

Warm regards,
{sender_name}""",
        "opening_style": "insight_driven",
        "cta_style": "value_conversation"
    },
    
    "partnership": {
        "structure": """Hi {name},

{opening_line}

{partnership_angle}

{call_to_action}

Looking forward to connecting,
{sender_name}""",
        "opening_style": "mutual_benefit",
        "cta_style": "exploration_call"
    }
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_api_call(func, *args, max_retries=None, **kwargs):
    """
    Wrapper function that adds retry logic to any API call.
    
    MENTOR NOTE: Network calls WILL fail. Always implement retry logic
    with exponential backoff for production systems. But also know when
    to give up - infinite retries can cause cascading failures.
    """
    if max_retries is None:
        max_retries = CONFIG['agent_settings']['max_retries']
    retry_delay = CONFIG['agent_settings']['retry_delay_seconds']
    
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                # Exponential backoff
                sleep_time = retry_delay * (2 ** attempt)
                time.sleep(sleep_time)
            else:
                logger.error(f"API call failed after {max_retries} attempts: {str(e)}")
                return None
    
    return None


def validate_email(email: str) -> bool:
    """Basic email validation."""
    if not email or '@' not in email or '.' not in email:
        return False
    # Check for common typos
    invalid_domains = ['gmial.com', 'gmil.com', 'gmal.com', 'yahooo.com']
    domain = email.split('@')[-1].lower()
    if domain in invalid_domains:
        logger.warning(f"Possible typo in email domain: {email}")
    return True


def validate_lead_data(lead_data: Dict) -> tuple:
    """
    Validate that lead data has all required fields.
    
    MENTOR NOTE: Validate early, validate often. Bad data in = bad data out.
    This is called "defensive programming" - assume all input is potentially wrong.
    """
    required_fields = ['name', 'email', 'company']
    
    for field in required_fields:
        if field not in lead_data or not lead_data[field]:
            return False, f"Missing required field: {field}"
    
    if not validate_email(lead_data['email']):
        return False, f"Invalid email format: {lead_data['email']}"
    
    # Sanitize data
    lead_data['name'] = lead_data['name'].strip()
    lead_data['email'] = lead_data['email'].strip().lower()
    lead_data['company'] = lead_data['company'].strip()
    
    return True, ""


# ============================================================================
# GOOGLE SHEETS FUNCTIONS (For Import Only)
# ============================================================================

def connect_to_sheet():
    """Connects to Google Sheet for importing leads."""
    if not GSHEETS_AVAILABLE:
        logger.error("Google Sheets not available. Install gspread.")
        return None
    
    try:
        logger.info("Connecting to Google Sheets...")
        
        creds_path = CONFIG['credentials']['google_sheets_credentials_path']
        sheet_name = CONFIG['credentials']['sheet_name']
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(creds)
        
        sheet = gc.open(sheet_name).sheet1
        logger.info("Successfully connected to Google Sheets")
        
        return sheet
        
    except Exception as e:
        logger.error(f"Failed to connect to Google Sheets: {str(e)}")
        return None


def import_leads_from_sheets(user_id: str) -> int:
    """
    Import leads from Google Sheets into the database.
    
    MENTOR NOTE: This is a migration pattern - we keep the old system
    working while transitioning to the new one. Never do a "big bang"
    migration in production. Always have a fallback.
    """
    sheet = connect_to_sheet()
    if not sheet:
        return 0
    
    try:
        all_values = sheet.get_all_values()
        
        if len(all_values) < 2:
            logger.warning("Sheet has no data rows")
            return 0
        
        headers = [h.lower().strip() for h in all_values[0]]
        leads_data = []
        
        for row in all_values[1:]:
            if len(row) >= 4:
                lead = {
                    'name': row[0],
                    'email': row[1],
                    'company': row[2],
                    'job_title': row[3] if len(row) > 3 else ''
                }
                
                # Validate before adding
                is_valid, _ = validate_lead_data(lead)
                if is_valid:
                    leads_data.append(lead)
        
        # Bulk insert into database
        imported = LeadDB.bulk_create(user_id, leads_data, source='google_sheets')
        logger.info(f"Imported {imported} leads from Google Sheets")
        
        return imported
        
    except Exception as e:
        logger.error(f"Failed to import from sheets: {e}")
        return 0


# ============================================================================
# WEB SEARCH FUNCTIONS
# ============================================================================

def search_web(query: str) -> Optional[Dict]:
    """
    Performs a web search using Serper API.
    
    MENTOR NOTE: Always set timeouts on HTTP requests. A hanging request
    can block your entire application. 10 seconds is usually reasonable.
    """
    url = "https://google.serper.dev/search"
    
    max_results = CONFIG['research_settings']['max_search_results']
    
    payload = {
        "q": query,
        "num": max_results
    }
    
    headers = {
        "X-API-KEY": CONFIG['credentials']['serper_api_key'],
        "Content-Type": "application/json"
    }
    
    def make_request():
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    
    result = safe_api_call(make_request)
    
    if result:
        logger.debug(f"Search successful for: {query}")
    else:
        logger.warning(f"Search failed for: {query}")
    
    return result


def extract_company_details(search_results: Dict) -> Dict:
    """Extract structured company information from search results."""
    details = {
        "description": "",
        "industry": "",
        "size": "",
        "recent_news": [],
        "funding": ""
    }
    
    if not search_results or 'organic' not in search_results:
        return details
    
    # Extract description from first result
    if len(search_results['organic']) > 0:
        first_result = search_results['organic'][0]
        details['description'] = first_result.get('snippet', '')
    
    # Look for company size, industry hints in snippets
    for result in search_results['organic'][:3]:
        snippet = result.get('snippet', '').lower()
        
        # Industry detection
        industry_keywords = {
            'software': 'Software/SaaS',
            'saas': 'Software/SaaS',
            'finance': 'Finance/Fintech',
            'fintech': 'Finance/Fintech',
            'healthcare': 'Healthcare',
            'medical': 'Healthcare',
            'retail': 'Retail/E-commerce',
            'ecommerce': 'Retail/E-commerce',
            'manufacturing': 'Manufacturing',
            'consulting': 'Consulting/Services'
        }
        
        for keyword, industry in industry_keywords.items():
            if keyword in snippet and not details['industry']:
                details['industry'] = industry
                break
        
        # Size detection
        if 'employees' in snippet and not details['size']:
            details['size'] = snippet[:200]
    
    return details

# ============================================================================
# RESEARCH FUNCTIONS (with caching and cost optimization)
# ============================================================================

def get_cached_research(company_name: str, user_id: str = None) -> Optional[Dict]:
    """
    Check if we have recent research for this company.
    
    Returns cached research if available and not expired.
    """
    try:
        from database import get_db_cursor
        
        cache_hours = CONFIG['research_settings'].get('cache_hours', 24)
        
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT r.* FROM lead_research r
                JOIN leads l ON r.lead_id = l.id
                WHERE r.company_name ILIKE %s
                AND r.created_at > NOW() - INTERVAL '%s hours'
                ORDER BY r.created_at DESC
                LIMIT 1
            """, (company_name, cache_hours))
            
            cached = cursor.fetchone()
            
            if cached:
                logger.info(f"[CACHE HIT] Found cached research for: {company_name}")
                return dict(cached)
                
    except Exception as e:
        logger.warning(f"[get_cached_research] Cache lookup failed: {e}")
    
    return None


def research_company(company_name: str, user_id: str = None) -> Dict:
    """
    Performs comprehensive research on a company.
    
    Now with caching support and cost-optimized model selection!
    
    MENTOR NOTE: This is the "intelligence gathering" phase. The quality
    of your outreach depends entirely on the quality of research. 
    Garbage in, garbage out.
    """
    logger.info(f"[research_company] Researching company: {company_name}")
    
    # Check cache first
    cached = get_cached_research(company_name, user_id)
    if cached:
        return {
            'company_name': company_name,
            'summary': cached.get('ai_summary', ''),
            'details': {
                'description': cached.get('company_description', ''),
                'industry': cached.get('industry', ''),
                'size': cached.get('company_size', ''),
                'funding': cached.get('funding_info', '')
            },
            'news': cached.get('news_items', []),
            'search_results': cached.get('search_results', []),
            'cached': True
        }
    
    logger.info(f"[research_company] No cache found, performing fresh research for: {company_name}")
    
    research_data = {
        "company_name": company_name,
        "details": {},
        "news": [],
        "search_results": [],
        "summary": "",
        "cached": False
    }
    
    if not CONFIG['feature_flags']['enable_research']:
        logger.info("Research disabled by feature flag")
        research_data['summary'] = f"Research skipped for {company_name}"
        return research_data
    
    # Search for general company information
    company_results = search_web(f"{company_name} company")
    
    if company_results:
        research_data['details'] = extract_company_details(company_results)
        research_data['search_results'] = company_results.get('organic', [])[:5]
    
    # Search for recent news if enabled
    if CONFIG['research_settings']['include_news']:
        news_results = search_web(f"{company_name} news recent")
        
        if news_results and 'organic' in news_results:
            for result in news_results['organic'][:3]:
                research_data['news'].append({
                    "title": result.get('title', ''),
                    "snippet": result.get('snippet', ''),
                    "link": result.get('link', '')
                })
    
    # Search for funding info if enabled
    if CONFIG['research_settings']['include_funding_info']:
        funding_results = search_web(f"{company_name} funding investment")
        if funding_results and 'organic' in funding_results:
            for result in funding_results['organic'][:2]:
                snippet = result.get('snippet', '').lower()
                if any(word in snippet for word in ['million', 'billion', 'raised', 'series', 'funding']):
                    research_data['details']['funding'] = result.get('snippet', '')
                    break
    
    # Create AI summary (using cost-optimized model)
    research_data['summary'] = create_research_summary(research_data)
    
    return research_data


def create_research_summary(research_data: Dict) -> str:
    """
    Use Claude to create a concise summary of research findings.
    
    Uses Haiku model for cost optimization when enabled.
    """
    company_name = research_data['company_name']
    details = research_data['details']
    news = research_data['news']
    
    if not details.get('description') and not news:
        return f"Limited information found for {company_name}."
    
    context_parts = []
    
    if details.get('description'):
        context_parts.append(f"Company: {details['description']}")
    
    if details.get('industry'):
        context_parts.append(f"Industry: {details['industry']}")
    
    if details.get('funding'):
        context_parts.append(f"Funding: {details['funding']}")
    
    for news_item in news[:2]:
        context_parts.append(f"News: {news_item['title']} - {news_item['snippet']}")
    
    context = "\n".join(context_parts)
    
    prompt = f"""Analyze this company information and create a concise 3-4 sentence summary focusing on facts relevant for sales outreach:

{context}

Focus on: what they do, company scale/stage, recent notable events, and anything that would help personalize outreach. Be specific and factual."""
    
    # Select model based on cost optimization setting
    if CONFIG['feature_flags'].get('cost_optimized', True):
        model = CONFIG.get('model_routing', {}).get('research_summary', 'claude-3-haiku-20240307')
    else:
        model = CONFIG.get('model_routing', {}).get('email_generation', 'claude-sonnet-4-20250514')
    
    logger.info(f"[create_research_summary] Using {model} for research summary (cost-optimized)")
    
    def analyze():
        message = client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    summary = safe_api_call(analyze)
    return summary if summary else f"Research conducted for {company_name}."


# ============================================================================
# EMAIL GENERATION (with cost optimization)
# ============================================================================

def generate_personalized_email(lead_data: Dict, research_data: Dict) -> Optional[Dict]:
    """
    Uses Claude to generate a personalized outreach email.
    
    Returns dict with 'subject' and 'body' keys.
    
    Uses Sonnet model for best quality email generation.
    
    MENTOR NOTE: The magic of AI-powered sales is HERE. A generic email
    gets 1% response rate. A personalized email can get 10-20%. 
    That's the difference between success and failure.
    """
    if not CONFIG['feature_flags']['enable_email_generation']:
        logger.info("Email generation disabled by feature flag")
        return None
    
    logger.info(f"[generate_personalized_email] Generating email for {lead_data['name']}")
    
    tone = CONFIG['email_settings']['tone']
    template_name = CONFIG['email_settings']['template']
    max_words = CONFIG['email_settings']['max_length_words']
    sender_name = CONFIG['email_settings']['sender_name']
    
    template = EMAIL_TEMPLATES.get(template_name, EMAIL_TEMPLATES['default'])
    
    tone_guide = {
        'casual': 'friendly and conversational, use contractions',
        'professional': 'professional but warm, clear and respectful',
        'formal': 'formal business language, very respectful'
    }
    
    # Get research summary
    if research_data and isinstance(research_data, dict):
        research_summary = research_data.get('summary', f"Company: {lead_data['company']}")
    else:
        research_summary = f"Company: {lead_data.get('company', 'Unknown')}"
    
    prompt = f"""You are writing a sales outreach email. Generate BOTH a subject line and email body.

Template structure to follow:
{template['structure']}

Lead Information:
- Name: {lead_data['name']}
- Company: {lead_data['company']}
- Job Title: {lead_data.get('job_title', 'Professional')}

Research Summary:
{research_summary}

Instructions:
1. Write in a {tone_guide.get(tone, 'professional')} tone
2. Maximum {max_words} words for the body
3. Reference specific research findings naturally
4. Make the opening line compelling and personalized
5. Clear value proposition relevant to their role
6. Specific, easy call-to-action
7. Sign with: {sender_name}

Respond in this exact format:
SUBJECT: [Your subject line here]
BODY:
[Your email body here]"""
    
    # Always use Sonnet for email generation (quality matters here)
    model = CONFIG.get('model_routing', {}).get('email_generation', 'claude-sonnet-4-20250514')
    logger.info(f"[generate_personalized_email] Using {model} for email generation (best quality)")
    
    def generate():
        message = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    response = safe_api_call(generate)
    
    if not response:
        logger.error(f"Failed to generate email for {lead_data['name']}")
        return None
    
    # Parse the response
    result = {'subject': '', 'body': response}
    
    if 'SUBJECT:' in response and 'BODY:' in response:
        parts = response.split('BODY:', 1)
        subject_part = parts[0].replace('SUBJECT:', '').strip()
        body_part = parts[1].strip() if len(parts) > 1 else response
        result = {'subject': subject_part, 'body': body_part}
    
    logger.info(f"[generate_personalized_email] Email generated successfully for {lead_data['name']}")
    return result


# ============================================================================
# DATABASE-INTEGRATED ANALYTICS
# ============================================================================

class DatabaseAnalytics:
    """
    Analytics tracking that saves directly to database.
    Replaces the file-based analytics from v1.0.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.db_run = None
        self.metrics = {
            'leads_processed': 0,
            'leads_skipped': 0,
            'leads_failed': 0,
            'research_successes': 0,
            'research_failures': 0,
            'email_gen_successes': 0,
            'email_gen_failures': 0,
            'errors': [],
            'lead_times': []
        }
        self.start_time = None
    
    def start_run(self, config: Dict):
        """Start tracking a new agent run."""
        self.start_time = datetime.now()
        
        # Create run record in database
        self.db_run = AgentRunDB.create(
            user_id=self.user_id,
            run_id=self.run_id,
            config_snapshot=config
        )
        
        logger.info(f"Analytics run started: {self.run_id}")
    
    def record_lead_processed(self, success: bool = True):
        if success:
            self.metrics['leads_processed'] += 1
        else:
            self.metrics['leads_failed'] += 1
    
    def record_lead_skipped(self):
        self.metrics['leads_skipped'] += 1
    
    def record_research_result(self, success: bool):
        if success:
            self.metrics['research_successes'] += 1
        else:
            self.metrics['research_failures'] += 1
    
    def record_email_gen_result(self, success: bool):
        if success:
            self.metrics['email_gen_successes'] += 1
        else:
            self.metrics['email_gen_failures'] += 1
    
    def record_error(self, error_type: str, message: str, lead_name: str = None):
        self.metrics['errors'].append({
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message,
            'lead': lead_name
        })
    
    def record_lead_time(self, lead_name: str, duration: float):
        self.metrics['lead_times'].append({
            'lead': lead_name,
            'duration': duration
        })
    
    def end_run(self) -> Dict:
        """Finalize and save run metrics to database."""
        # Calculate success rate
        total = self.metrics['leads_processed'] + self.metrics['leads_failed']
        if total > 0:
            self.metrics['success_rate'] = self.metrics['leads_processed'] / total
        else:
            self.metrics['success_rate'] = 0
        
        # Calculate average processing time
        if self.metrics['lead_times']:
            times = [t['duration'] for t in self.metrics['lead_times']]
            self.metrics['avg_lead_processing_time'] = sum(times) / len(times)
        else:
            self.metrics['avg_lead_processing_time'] = 0
        
        # Save to database
        if self.db_run:
            AgentRunDB.complete(self.run_id, self.metrics)
        
        logger.info(f"Analytics run completed: {self.run_id}")
        return self.metrics
    
    def get_summary_report(self) -> str:
        """Generate a human-readable summary (no emojis for Windows)."""
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        report = [
            "\n" + "=" * 70,
            "AGENT PERFORMANCE SUMMARY",
            "=" * 70,
            f"Run ID: {self.run_id}",
            f"Duration: {duration:.2f} seconds",
            "",
            "LEAD PROCESSING:",
            f"  [OK] Processed Successfully: {self.metrics['leads_processed']}",
            f"  [->] Skipped (Already Done): {self.metrics['leads_skipped']}",
            f"  [X]  Failed: {self.metrics['leads_failed']}",
            f"  Success Rate: {self.metrics.get('success_rate', 0)*100:.1f}%",
            "",
            "COMPONENT PERFORMANCE:",
            f"  Research Successes: {self.metrics['research_successes']}",
            f"  Research Failures: {self.metrics['research_failures']}",
            f"  Email Gen Successes: {self.metrics['email_gen_successes']}",
            f"  Email Gen Failures: {self.metrics['email_gen_failures']}",
        ]
        
        if self.metrics['errors']:
            report.extend([
                "",
                f"[!] ERRORS: {len(self.metrics['errors'])}",
                "  (Check logs for details)"
            ])
        
        report.append("=" * 70)
        
        return "\n".join(report)


# ============================================================================
# MAIN PROCESSING LOGIC
# ============================================================================

def process_single_lead(lead: Dict, user_id: str, analytics: DatabaseAnalytics) -> bool:
    """
    Process a single lead: research + generate email.
    
    MENTOR NOTE: Breaking this into a separate function makes the code
    more testable and easier to understand. Each function should do ONE thing well.
    """
    lead_id = str(lead['id'])
    lead_name = lead['name']
    company = lead['company']
    
    start_time = time.time()
    success = True
    
    logger.info(f"Processing: {lead_name} from {company}")
    
    # Step 1: Research the company
    try:
        research_data = research_company(company, user_id)
        
        # Only save to DB if not cached
        if not research_data.get('cached', False):
            ResearchDB.create(
                lead_id=lead_id,
                company_name=company,
                ai_summary=research_data['summary'],
                company_description=research_data['details'].get('description'),
                industry=research_data['details'].get('industry'),
                company_size=research_data['details'].get('size'),
                funding_info=research_data['details'].get('funding'),
                search_results=research_data.get('search_results', []),
                news_items=research_data.get('news', []),
                research_depth=CONFIG['research_settings']['depth']
            )
        
        # Update lead status
        LeadDB.update_status(lead_id, 'researched')
        analytics.record_research_result(success=True)
        
    except Exception as e:
        logger.error(f"Research failed for {lead_name}: {e}")
        analytics.record_research_result(success=False)
        analytics.record_error("research_failed", str(e), lead_name)
        research_data = {"summary": f"Research failed for {company}"}
        success = False
    
    # Step 2: Generate personalized email
    try:
        lead_data = {
            'name': lead_name,
            'email': lead['email'],
            'company': company,
            'job_title': lead.get('job_title', '')
        }
        
        email_result = generate_personalized_email(lead_data, research_data)
        
        if email_result:
            # Get research ID for linking
            research_record = ResearchDB.get_by_lead_id(lead_id)
            research_id = str(research_record['id']) if research_record else None
            
            # Save email to database
            EmailDB.create(
                lead_id=lead_id,
                subject=email_result.get('subject', ''),
                body=email_result['body'],
                template_used=CONFIG['email_settings']['template'],
                tone=CONFIG['email_settings']['tone'],
                research_id=research_id
            )
            
            # Update lead status
            LeadDB.update_status(lead_id, 'email_drafted')
            analytics.record_email_gen_result(success=True)
        else:
            analytics.record_email_gen_result(success=False)
            success = False
            
    except Exception as e:
        logger.error(f"Email generation failed for {lead_name}: {e}")
        analytics.record_email_gen_result(success=False)
        analytics.record_error("email_gen_failed", str(e), lead_name)
        success = False
    
    # Record timing
    duration = time.time() - start_time
    analytics.record_lead_time(lead_name, duration)
    analytics.record_lead_processed(success=success)
    
    status_symbol = "[OK]" if success else "[X]"
    logger.info(f"{status_symbol} Completed {lead_name} in {duration:.2f}s")
    
    return success


def process_leads(user_id: str = None, limit: int = None):
    """
    Main function that processes leads from the database.
    
    MENTOR NOTE: This is the "orchestrator" - it coordinates all the pieces
    but doesn't do the detailed work itself. This separation of concerns
    makes the code maintainable as it grows.
    """
    
    # Initialize database connection
    if not test_connection():
        logger.error("Database connection failed. Aborting.")
        return
    
    # Get user (use first user if not specified - for single-user mode)
    if user_id is None:
        user = UserDB.get_first_user()
        if not user:
            logger.error("No user found in database. Please create a user first.")
            return
        user_id = str(user['id'])
        logger.info(f"Using user: {user['full_name']} ({user['email']})")
    
    # Initialize analytics
    analytics = DatabaseAnalytics(user_id)
    analytics.start_run(CONFIG)
    
    # Print startup banner (no emojis)
    logger.info("=" * 70)
    logger.info("SalesAgent AI v2.1 - Starting...")
    logger.info(f"Database Mode: ENABLED")
    logger.info(f"Cost Optimization: {'ENABLED' if CONFIG['feature_flags'].get('cost_optimized', True) else 'DISABLED'}")
    logger.info(f"Research: {'ENABLED' if CONFIG['feature_flags']['enable_research'] else 'DISABLED'}")
    logger.info(f"Email Generation: {'ENABLED' if CONFIG['feature_flags']['enable_email_generation'] else 'DISABLED'}")
    logger.info(f"Template: {CONFIG['email_settings']['template']}")
    logger.info(f"Tone: {CONFIG['email_settings']['tone']}")
    logger.info("=" * 70)
    
    # Get unprocessed leads from database
    max_leads = limit or CONFIG['agent_settings']['max_leads_per_run']
    leads = LeadDB.get_unprocessed(user_id, limit=max_leads)
    
    if not leads:
        logger.info("No unprocessed leads found.")
        logger.info("Tip: Import leads using import_leads_from_sheets() or add them via the API")
        analytics.end_run()
        return
    
    logger.info(f"Found {len(leads)} leads to process")
    
    # Process each lead
    processed = 0
    failed = 0
    
    for lead in leads:
        try:
            success = process_single_lead(lead, user_id, analytics)
            if success:
                processed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Unexpected error processing lead: {e}")
            analytics.record_error("unexpected", str(e), lead.get('name', 'Unknown'))
            failed += 1
        
        # Delay between leads to avoid rate limiting
        delay = CONFIG['agent_settings']['delay_between_leads_seconds']
        time.sleep(delay)
    
    # Finalize analytics
    analytics.end_run()
    
    # Print summary (no emojis)
    logger.info("\n" + "=" * 70)
    logger.info("SalesAgent AI - Run Complete!")
    logger.info(f"Processed: {processed} | Failed: {failed} | Skipped: {analytics.metrics['leads_skipped']}")
    logger.info("=" * 70)
    
    print(analytics.get_summary_report())
    
    # Show dashboard stats (no emojis)
    stats = get_dashboard_stats(user_id)
    print(f"\n[STATS] Dashboard: {stats['leads']['total']} total leads")
    print(f"   By status: {stats['leads']['by_status']}")


# ============================================================================
# CLI COMMANDS
# ============================================================================

def show_dashboard():
    """Display current dashboard statistics (no emojis)."""
    if not test_connection():
        print("[ERROR] Database connection failed")
        return
    
    user = UserDB.get_first_user()
    if not user:
        print("[ERROR] No user found")
        return
    
    stats = get_dashboard_stats(str(user['id']))
    
    print("\n" + "=" * 50)
    print("[DASHBOARD] SALESAGENT DASHBOARD")
    print("=" * 50)
    print(f"User: {user['full_name']}")
    print(f"Total Leads: {stats['leads']['total']}")
    print("\nLeads by Status:")
    for status, count in stats['leads']['by_status'].items():
        print(f"  {status}: {count}")
    
    if stats['runs'].get('total_runs'):
        print(f"\nTotal Runs: {stats['runs']['total_runs']}")
        print(f"Avg Success Rate: {float(stats['runs'].get('avg_success_rate', 0))*100:.1f}%")
    print("=" * 50)


def import_from_sheets():
    """Import leads from Google Sheets (no emojis)."""
    if not test_connection():
        print("[ERROR] Database connection failed")
        return
    
    user = UserDB.get_first_user()
    if not user:
        print("[ERROR] No user found")
        return
    
    print("[IMPORT] Importing leads from Google Sheets...")
    count = import_leads_from_sheets(str(user['id']))
    print(f"[OK] Imported {count} leads")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'dashboard':
            show_dashboard()
        elif command == 'import':
            import_from_sheets()
        elif command == 'test':
            print("Testing database connection...")
            if test_connection():
                print("[OK] Database connection successful!")
            else:
                print("[ERROR] Database connection failed!")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: dashboard, import, test")
            print("Or run without arguments to process leads")
    else:
        # Default: process leads
        process_leads()