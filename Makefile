.PHONY: help setup up down restart logs status import backup backup-db clean health-logs

# ─── Default ─────────────────────────────────────────────────
help: ## Show this help message
	@echo "╔══════════════════════════════════════════════════╗"
	@echo "║          MITRA AI CHATBOT - Commands             ║"
	@echo "╚══════════════════════════════════════════════════╝"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ─── Setup ───────────────────────────────────────────────────
setup: ## First-time setup (copy env, generate keys, build)
	@echo "==> Running first-time setup..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		ENCRYPTION_KEY=$$(openssl rand -hex 32) && \
		POSTGRES_PASS=$$(openssl rand -hex 16) && \
		HEALTH_KEY=$$(openssl rand -hex 16) && \
		sed -i '' "s|CHANGE_ME_generate_with_openssl_rand_hex_32|$$ENCRYPTION_KEY|" .env && \
		sed -i '' "s|CHANGE_ME_secure_postgres_password|$$POSTGRES_PASS|" .env && \
		sed -i '' "s|CHANGE_ME_health_bridge_key|$$HEALTH_KEY|" .env && \
		chmod 600 .env && \
		echo "==> .env created with generated secrets (chmod 600)"; \
		echo "==> IMPORTANT: Edit .env to add your API keys and tokens"; \
	else \
		echo "==> .env already exists, skipping"; \
	fi
	@mkdir -p backups
	@echo "==> Building Docker images..."
	docker compose build
	@echo ""
	@echo "==> Setup complete! Next steps:"
	@echo "  1. Edit .env with your API keys (Telegram, Google, Gemini)"
	@echo "  2. Place Google credentials in ./credentials/"
	@echo "  3. Run 'make up' to start services"
	@echo "  4. Run 'make import' to import N8N workflows"

# ─── Docker Operations ──────────────────────────────────────
up: ## Start all services
	docker compose up -d
	@echo ""
	@echo "==> Services starting..."
	@echo "  N8N UI:         http://localhost:5678"
	@echo "  Health Bridge:  http://localhost:8085"
	@echo ""
	@echo "  Run 'make status' to check health"

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## View N8N logs (follow mode)
	docker compose logs -f n8n

logs-all: ## View all service logs
	docker compose logs -f

health-logs: ## View Health Bridge logs
	docker compose logs -f health-bridge

status: ## Check service health status
	@echo "==> Service Status:"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# ─── Workflow Management ─────────────────────────────────────
import: ## Import all workflow JSONs to N8N via API
	@echo "==> Importing workflows to N8N..."
	@bash scripts/import-workflows.sh

backup: ## Export all N8N workflows + database backup
	@echo "==> Backing up N8N workflows..."
	@bash scripts/backup-workflows.sh
	@echo "==> Backing up PostgreSQL database..."
	@mkdir -p backups
	docker compose run --rm backup
	@echo "==> Backup complete. Files in ./backups/"

backup-db: ## Database-only backup (PostgreSQL)
	@mkdir -p backups
	docker compose run --rm backup
	@echo "==> Database backup saved to ./backups/"

# ─── Google Setup ────────────────────────────────────────────
setup-google: ## Run Google OAuth setup (interactive)
	python3 scripts/setup-google-oauth.py

setup-sheets: ## Initialize Google Sheets with schema
	python3 scripts/setup-sheets.py

# ─── Maintenance ─────────────────────────────────────────────
clean: ## Remove all Docker volumes (DESTRUCTIVE!)
	@echo "WARNING: This will delete all N8N data, workflows, and credentials!"
	@read -p "Are you sure? (yes/no) " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v; \
		echo "==> All volumes removed"; \
	else \
		echo "==> Cancelled"; \
	fi

update: ## Pull latest N8N image and restart
	docker compose pull n8n
	docker compose up -d n8n
	@echo "==> N8N updated and restarted"

shell-n8n: ## Open shell in N8N container
	docker compose exec n8n /bin/sh

shell-db: ## Open psql shell in PostgreSQL
	docker compose exec postgres psql -U $${POSTGRES_USER:-n8n} -d $${POSTGRES_DB:-mitra_n8n}

redis-cli: ## Open Redis CLI
	docker compose exec redis redis-cli

# ─── Validation ──────────────────────────────────────────────
validate: ## Validate environment and credentials
	@echo "==> Validating configuration..."
	@test -f .env && echo "  ✓ .env exists" || echo "  ✗ .env missing (run: make setup)"
	@test -f credentials/google-service-account.json && echo "  ✓ Google service account found" || echo "  ✗ Google service account missing"
	@test -f credentials/gmail-credentials.json && echo "  ✓ Gmail credentials found" || echo "  ✗ Gmail credentials missing"
	@grep -q "YOUR_" .env 2>/dev/null && echo "  ✗ .env has unfilled placeholders" || echo "  ✓ .env has no placeholders"
	@echo "==> Docker services:"
	@docker compose ps --format "  {{.Name}}: {{.Status}}" 2>/dev/null || echo "  (not running)"
