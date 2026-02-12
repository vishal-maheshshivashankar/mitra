#!/bin/bash
# ============================================================
# Export all N8N workflows to backup directory
# ============================================================
set -e

N8N_URL="${N8N_URL:-http://localhost:5678}"
BACKUP_DIR="$(cd "$(dirname "$0")/../n8n/backup" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "╔══════════════════════════════════════════════════╗"
echo "║     MITRA - Workflow Backup                      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

read -p "Enter N8N API Key: " API_KEY

if [ -z "$API_KEY" ]; then
    echo "Error: API key is required for backup"
    exit 1
fi

# Fetch all workflows
echo "Fetching workflows from N8N..."
WORKFLOWS=$(curl -sf "${N8N_URL}/api/v1/workflows" \
    -H "X-N8N-API-KEY: ${API_KEY}" 2>&1)

if [ $? -ne 0 ]; then
    echo "Error: Could not fetch workflows from N8N"
    exit 1
fi

# Create timestamped backup directory
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"
mkdir -p "$BACKUP_PATH"

# Extract and save each workflow
COUNT=$(echo "$WORKFLOWS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
workflows = data.get('data', data) if isinstance(data, dict) else data
for wf in workflows:
    wf_id = wf.get('id', 'unknown')
    wf_name = wf.get('name', 'unnamed').replace(' ', '_').replace('/', '_')
    filename = f'{wf_name}_{wf_id}.json'
    with open('${BACKUP_PATH}/' + filename, 'w') as f:
        json.dump(wf, f, indent=2)
print(len(workflows))
" 2>/dev/null || echo "0")

echo "  Backed up $COUNT workflows to: $BACKUP_PATH"
echo ""
echo "Backup files:"
ls -la "$BACKUP_PATH"/*.json 2>/dev/null || echo "  No files found"
