#!/usr/bin/env python3
"""
Google OAuth Setup - Generate refresh tokens for Gmail accounts.

Usage:
    python3 scripts/setup-google-oauth.py

Prerequisites:
    1. Download OAuth credentials JSON from Google Cloud Console
    2. Save as credentials/gmail-credentials.json
    3. Enable Gmail API, Drive API, Sheets API, Calendar API
"""

import json
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_DIR = os.path.join(PROJECT_DIR, "credentials")
CREDENTIALS_FILE = os.path.join(CREDENTIALS_DIR, "gmail-credentials.json")
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "gmail-token.json")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
]

ACCOUNTS = [
    "vishal.maheshshivashankar@gmail.com",
    "vishalre411@gmail.com",
]


def check_dependencies():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: F401

        return True
    except ImportError:
        print("Missing dependencies. Install with:")
        print(
            "  pip3 install google-auth google-auth-oauthlib"
            " google-auth-httplib2 google-api-python-client"
        )
        return False


def generate_token(account_email: str, account_num: int):
    from google_auth_oauthlib.flow import InstalledAppFlow

    print(f"\n{'=' * 50}")
    print(f"Generating token for: {account_email}")
    print(f"{'=' * 50}")
    print(f"A browser window will open. Sign in with: {account_email}")
    print("Grant all requested permissions.\n")

    input(f"Press Enter to start OAuth flow for {account_email}...")

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=3000 + account_num, access_type="offline", prompt="consent")

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
        "account": account_email,
    }

    token_file = os.path.join(CREDENTIALS_DIR, f"gmail-token-{account_num}.json")
    with open(token_file, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"\n  Token saved to: {token_file}")
    print(f"  Refresh token: {creds.refresh_token[:20]}...")
    print("\n  Add to .env:")
    print(f"  GMAIL_REFRESH_TOKEN_{account_num}={creds.refresh_token}")

    return creds.refresh_token


def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║     MITRA - Google OAuth Token Generator         ║")
    print("╚══════════════════════════════════════════════════╝")

    if not check_dependencies():
        sys.exit(1)

    if not os.path.exists(CREDENTIALS_FILE):
        print("\nError: OAuth credentials not found at:")
        print(f"  {CREDENTIALS_FILE}")
        print("\nDownload from Google Cloud Console:")
        print("  1. Go to https://console.cloud.google.com/apis/credentials")
        print("  2. Click on your OAuth 2.0 Client ID")
        print("  3. Click 'DOWNLOAD JSON'")
        print(f"  4. Save as: {CREDENTIALS_FILE}")
        sys.exit(1)

    tokens = {}
    for i, account in enumerate(ACCOUNTS, 1):
        try:
            token = generate_token(account, i)
            tokens[account] = token
        except Exception as e:
            print(f"\nError generating token for {account}: {e}")
            continue

    if tokens:
        print(f"\n{'=' * 50}")
        print("Summary - Add these to your .env file:")
        print(f"{'=' * 50}")
        for i, (account, token) in enumerate(tokens.items(), 1):
            print(f"# {account}")
            print(f"GMAIL_REFRESH_TOKEN_{i}={token}")
            print()

        # Also extract client_id and client_secret for .env
        with open(CREDENTIALS_FILE) as f:
            creds_data = json.load(f)
            installed = creds_data.get("installed", creds_data.get("web", {}))
            print(f"GMAIL_CLIENT_ID={installed.get('client_id', 'NOT_FOUND')}")
            print(f"GMAIL_CLIENT_SECRET={installed.get('client_secret', 'NOT_FOUND')}")

    print("\nDone! Next: run 'python3 scripts/setup-sheets.py'")


if __name__ == "__main__":
    main()
