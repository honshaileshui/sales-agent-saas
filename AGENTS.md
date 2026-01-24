# 🤖 AGENTS.md - SalesAgent AI

> **Purpose:** This file helps AI assistants (Claude, ChatGPT, Cursor, etc.) understand this project instantly. Read this FIRST before making any changes.

---

## 📋 PROJECT OVERVIEW

**Project Name:** SalesAgent AI  
**Description:** AI-powered Sales Development Representative (SDR) platform that automates lead research, personalized email generation, and outreach campaigns.  
**Target Market:** SaaS Startups (Series A-B), then expanding to Recruitment, Marketing Agencies, Real Estate  
**Pricing:** $299/month (competing with $2,500/month tools like 11x.ai)

### The Problem We Solve
Sales teams spend 70% of their time on manual research and email writing instead of closing deals. Existing AI SDR tools are either too expensive ($2,500/month) or too shallow (just name/company swaps).

### Our Competitive Advantage (6 Gaps We Fill)
1. **Deep Personalization** - 3-layer research (Personal + Company + Industry)
2. **Conversation Intelligence** - Stateful memory + sentiment tracking
3. **Omnichannel** - Email + LinkedIn + Twitter orchestration
4. **Smart Reply Detection** - AI classifies Hot/Warm/Nurture/Objection
5. **Predictive Intelligence** - Intent scoring tells WHO to contact WHEN
6. **Advanced Analytics** - Revenue attribution + ROI proof

---

## 🏗️ ARCHITECTURE

```
SalesAgent AI/
├── api/                    # FastAPI Backend
│   ├── main.py            # Entry point - FastAPI app
│   ├── auth.py            # JWT authentication
│   ├── models.py          # Pydantic models
│   └── routes/            # API endpoints
│       ├── leads.py       # /api/leads/*
│       ├── campaigns.py   # /api/campaigns/*
│       ├── emails.py      # /api/emails/*
│       ├── analytics.py   # /api/analytics/*
│       └── auth.py        # /auth/*
│
├── frontend/              # React Frontend (Vite)
│   ├── src/
│   │   ├── api.js        # Axios API client
│   │   ├── App.jsx       # Main app + routing
│   │   ├── pages/        # Page components
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Leads.jsx
│   │   │   ├── Campaigns.jsx
│   │   │   └── Emails.jsx
│   │   └── components/   # Reusable components
│   │       └── Layout.jsx
│   └── package.json
│
├── database.py            # SQLAlchemy models + database connection
├── sales_agent.py         # Core AI agent logic
├── analytics.py           # Analytics engine
├── config/               # Configuration files
├── utils/                # Utility functions
├── .venv/                # Python virtual environment
└── AGENTS.md             # THIS FILE
```

---

## 🔧 TECH STACK

| Layer | Technology | Notes |
|-------|------------|-------|
| **Backend** | FastAPI (Python 3.11+) | Async, fast, auto-docs |
| **Frontend** | React 18 + Vite | Fast dev server, modern React |
| **Database** | PostgreSQL + SQLAlchemy | Relational, robust |
| **Auth** | JWT tokens | Stored in localStorage |
| **AI** | Claude API (Anthropic) | For email generation |
| **Styling** | Inline styles (JS objects) | No separate CSS files |
| **Icons** | Lucide React | Consistent icon set |
| **HTTP Client** | Axios | With interceptors for auth |

---

## 🚀 HOW TO RUN

### Start Backend (Terminal 1)
```powershell
cd "C:\Users\shail\OneDrive\Desktop\new Project"
.\.venv\Scripts\Activate.ps1
uvicorn api.main:app --reload --port 8000
```
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### Start Frontend (Terminal 2)
```powershell
cd "C:\Users\shail\OneDrive\Desktop\new Project\frontend"
npm run dev
```
- App: http://localhost:5173

---

## 📐 CODING STANDARDS

### Backend (Python/FastAPI)

```python
# ✅ DO: Use async functions for routes
@router.get("/leads")
async def get_leads(db: Session = Depends(get_db)):
    return await lead_service.get_all(db)

# ✅ DO: Use Pydantic models for request/response
class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    company: str

# ✅ DO: Handle errors gracefully
@router.get("/leads/{id}")
async def get_lead(id: int, db: Session = Depends(get_db)):
    lead = await lead_service.get(db, id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

# ❌ DON'T: Use sync functions for I/O operations
# ❌ DON'T: Return raw database models (use Pydantic)
# ❌ DON'T: Hardcode configuration values
```

### Frontend (React)

