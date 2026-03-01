# Mitra - Calorie & Water Logger

AI-powered daily calorie and water tracker via Telegram.

| Command | Action |
|---------|--------|
| Send food photo | Gemini Vision analyzes → saves to Sheets → shows macros |
| `water` or `water 2` | Logs glasses → saves to Sheets → shows daily progress |
| `summary` or `today` | Shows daily report: calories + water |

Hourly cron (8AM–10PM) sends a water reminder if you're behind on 8 glasses.

---

## Architecture

```
Telegram Bot
    │
    ▼
00-daily-tracker.json (single workflow)
    ├── Photo  → Gemini Vision → parse macros → Sheets (Meals) → reply
    ├── water  → log glasses  → Sheets (Water) → show today total
    └── summary→ read Meals + Water sheets → daily report

cron-water-reminders.json
    └── Hourly 8AM-10PM → read Sheets Water → alert if behind
```

## Repositories

| Repo | Purpose |
|------|---------|
| `mitra/` (this repo) | N8N workflow definitions |
| `n8n/` | Docker infrastructure (N8N + PostgreSQL + Health Bridge) |

## Workflows (2 total)

| File | Trigger | What it does |
|------|---------|-------------|
| [00-daily-tracker.json](workflows/00-daily-tracker.json) | Telegram message | Routes photo/water/summary to the right branch |
| [cron-water-reminders.json](workflows/cron-water-reminders.json) | Hourly 8AM–10PM | Checks Sheets Water tab, sends reminder if behind |

## Google Sheets Schema

**Meals tab** — written by daily tracker (photo branch)

| Column | Example |
|--------|---------|
| meal_id | meal_1234567890 |
| date | 2026-03-01 |
| time | 13:30:00 |
| meal_type | lunch |
| food_items | dal, rice, sabzi |
| calories | 520 |
| protein_g | 18 |
| carbs_g | 85 |
| fat_g | 12 |
| sugar_g | 4 |
| fiber_g | 6 |

**Water tab** — written by daily tracker (water branch)

| Column | Example |
|--------|---------|
| date | 2026-03-01 |
| time | 10:00:00 |
| glasses | 1.5 |

## Setup

```bash
cd ../n8n
make setup      # generates secrets, builds images
# edit .env — fill in API keys
make up         # start n8n + postgres
make import     # import workflows from mitra/workflows/
```

In N8N UI (http://localhost:5678):
1. Create credentials: **Telegram Bot API**, **Google Sheets OAuth2**
2. Set `SPREADSHEET_ID` env var in n8n/.env
3. Activate both workflows
4. `make webhook` to register Telegram webhook
