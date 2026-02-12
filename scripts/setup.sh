#!/bin/bash
# ============================================================
# MITRA AI CHATBOT - First-Time Setup Script
# ============================================================
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║          MITRA AI CHATBOT - Setup                ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Step 1: Check prerequisites ────────────────────────────
echo -e "${CYAN}[1/7] Checking prerequisites...${NC}"

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}  ✗ $1 is not installed${NC}"
        echo -e "  Install: $2"
        return 1
    else
        echo -e "${GREEN}  ✓ $1 found${NC}"
        return 0
    fi
}

MISSING=0
check_command "docker" "https://docs.docker.com/desktop/install/mac-install/" || MISSING=1
check_command "docker" "Docker Compose is included with Docker Desktop" || MISSING=1
check_command "python3" "brew install python3" || MISSING=1
check_command "openssl" "Should be pre-installed on macOS" || MISSING=1

if [ "$MISSING" -eq 1 ]; then
    echo -e "\n${RED}Please install missing prerequisites and run again.${NC}"
    exit 1
fi

# Check Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}  ✗ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Docker is running${NC}"
echo ""

# ─── Step 2: Create .env file ───────────────────────────────
echo -e "${CYAN}[2/7] Setting up environment...${NC}"

cd "$PROJECT_DIR"

if [ ! -f .env ]; then
    cp .env.example .env

    # Generate secure random keys
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    POSTGRES_PASS=$(openssl rand -hex 16)
    HEALTH_KEY=$(openssl rand -hex 16)

    # Replace placeholder values (macOS sed syntax)
    sed -i '' "s/CHANGE_ME_generate_with_openssl_rand_hex_32/$ENCRYPTION_KEY/" .env
    sed -i '' "s/CHANGE_ME_secure_postgres_password/$POSTGRES_PASS/" .env
    sed -i '' "s/mitra-health-secret/$HEALTH_KEY/" .env

    echo -e "${GREEN}  ✓ .env created with generated secrets${NC}"
else
    echo -e "${YELLOW}  → .env already exists, skipping${NC}"
fi
echo ""

# ─── Step 3: Telegram Bot Setup ─────────────────────────────
echo -e "${CYAN}[3/7] Telegram Bot Setup${NC}"
echo -e "${YELLOW}  To create a Telegram bot:${NC}"
echo "  1. Open Telegram and search for @BotFather"
echo "  2. Send /newbot"
echo "  3. Choose a name: Mitra AI"
echo "  4. Choose a username: mitra_ai_bot (must end in 'bot')"
echo "  5. Copy the API token"
echo ""

read -p "  Enter your Telegram Bot Token (or press Enter to skip): " BOT_TOKEN
if [ -n "$BOT_TOKEN" ]; then
    sed -i '' "s/YOUR_TELEGRAM_BOT_TOKEN/$BOT_TOKEN/" .env
    echo -e "${GREEN}  ✓ Bot token saved${NC}"
fi

echo ""
echo -e "${YELLOW}  To get your Chat ID:${NC}"
echo "  1. Open Telegram and search for @userinfobot"
echo "  2. Send /start"
echo "  3. Copy your user ID number"
echo ""

read -p "  Enter your Telegram Chat ID (or press Enter to skip): " CHAT_ID
if [ -n "$CHAT_ID" ]; then
    sed -i '' "s/YOUR_TELEGRAM_CHAT_ID/$CHAT_ID/" .env
    echo -e "${GREEN}  ✓ Chat ID saved${NC}"
fi
echo ""

# ─── Step 4: Google Cloud Setup ──────────────────────────────
echo -e "${CYAN}[4/7] Google Cloud Setup${NC}"
echo -e "${YELLOW}  Follow these steps to set up Google APIs:${NC}"
echo ""
echo "  1. Go to https://console.cloud.google.com"
echo "  2. Create a new project named 'Mitra AI'"
echo "  3. Enable these APIs (search in API Library):"
echo "     - Gmail API"
echo "     - Google Drive API"
echo "     - Google Sheets API"
echo "     - Google Calendar API"
echo ""
echo "  4. Create OAuth 2.0 Client ID:"
echo "     - Go to APIs & Services > Credentials"
echo "     - Click '+ CREATE CREDENTIALS' > OAuth client ID"
echo "     - Application type: Desktop app"
echo "     - Name: Mitra AI"
echo "     - Download the JSON and save as:"
echo "       ${PROJECT_DIR}/credentials/gmail-credentials.json"
echo ""
echo "  5. Create Service Account:"
echo "     - Go to APIs & Services > Credentials"
echo "     - Click '+ CREATE CREDENTIALS' > Service account"
echo "     - Name: mitra-service"
echo "     - Role: Editor"
echo "     - Create key (JSON) and save as:"
echo "       ${PROJECT_DIR}/credentials/google-service-account.json"
echo ""

read -p "  Press Enter when credentials are in place (or type 'skip'): " GOOGLE_READY
echo ""

# ─── Step 5: Gemini API Key ─────────────────────────────────
echo -e "${CYAN}[5/7] Gemini AI Setup${NC}"
echo "  Get your API key from: https://aistudio.google.com/app/apikey"
echo ""

read -p "  Enter your Gemini API Key (or press Enter to skip): " GEMINI_KEY
if [ -n "$GEMINI_KEY" ]; then
    sed -i '' "s/YOUR_GEMINI_API_KEY/$GEMINI_KEY/" .env
    echo -e "${GREEN}  ✓ Gemini API key saved${NC}"
fi
echo ""

# ─── Step 6: Build Docker images ────────────────────────────
echo -e "${CYAN}[6/7] Building Docker images...${NC}"
docker compose build
echo -e "${GREEN}  ✓ Docker images built${NC}"
echo ""

# ─── Step 7: Install Python dependencies for setup scripts ──
echo -e "${CYAN}[7/7] Installing Python dependencies for setup scripts...${NC}"
pip3 install --quiet google-auth google-auth-oauthlib google-auth-httplib2 \
    google-api-python-client gspread 2>/dev/null || true
echo -e "${GREEN}  ✓ Python dependencies installed${NC}"
echo ""

# ─── Summary ────────────────────────────────────────────────
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║              Setup Complete!                      ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Review and update .env with any missing API keys"
echo "  2. Run: ${CYAN}make up${NC} to start all services"
echo "  3. Open: ${CYAN}http://localhost:5678${NC} for N8N UI"
echo "  4. Run: ${CYAN}python3 scripts/setup-google-oauth.py${NC} for Gmail OAuth"
echo "  5. Run: ${CYAN}python3 scripts/setup-sheets.py${NC} to create Google Sheets"
echo "  6. Run: ${CYAN}make import${NC} to import workflows into N8N"
echo "  7. Activate workflows in N8N UI"
echo "  8. Send /start to your Telegram bot!"
echo ""
echo -e "${YELLOW}For Health data:${NC}"
echo "  - Install 'Health Auto Export' app on iPhone"
echo "  - Configure REST API export to: http://<mac-mini-ip>:8085/health/data"
echo ""