```jsx
// ✅ DO: Use functional components with hooks
function Leads() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchLeads();
  }, []);
  
  // ...
}

// ✅ DO: Use inline styles (consistent with existing code)
const styles = {
  container: {
    padding: '30px',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  title: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1a1a2e',
  },
};

// ✅ DO: Handle loading and empty states
{loading ? (
  <div>Loading...</div>
) : leads.length === 0 ? (
  <div>No leads found</div>
) : (
  <LeadsList leads={leads} />
)}

// ✅ DO: Use try-catch for API calls
const fetchLeads = async () => {
  try {
    const response = await leadsAPI.getAll();
    setLeads(response.data.leads);
  } catch (err) {
    console.error('Failed to fetch leads:', err);
  } finally {
    setLoading(false);
  }
};

// ❌ DON'T: Use class components
// ❌ DON'T: Use separate CSS files
// ❌ DON'T: Forget error handling
// ❌ DON'T: Leave console.logs in production
```

### Styling Guidelines

```javascript
// Color palette (use consistently)
const colors = {
  primary: '#667eea',        // Purple - main actions
  primaryGradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  success: '#10b981',        // Green - success states
  warning: '#f59e0b',        // Yellow - warnings
  danger: '#ef4444',         // Red - errors, delete
  text: '#1a1a2e',          // Dark - headings
  textMuted: '#666',        // Gray - secondary text
  background: '#f5f7fa',    // Light gray - page bg
  card: '#ffffff',          // White - cards
  border: '#e0e0e0',        // Light - borders
};

// Status badge colors
const statusColors = {
  new: { bg: '#e0e7ff', text: '#4338ca' },
  researched: { bg: '#fef3c7', text: '#d97706' },
  email_drafted: { bg: '#d1fae5', text: '#059669' },
  email_sent: { bg: '#dbeafe', text: '#2563eb' },
  replied: { bg: '#f3e8ff', text: '#9333ea' },
  converted: { bg: '#dcfce7', text: '#16a34a' },
};
```

---

## 📡 API ENDPOINTS

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login, returns JWT token |
| POST | `/auth/register` | Register new user |
| GET | `/auth/me` | Get current user profile |

### Leads
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/leads` | List leads (with pagination, filters) |
| GET | `/api/leads/{id}` | Get single lead |
| POST | `/api/leads` | Create new lead |
| PUT | `/api/leads/{id}` | Update lead |
| DELETE | `/api/leads/{id}` | Delete lead |
| POST | `/api/leads/import/csv` | Import leads from CSV |
| GET | `/api/leads/stats/summary` | Get lead statistics |

### Campaigns
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/campaigns` | List campaigns |
| GET | `/api/campaigns/{id}` | Get single campaign |
| POST | `/api/campaigns` | Create campaign |
| PUT | `/api/campaigns/{id}` | Update campaign |
| DELETE | `/api/campaigns/{id}` | Delete campaign |
| POST | `/api/campaigns/{id}/start` | Start campaign |
| POST | `/api/campaigns/{id}/pause` | Pause campaign |

### Emails
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/emails` | List emails |
| GET | `/api/emails/{id}` | Get single email |
| POST | `/api/emails/generate` | Generate email for lead |
| POST | `/api/emails/generate/bulk` | Generate emails for multiple leads |
| PUT | `/api/emails/{id}` | Update email content |
| POST | `/api/emails/{id}/approve` | Approve email for sending |
| POST | `/api/emails/{id}/send` | Send email |
| DELETE | `/api/emails/{id}` | Delete email |

---

## 🗄️ DATABASE SCHEMA

### Core Tables

```sql
-- Users
users (
  id, email, hashed_password, name, company,
  created_at, updated_at
)

-- Leads
leads (
  id, user_id, name, email, company, job_title,
  linkedin_url, phone, status, priority, intent_score,
  research_data (JSON), created_at, updated_at
)

-- Campaigns
campaigns (
  id, user_id, name, description, status,
  template, settings (JSON), created_at, updated_at
)

-- Emails
emails (
  id, user_id, lead_id, campaign_id,
  to_email, subject, body, status,
  sent_at, opened_at, clicked_at, replied_at,
  created_at, updated_at
)

-- Campaign_Leads (junction table)
campaign_leads (
  campaign_id, lead_id, added_at
)
```

### Status Enums

```python
# Lead Status
lead_status = ['new', 'researched', 'email_drafted', 'email_sent', 
               'replied', 'converted', 'unsubscribed']

# Campaign Status  
campaign_status = ['draft', 'active', 'paused', 'completed']

