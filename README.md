# Mitra

Personal Telegram bot for daily health tracking and AI-powered resume generation. Built on n8n with Claude AI, Gemini Vision, and Google Sheets.

## Commands

| Input | What happens |
|-------|-------------|
| Send food photo | Gemini Vision analyzes macros → saves to Sheets → replies with nutrition breakdown |
| `water` or `water 2` | Logs glasses to Health Bridge → shows daily progress toward 8-glass goal |
| `summary` or `today` | Daily report: total calories + water intake |
| `/resume <job description>` | Claude AI rewrites your resume for the JD → pdflatex compiles → sends PDF |
| `help` | Shows available commands |

Hourly cron (8AM–10PM) sends a water reminder if you're behind on 8 glasses.

---

## Architecture

```
Telegram message
    │
    ▼
00-daily-tracker.json
    ├── Photo       → Gemini Vision → parse macros → Sheets (Meals) → reply
    ├── water       → Health Bridge POST /health/water/add → reply with total
    ├── summary     → Sheets (Meals + Water) → daily report
    ├── /resume JD  → ai-resume-telegram.json (sub-workflow)
    │                   └── Claude Sonnet 4.6 → LaTeX → latex-compiler → PDF → send
    └── help        → command list

cron-water-reminders.json
    └── Hourly 8AM–10PM → Health Bridge GET /health/water → Telegram alert if behind
```

---

## Workflows

| File | Trigger | Description |
|------|---------|-------------|
| [00-daily-tracker.json](workflows/00-daily-tracker.json) | Telegram message | Main router: food photos, water logging, daily summary, resume requests |
| [ai-resume-telegram.json](workflows/ai-resume-telegram.json) | Called by daily tracker | Claude AI → ATS-optimised LaTeX resume → PDF via latex-compiler |
| [cron-water-reminders.json](workflows/cron-water-reminders.json) | Hourly cron (8AM–10PM) | Checks water intake, sends Telegram reminder if behind |

---

## Infrastructure

This repo contains only workflow definitions. The Docker infrastructure lives in the sibling repo:

| Repo | Purpose |
|------|---------|
| `mitra/` (this repo) | n8n workflow JSON files |
| [`n8n-health-stack`](https://github.com/vishal-maheshshivashankar/n8n-health-stack) | Docker Compose: n8n + PostgreSQL + Health Bridge + LaTeX Compiler |

---

## Google Sheets Schema

**Meals tab** — written by the food photo branch

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

**Water tab** — written by the water branch

| Column | Example |
|--------|---------|
| date | 2026-03-01 |
| time | 10:00:00 |
| glasses | 1.5 |

---

## Setup

### Prerequisites

- n8n-health-stack running (`make up` in the `n8n/` repo)
- Telegram bot created via [@BotFather](https://t.me/botfather)
- Google Cloud project with Sheets API enabled
- Gemini API key (food photo analysis)
- Anthropic API key (resume generation)

### Import workflows

```bash
cd ../n8n
make import     # imports from ../mitra/workflows/ and ../mitra-mom/workflows/
```

### n8n UI setup

1. Open http://localhost:5678
2. Create credentials:
   - **Telegram Bot API** (bot token)
   - **Google Sheets OAuth2** (client ID + secret + refresh token)
   - **HTTP Header Auth** for Health Bridge (`X-API-Key`)
3. Activate all three workflows
4. Register the Telegram webhook:
   ```bash
   make webhook
   ```

### Required env vars (in `n8n/.env`)

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
SPREADSHEET_ID=...
HEALTH_BRIDGE_API_KEY=...
```
