# Mitra AI Chatbot - Project Context

## What Is This
AI-powered personal assistant on N8N workflows + Telegram bot, deployed locally on Mac Mini via Docker. 10 feature areas, 17 N8N workflows, FastAPI health bridge for Apple Watch data.

**Owner:** vishal-maheshshivashankar | **Repo:** https://github.com/vishal-maheshshivashankar/mitra

---

## Tech Stack
- **Orchestration:** N8N v2.7.4 (Docker)
- **AI Model:** Gemini 2.5 Flash (primary), OpenAI (optional fallback)
- **Database:** PostgreSQL 16 (N8N data), Redis 7 (chat memory)
- **Health Bridge:** FastAPI + Pydantic (Python 3.12)
- **Data Store:** Google Sheets (8 sheets for all app data)
- **Interface:** Telegram Bot
- **APIs:** Gmail (x2), Google Calendar, Google Drive, Google Sheets

---

## Project Structure
```
mitra/
├── docker-compose.yml          # 5 services: n8n, postgres, redis, health-bridge, backup
├── .env                        # Secrets (gitignored). Template: .env.example
├── Makefile                    # 17 targets (setup, up, down, import, backup, validate, etc.)
├── CLAUDE.md                   # This file - project context
├── README.md                   # Full documentation with Mermaid diagrams + screenshots
│
├── workflows/                  # 17 N8N workflow JSONs
│   ├── 00-router-agent.json    # Main Telegram router → AI Tools Agent → 10 sub-workflows
│   ├── 01-email-agent.json     # Gmail x2 → Merge → Gemini classifier
│   ├── 02-calendar-agent.json  # LangChain Tools Agent + Google Calendar
│   ├── 03-document-agent.json  # Gmail/Drive search → auto-organize to Drive folders
│   ├── 04-budget-agent.json    # Sheets read → Gemini analysis (8 categories, 90K INR)
│   ├── 05-finance-agent.json   # Transaction analysis from Sheets
│   ├── 06-health-agent.json    # HTTP → Health Bridge API → Gemini summary
│   ├── 07-calorie-agent.json   # Telegram photo → Gemini Vision → parse macros → Sheets
│   ├── 08-todo-agent.json      # CRUD via Sheets, intent parsing (add/complete/list)
│   ├── 09-fitness-agent.json   # Workouts + vitals from Health Bridge
│   ├── 10-motivation-agent.json# Reads all sheets → personalized motivation
│   ├── cron-email-monitor.json # Every 15 min - malicious email detection
│   ├── cron-finance-scraper.json # Every 30 min - extract transactions from emails
│   ├── cron-budget-alerts.json # Daily 9 PM - budget status report
│   ├── cron-health-alerts.json # Hourly water + 15-min HR monitoring
│   ├── cron-todo-reminders.json# 8 AM tasks + 9 PM recap
│   └── cron-motivation.json    # 6:30 AM daily + Sun 8 PM weekly review
│
├── health-bridge/
│   ├── app.py                  # FastAPI: 8 endpoints, API key auth, Pydantic validation
│   ├── Dockerfile              # Python 3.12-slim, non-root user, healthcheck
│   ├── requirements.txt        # fastapi==0.115.6, uvicorn==0.34.0, pydantic==2.10.4
│   └── .dockerignore
│
├── config/
│   ├── budget-config.json      # 8 categories, thresholds (80%/100%), aliases
│   ├── email-rules.json        # 2 Gmail accounts, phishing patterns, priority rules
│   ├── document-rules.json     # 7 doc categories with Drive folder patterns
│   └── health-goals.json       # Daily targets, fitness goals, recovery metrics
│
├── scripts/
│   ├── setup.sh                # First-time setup wizard (set -euo pipefail)
│   ├── setup-google-oauth.py   # OAuth token generator for both Gmail accounts
│   ├── setup-sheets.py         # Creates "Mitra Dashboard" spreadsheet with 8 sheets
│   ├── import-workflows.sh     # Import workflows via N8N API (or manual fallback)
│   └── backup-workflows.sh     # Export workflows from N8N
│
├── credentials/                # API keys (gitignored, .gitkeep only)
├── docs/                       # 5 N8N workflow screenshots (PNG)
└── backups/                    # DB dumps (gitignored)
```

---

## Docker Services

| Service | Image | Port | Network | Resources |
|---------|-------|------|---------|-----------|
| n8n | n8nio/n8n:2.7.4 | 127.0.0.1:5678 | mitra-network + mitra-internal | 2 CPU / 2GB |
| postgres | postgres:16-alpine | internal only | mitra-internal | 1 CPU / 1GB |
| redis | redis:7-alpine | internal only | mitra-internal | 0.5 CPU / 512MB |
| health-bridge | custom (Python 3.12) | 0.0.0.0:8085 | mitra-network | 0.5 CPU / 512MB |
| backup | postgres:16-alpine | none | mitra-internal | on-demand (profiles: backup) |

