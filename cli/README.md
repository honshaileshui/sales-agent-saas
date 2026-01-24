# 🚀 SalesAgent CLI

> **Command-line interface for SalesAgent AI - Manage leads, campaigns, and emails from your terminal!**

## ⚡ Quick Install

```powershell
# Navigate to CLI folder
cd "C:\Users\shail\OneDrive\Desktop\new Project\cli"

# Install in development mode
pip install -e .

# Verify installation
salesagent --help
```

## 🔐 First Time Setup

```powershell
# Login to your account
salesagent config login --email shailesh@test.com --password password123

# Verify connection
salesagent stats
```

## 📋 Commands Reference

### Leads

```powershell
# List all leads
salesagent leads list

# List with filters
salesagent leads list --status new
salesagent leads list --limit 10

# Add a new lead
salesagent leads add --name "John Doe" --email "john@techcorp.com" --company "TechCorp"
salesagent leads add --name "Jane" --email "jane@startup.io" --company "StartupIO" --title "CTO" --priority high

# Import from CSV
salesagent leads import contacts.csv

# View lead details
salesagent leads view 5

# Delete a lead
salesagent leads delete 5
salesagent leads delete 5 --force  # Skip confirmation
```

### Campaigns

```powershell
# List all campaigns
salesagent campaigns list
salesagent campaigns list --status active

# Create a campaign
salesagent campaigns create "Q1 SaaS Outreach"
salesagent campaigns create "Tech Founders" --description "Targeting tech founders" --template friendly

# Start/Pause campaigns
salesagent campaigns start 1
salesagent campaigns pause 1

# Delete a campaign
salesagent campaigns delete 1
```

### Emails

```powershell
# List all emails
salesagent emails list
salesagent emails list --status draft

# Generate email for a lead
salesagent emails generate --lead 5
salesagent emails generate --lead 5 --template friendly

# View email content
salesagent emails view 1

# Approve and send
salesagent emails approve 1
salesagent emails send 1
```

### Stats

```powershell
# View dashboard overview
salesagent stats
```

### Config

```powershell
# Show current config
salesagent config show

# Login
salesagent config login
salesagent config login --email your@email.com --password yourpass

# Logout
salesagent config logout

# Set API URL (if not localhost)
salesagent config set-url http://your-server.com:8000
```

## 🎨 Output Examples

### Leads List
```
══════════════════════════════════════════════════
  📋 LEADS
══════════════════════════════════════════════════

ID | Name                      | Email                          | Company              | Status       | Priority
---|---------------------------|--------------------------------|----------------------|--------------|----------
1  | John Doe                  | john@techcorp.com              | TechCorp             | new          | high
2  | Jane Smith                | jane@startup.io                | StartupIO            | researched   | medium
3  | Bob Wilson                | bob@acme.com                   | Acme Inc             | email_sent   | low

Total: 3 leads
```

### Stats Dashboard
```
══════════════════════════════════════════════════
  📊 SALESAGENT DASHBOARD
══════════════════════════════════════════════════

LEADS
  Total:         25
  New:           10
  Researched:    8
  Email Drafted: 5
  Email Sent:    2

CAMPAIGNS
  Total:         3
  Active:        1

EMAILS
  Total:         15
  Drafts:        8
  Sent:          7

──────────────────────────────────────────────────
  Dashboard: http://localhost:5173
  API Docs:  http://localhost:8000/docs
```

## 🛠️ Troubleshooting

### "Cannot connect to API"
Make sure the backend is running:
```powershell
cd "C:\Users\shail\OneDrive\Desktop\new Project"
.\.venv\Scripts\Activate.ps1
uvicorn api.main:app --reload --port 8000
```

### "Authentication required"
Login first:
```powershell
salesagent config login
```

### Colors not showing
Install colorama:
```powershell
pip install colorama
```

## 📁 Config Location

Your CLI configuration is stored at:
- Windows: `C:\Users\<username>\.salesagent\config.json`
- Mac/Linux: `~/.salesagent/config.json`

## 🔄 Update CLI

```powershell
cd "C:\Users\shail\OneDrive\Desktop\new Project\cli"
pip install -e . --upgrade
```

## 💡 Pro Tips

1. **Quick workflow:**
   ```powershell
   salesagent leads import new_contacts.csv && salesagent leads list
   ```

2. **Batch operations:**
   ```powershell
   # Generate emails for multiple leads
   for ($i=1; $i -le 5; $i++) { salesagent emails generate --lead $i }
   ```

3. **Alias setup (PowerShell profile):**
   ```powershell
   Set-Alias sa salesagent
   # Then use: sa leads list
   ```

---

Made with ❤️ for SalesAgent AI
