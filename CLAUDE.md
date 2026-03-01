# Mitra - Project Context

## What Is This
Calorie and water intake logger via Telegram + N8N + Gemini Vision.

**Two repos:**
- `mitra/` — N8N workflow definitions + config (this repo)
- `n8n/` (`/Users/vishalm/projects/n8n`) — Docker infrastructure

---

## Tech Stack
- **Orchestration:** N8N v2.7.4 (Docker, managed in `n8n/` repo)
- **AI Model:** Gemini 2.5 Flash (food photo analysis via Vision API)
- **Database:** PostgreSQL 16 (N8N data), Health Bridge JSON files (water data)
- **Health Bridge:** FastAPI + Pydantic (Python 3.12) — lives in `n8n/health-bridge/`
- **Data Store:** Google Sheets (2 sheets: Meals, Health)
- **Interface:** Telegram Bot

---

## Project Structure (mitra/ — this repo)
```
mitra/
├── workflows/
│   ├── 00-router.json              # Telegram router → calorie or water
│   ├── 07-calorie-agent.json       # Food photo → Gemini Vision → Sheets Meals
│   └── cron-water-reminders.json   # Hourly 8AM-10PM water check → Telegram alert
├── config/
│   └── health-goals.json           # Daily targets: 2000 cal, 8 glasses
├── CLAUDE.md                        # This file
└── README.md
```

## Infrastructure (n8n/ — sibling repo)
```
n8n/
├── docker-compose.yml       # 3 services: n8n, postgres, health-bridge
├── .env.example             # Template with all required vars
├── Makefile                 # up, down, import, webhook, etc.
└── health-bridge/           # FastAPI water/health data API
```

---

## Workflow Flow

```
Telegram photo  → 00-router → 07-calorie-agent → Gemini Vision → Sheets (Meals)
Telegram "water"→ 00-router → Health Bridge POST /health/water/add
Cron hourly     → cron-water-reminders → Health Bridge GET /health/water → Telegram alert
```

---

## Health Bridge Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Healthcheck (no auth) |
| GET | `/health/water` | Get today's water glasses |
| POST | `/health/water/add?glasses=1` | Log water intake |

Auth: `X-API-Key` header (value = `HEALTH_BRIDGE_API_KEY` env var in n8n/.env)

---

## Google Sheets Schema

| Sheet | Key Columns | Written By |
|-------|-------------|-----------|
| Meals | meal_id, date, time, meal_type, food_items, calories, protein_g, carbs_g, fat_g, sugar_g, fiber_g, image_url | 07-calorie-agent |
| Health | date, time, water_glasses | cron-water-reminders |

---

## N8N Workflow Notes
- All env vars (`$env.HEALTH_BRIDGE_URL`, `$env.TELEGRAM_CHAT_ID`, etc.) are set in `n8n/.env`
- `callerPolicy: "workflowsFromSameOwner"` required on all workflows (prevents N8N startup errors)
- After importing, update `CALORIE_WORKFLOW_ID` placeholder in `00-router.json` with the actual ID
- N8N CLI import needs array wrapping: `echo '[' > /tmp/wf.json && cat file.json >> /tmp/wf.json && echo ']'`

---

## Key Commands (run from n8n/)
```bash
make up        # Start services
make down      # Stop services
make import    # Import workflows from ../mitra/workflows/
make webhook   # Register Telegram webhook
make status    # Health check
```
