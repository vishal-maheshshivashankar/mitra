#!/bin/bash
# ============================================================
# Import all N8N workflow JSON files via the N8N REST API
# ============================================================
set -e

N8N_URL="${N8N_URL:-http://localhost:5678}"
WORKFLOW_DIR="$(cd "$(dirname "$0")/../workflows" && pwd)"

echo "╔══════════════════════════════════════════════════╗"
echo "║     MITRA - Workflow Importer                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Wait for N8N to be ready
echo "Checking N8N availability at ${N8N_URL}..."
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -sf "${N8N_URL}/healthz" > /dev/null 2>&1; then
        echo "  N8N is ready!"
        break
    fi
    RETRY=$((RETRY + 1))
    echo "  Waiting for N8N... (attempt $RETRY/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo "Error: N8N is not available at ${N8N_URL}"
    echo "Make sure services are running: make up"
    exit 1
fi

# Get API key from N8N (or use owner setup)
echo ""
echo "To import workflows, you need an N8N API key."
echo "Generate one in N8N UI: Settings > API > Create API Key"
echo ""
read -p "Enter N8N API Key (or press Enter to use manual import): " API_KEY

if [ -z "$API_KEY" ]; then
    echo ""
    echo "Manual import mode:"
    echo "  1. Open ${N8N_URL} in your browser"
    echo "  2. For each workflow file in ${WORKFLOW_DIR}:"
    echo "     - Click '...' menu > Import from File"
    echo "     - Select the JSON file"
    echo "     - Save and activate the workflow"
    echo ""
    echo "Workflow files to import:"
    for f in "$WORKFLOW_DIR"/*.json; do
        [ -f "$f" ] && echo "  - $(basename "$f")"
    done
    exit 0
fi

# Import each workflow via API
echo ""
echo "Importing workflows..."
IMPORTED=0
FAILED=0

for workflow_file in "$WORKFLOW_DIR"/*.json; do
    [ -f "$workflow_file" ] || continue

    filename=$(basename "$workflow_file")
    echo -n "  Importing: $filename ... "

    RESPONSE=$(curl -sf -X POST "${N8N_URL}/api/v1/workflows" \
        -H "X-N8N-API-KEY: ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d @"$workflow_file" 2>&1)

    if [ $? -eq 0 ]; then
        WORKFLOW_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','?'))" 2>/dev/null || echo "?")
        echo "OK (ID: $WORKFLOW_ID)"
        IMPORTED=$((IMPORTED + 1))
    else
        echo "FAILED"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "Results: $IMPORTED imported, $FAILED failed"
echo ""
echo "Next steps:"
echo "  1. Open ${N8N_URL}"
echo "  2. Configure credentials for each workflow (Google, Telegram, Gemini)"
echo "  3. Activate the workflows you want to use"
echo "  4. Test with: send /start to your Telegram bot"
