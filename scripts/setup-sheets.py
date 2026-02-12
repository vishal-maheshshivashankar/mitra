#!/usr/bin/env python3
"""
Google Sheets Setup - Create and initialize the Mitra Dashboard spreadsheet.

Usage:
    python3 scripts/setup-sheets.py [spreadsheet_id]

If no spreadsheet_id is provided, creates a new spreadsheet.
"""

import json
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(PROJECT_DIR, "credentials", "google-service-account.json")
BUDGET_CONFIG = os.path.join(PROJECT_DIR, "config", "budget-config.json")

SHEETS_SCHEMA = {
    "Transactions": [
        "txn_id", "date", "amount", "merchant", "category", "type",
        "source", "card_name", "description", "email_account",
        "raw_email_id", "created_at"
    ],
    "Budgets": [
        "category", "monthly_limit", "alert_threshold"
    ],
    "Meals": [
        "meal_id", "date", "time", "meal_type", "food_items",
        "calories", "protein_g", "carbs_g", "fat_g", "sugar_g",
        "fiber_g", "image_url"
    ],
    "Todos": [
        "todo_id", "date", "task", "priority", "status",
        "due_date", "completed_at", "category"
    ],
    "Health": [
        "date", "time", "heart_rate", "resting_hr", "hrv",
        "steps", "active_calories", "water_glasses", "sleep_hours",
        "blood_oxygen"
    ],
    "Workouts": [
        "workout_id", "date", "type", "duration_min", "distance_km",
        "calories", "avg_hr", "max_hr", "avg_pace", "notes"
    ],
    "Email_Log": [
        "email_id", "account", "date", "sender", "subject",
        "category", "priority", "is_malicious", "action_taken"
    ],
    "Weekly_Summary": [
        "week_start", "total_spend", "budget_status", "calories_avg",
        "steps_avg", "workouts_count", "todos_completed", "todos_total",
        "ai_summary"
    ],
}

USER_EMAIL = "vishal.maheshshivashankar@gmail.com"


def check_dependencies():
    try:
        import gspread  # noqa: F401
        from google.oauth2.service_account import Credentials  # noqa: F401
        return True
    except ImportError:
        print("Missing dependencies. Install with:")
        print("  pip3 install gspread google-auth")
        return False


def setup_spreadsheet(spreadsheet_id=None):
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)

    if spreadsheet_id:
        print(f"Opening existing spreadsheet: {spreadsheet_id}")
        spreadsheet = client.open_by_key(spreadsheet_id)
    else:
        print("Creating new spreadsheet: Mitra Dashboard")
        spreadsheet = client.create("Mitra Dashboard")
        spreadsheet.share(USER_EMAIL, perm_type="user", role="writer")
        print(f"  Shared with: {USER_EMAIL}")

    print(f"  Spreadsheet ID: {spreadsheet.id}")
    print(f"  URL: {spreadsheet.url}")

    # Create each sheet with headers
    existing_sheets = [ws.title for ws in spreadsheet.worksheets()]

    for sheet_name, headers in SHEETS_SCHEMA.items():
        if sheet_name in existing_sheets:
            print(f"  Sheet '{sheet_name}' already exists, updating headers...")
            worksheet = spreadsheet.worksheet(sheet_name)
        else:
            print(f"  Creating sheet: {sheet_name}")
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))

        # Set headers
        worksheet.update("A1", [headers])

        # Format header row (bold, blue background)
        worksheet.format("A1:{}1".format(chr(64 + len(headers))), {
            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER",
        })

        # Freeze header row
        worksheet.freeze(rows=1)

    # Remove default Sheet1 if it exists and we created new sheets
    if "Sheet1" in existing_sheets and len(existing_sheets) > 1:
        try:
            spreadsheet.del_worksheet(spreadsheet.worksheet("Sheet1"))
            print("  Removed default Sheet1")
        except Exception:
            pass

    # Populate budgets from config
    if os.path.exists(BUDGET_CONFIG):
        print("\n  Populating budget data from config...")
        with open(BUDGET_CONFIG) as f:
            config = json.load(f)

        budget_sheet = spreadsheet.worksheet("Budgets")
        budget_rows = []
        for category, amount in config["monthly_budget"].items():
            threshold = config["alert_thresholds"]["warning_percent"] / 100
            budget_rows.append([category, amount, threshold])

        if budget_rows:
            budget_sheet.update(f"A2:C{1 + len(budget_rows)}", budget_rows)
            print(f"  Added {len(budget_rows)} budget categories")

    return spreadsheet.id


def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║     MITRA - Google Sheets Setup                  ║")
    print("╚══════════════════════════════════════════════════╝")

    if not check_dependencies():
        sys.exit(1)

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"\nError: Service account credentials not found at:")
        print(f"  {CREDENTIALS_FILE}")
        print(f"\nCreate a service account in Google Cloud Console:")
        print(f"  1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts")
        print(f"  2. Create service account")
        print(f"  3. Create key (JSON)")
        print(f"  4. Save as: {CREDENTIALS_FILE}")
        sys.exit(1)

    spreadsheet_id = sys.argv[1] if len(sys.argv) > 1 else None

    sid = setup_spreadsheet(spreadsheet_id)

    print(f"\n{'='*50}")
    print("Add to your .env file:")
    print(f"{'='*50}")
    print(f"SPREADSHEET_ID={sid}")
    print(f"\nDone! Your Mitra Dashboard is ready.")


if __name__ == "__main__":
    main()
