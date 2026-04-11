import base64
import json
import logging
import os
import re

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _get_credentials() -> Credentials:
    """Load Google service account credentials from environment."""
    raw = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

    # Support both base64-encoded and raw JSON
    try:
        decoded = base64.b64decode(raw)
        creds_dict = json.loads(decoded)
    except Exception:
        creds_dict = json.loads(raw)

    return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)


def _is_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value.strip()))


def get_subscribers() -> list[str]:
    """Read subscriber email addresses from Google Sheets."""
    creds = _get_credentials()
    gc = gspread.authorize(creds)

    sheet_id = os.environ["GOOGLE_SHEET_ID"]
    sheet = gc.open_by_key(sheet_id).sheet1

    # Get all values and find the email column automatically
    all_values = sheet.get_all_values()
    if not all_values:
        logger.warning("Google Sheet is empty.")
        return []

    # Find which column contains emails (check header row and first data row)
    header = all_values[0]
    email_col = None

    # First, check header names
    for i, h in enumerate(header):
        if "email" in h.lower():
            email_col = i
            break

    # If no header match, check first data row for email-like values
    if email_col is None and len(all_values) > 1:
        for i, val in enumerate(all_values[1]):
            if _is_email(val):
                email_col = i
                break

    if email_col is None:
        logger.error("Could not find an email column in the sheet.")
        return []

    # Extract emails from that column, skipping header
    emails = []
    for row in all_values[1:]:
        if email_col < len(row):
            val = row[email_col].strip()
            if _is_email(val):
                emails.append(val)

    logger.info("Found %d subscribers from Google Sheet.", len(emails))
    return emails