**Key env vars:** `N8N_SECURE_COOKIE=false` (needed for local HTTP access)

---

## Health Bridge API

**Auth:** `X-API-Key` header on all endpoints except `/health`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Healthcheck (no auth) |
| POST | `/health/data` | Receive metrics/workouts from iPhone |
| GET | `/health/latest` | Latest metrics + today summary |
| GET | `/health/heart-rate` | HR stats (current, resting, HRV, min/max/avg) |
| GET | `/health/water` | Water intake vs 8-glass target |
| GET | `/health/workouts` | Recent workouts (default 7 days) |
| GET | `/health/summary` | Comprehensive daily summary |
| GET | `/health/range?start=&end=` | Date range query (max 90 days) |
| POST | `/health/water/add?glasses=1` | Manual water logging |

**Validation:** heart_rate (20-300), blood_oxygen (50-100%), steps (0-200K), duration (0-1440min)
**Storage:** JSON files at `/app/data/metrics_YYYY-MM-DD.json`, `workouts_YYYY-MM-DD.json`

---

## Google Sheets Schema ("Mitra Dashboard")

| Sheet | Key Columns | Used By |
|-------|-------------|---------|
| Transactions | txn_id, date, amount, merchant, category, type, source | Budget, Finance agents + cron |
| Budgets | category, monthly_limit, alert_threshold | Budget agent + cron |
| Meals | meal_id, date, food_items, calories, protein_g, carbs_g, fat_g, sugar_g | Calorie agent |
| Todos | todo_id, task, priority, status, due_date, completed_at | Todo agent + cron |
| Health | date, heart_rate, resting_hr, hrv, steps, water_glasses, sleep_hours | Health cron |
| Workouts | workout_id, type, duration_min, distance_km, calories, avg_hr | Fitness agent |
| Email_Log | email_id, account, sender, subject, category, is_malicious | Email cron |
| Weekly_Summary | week_start, total_spend, calories_avg, steps_avg, ai_summary | Motivation agent |

---

## N8N Workflow Patterns

**Router (00):** `Telegram Trigger → Switch (text/photo/doc) → AI Tools Agent (Gemini) → Sub-workflows → Response`
**Agents (01-10):** `Execute Workflow Trigger → Fetch data → Gemini AI → Format response`
**Crons:** `Schedule Trigger → Fetch data → JS calculations → Conditional → Telegram alert`

**Gemini temperatures:** 0.2 (doc classification) → 0.3-0.4 (analysis) → 0.7 (conversation)
**Memory:** Redis-backed Window Buffer (last 20 messages)

---

## Production Hardening (Applied)

- Non-root users in all containers
- N8N bound to localhost only (127.0.0.1:5678)
- PostgreSQL/Redis on internal-only Docker network
- API key auth on Health Bridge endpoints
- CORS restricted to localhost
- Request size limit (1MB), Pydantic input validation
- Resource limits + log rotation (50MB/5 files)
- Swagger/ReDoc disabled, diagnostics off
- .env chmod 600

---

## Budget Categories (INR/month)

| Category | Limit | Category | Limit |
|----------|-------|----------|-------|
| Loan | 40,000 | Stocks | 5,000 |
| Savings | 10,000 | Home | 5,000 |
| Insurances | 10,000 | Bills | 10,000 |
| MF SIP | 5,000 | Other | 5,000 |
| **Total** | **90,000** | | |

---

## Known Gaps / Future Work

1. **N8N workflow error handling** - No error handler nodes or retry logic in any of the 17 workflows
2. **Router workflow IDs** - Sub-workflow tool references use placeholder IDs, need updating after import
3. **Gemini rate limiting** - Not handled; concurrent requests could fail
4. **Health data cleanup** - No archival/pruning of daily JSON files (disk grows unbounded)
5. **Finance dedup** - Relies on exact (date, merchant, amount) match; slight variations create duplicates
6. **N8N version** - Updated to 2.7.4

---

## Key Commands

```bash
make up              # Start all services
make down            # Stop services
make restart         # Restart services
make logs            # N8N logs
make import          # Import workflows (needs API key or manual)
make backup          # Full backup (workflows + DB)
make validate        # Check .env, Docker, credentials
make status          # Service health check
docker compose down && docker compose up -d  # Full restart (apply config changes)
```

## Workflow Import (CLI method)
```bash
# Workflows need array wrapping for n8n CLI:
for f in $(docker exec mitra-n8n ls /workflows/); do
  docker exec mitra-n8n sh -c "echo '[' > /tmp/wf.json && cat /workflows/$f >> /tmp/wf.json && echo ']' >> /tmp/wf.json && n8n import:workflow --input=/tmp/wf.json"
done
```

---

## Git History
| Commit | Description |
|--------|-------------|
| `6cb51e2` | Initial commit: full system with production hardening |
| `bc392b4` | Add Mermaid architecture + network diagrams to README |
| `fb78e23` | Add N8N workflow screenshots to README |
