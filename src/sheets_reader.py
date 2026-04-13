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
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not set")

    # Support both base64-encoded and raw JSON
    try:
        decoded = base64.b64decode(raw)
        creds_dict = json.loads(decoded)
    except Exception:
        try:
            creds_dict = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON or base64: {e}")

    return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)


def _is_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value.strip()))


def get_subscribers() -> list[str]:
    """Read subscriber email addresses from Google Sheets."""
    try:
        creds = _get_credentials()
    except Exception as e:
        logger.error("Failed to load Google service account credentials: %s", e)
        raise

    try:
        gc = gspread.authorize(creds)
        sheet_id = os.environ["GOOGLE_SHEET_ID"]
        sheet = gc.open_by_key(sheet_id).sheet1
    except gspread.exceptions.APIError as e:
        logger.error("Google Sheets API error (sheet_id=%s): %s", os.environ.get("GOOGLE_SHEET_ID", "?"), e)
        raise
    except Exception as e:
        logger.error("Failed to connect to Google Sheets: %s", e)
        raise

    try:
        all_values = sheet.get_all_values()
    except gspread.exceptions.APIError as e:
        logger.error("Failed to read data from Google Sheet: %s", e)
        raise
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