# Email Status
email_status = ['draft', 'approved', 'scheduled', 'sent', 
                'opened', 'clicked', 'replied', 'bounced']

# Priority
priority = ['high', 'medium', 'low']
```

---

## 🔐 AUTHENTICATION FLOW

```
1. User submits email/password to POST /auth/login
2. Backend validates credentials
3. Backend returns JWT token
4. Frontend stores token in localStorage
5. All subsequent requests include: Authorization: Bearer <token>
6. Backend middleware validates token on protected routes
7. On 401 response, frontend clears token and redirects to /login
```

---

## 📁 FILE NAMING CONVENTIONS

```
Backend:
- Routes: lowercase, plural (leads.py, campaigns.py)
- Models: lowercase (models.py)
- Services: lowercase_service.py (lead_service.py)

Frontend:
- Pages: PascalCase (Leads.jsx, Campaigns.jsx)
- Components: PascalCase (Layout.jsx, CSVImportModal.jsx)
- Utilities: camelCase (api.js, utils.js)
```

---

## 🚨 COMMON PITFALLS TO AVOID

### Backend
1. **CORS errors** - Make sure CORS middleware allows localhost:5173
2. **Database sessions** - Always use `Depends(get_db)`, don't create manually
3. **Async/await** - Don't forget `await` on async functions
4. **JWT expiry** - Tokens expire, handle refresh properly

### Frontend
1. **State updates** - React state is async, don't read immediately after set
2. **useEffect deps** - Include all dependencies to avoid stale closures
3. **API errors** - Always wrap API calls in try-catch
4. **Loading states** - Show loading indicators during API calls

---

## 🎯 CURRENT PROJECT STATUS

### Completed ✅
- [x] Week 1-2: Email Agent (Core AI)
- [x] Week 3-4: Web Dashboard
  - [x] Login page
  - [x] Dashboard page
  - [x] Leads page + CSV Import
  - [x] Campaigns page + Wizard
  - [x] Emails page + Preview/Edit

### In Progress 🔄
- [ ] Week 5: Email Infrastructure
  - [ ] SendGrid/Postmark integration
  - [ ] Open/click tracking
  - [ ] Reply detection
  - [ ] Email queue (Celery)

### Upcoming 📅
- [ ] Week 6: Email Analytics
- [ ] Week 7-8: 3-Layer Research Engine
- [ ] Week 9-10: Intent Scoring Engine
- [ ] Week 11-12: Legal Lead Sources (Apollo.io, etc.)
- [ ] Week 13-14: Advanced Analytics + RAG
- [ ] Week 15-16: Polish & Launch

---

## 🤖 INSTRUCTIONS FOR AI ASSISTANTS

When helping with this project:

1. **Read this file first** before making any changes
2. **Match existing code style** - look at similar files for patterns
3. **Use inline styles** - don't create separate CSS files
4. **Handle all states** - loading, empty, error, success
5. **Keep components focused** - one main purpose per component
6. **Add proper error handling** - try-catch on all API calls
7. **Test your suggestions** - make sure code runs without errors
8. **Explain changes** - help the developer learn

### When Creating New Features:
```
1. Check if similar feature exists (don't duplicate)
2. Follow existing patterns in the codebase
3. Add to appropriate folder (pages/, components/, routes/)
4. Update this AGENTS.md if adding new patterns
5. Consider both happy path and error cases
```

### When Debugging:
```
1. Check browser console for frontend errors
2. Check terminal for backend errors
3. Verify API endpoint exists and returns expected data
4. Check network tab for request/response details
5. Verify authentication token is being sent
```

---

## 📞 QUICK REFERENCE

### Start Development
```powershell
# Terminal 1 - Backend
cd "C:\Users\shail\OneDrive\Desktop\new Project"
.\.venv\Scripts\Activate.ps1
uvicorn api.main:app --reload --port 8000

# Terminal 2 - Frontend
cd "C:\Users\shail\OneDrive\Desktop\new Project\frontend"
npm run dev
```

### URLs
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Test Credentials
- Email: shailesh@test.com
- Password: password123

---

## 📝 CHANGELOG

| Date | Change |
|------|--------|
| 2026-01-08 | Created AGENTS.md |
| 2026-01-07 | Added Campaigns & Emails pages |
| 2026-01-06 | Added CSV Import to Leads |
| 2026-01-05 | Completed Dashboard & Leads pages |
| 2026-01-04 | Initial project setup |

---

*Last updated: January 8, 2026*
*Maintained by: Shailesh (Founder) + AI Assistants*
