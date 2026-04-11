import json
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.config import EST

logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sent_articles.json")
RETENTION_DAYS = 7


def load_sent_urls() -> list[str]:
    """Load previously sent article URLs from the dedup file."""
    try:
        with open(DATA_FILE, "r") as f:
            entries = json.load(f)
        return [entry["url"] for entry in entries]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        logger.info("No dedup history found, starting fresh.")
        return []


def save_sent_articles(new_urls: list[str]) -> None:
    """Append new article URLs and purge entries older than RETENTION_DAYS."""
    today = datetime.now(EST).strftime("%Y-%m-%d")

    # Load existing entries
    try:
        with open(DATA_FILE, "r") as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []

    # Add new entries
    for url in new_urls:
        entries.append({"url": url, "date": today})

    # Purge old entries
    cutoff = (datetime.now(EST) - timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d")
    entries = [e for e in entries if e.get("date", "2000-01-01") >= cutoff]

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(entries, f, indent=2)

    logger.info("Saved %d new URLs, %d total in dedup history.", len(new_urls), len(entries))
