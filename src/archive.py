import json
import logging
import os

from src.config import get_today_date

logger = logging.getLogger(__name__)

DOCS_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
INDEX_FILE = os.path.join(DOCS_DATA_DIR, "index.json")


def save_to_archive(articles: list[dict]) -> None:
    """Save today's curated articles to the docs/data/ archive for GitHub Pages."""
    today = get_today_date()
    os.makedirs(DOCS_DATA_DIR, exist_ok=True)

    # Save today's articles
    day_file = os.path.join(DOCS_DATA_DIR, f"{today}.json")
    with open(day_file, "w") as f:
        json.dump(articles, f, indent=2)

    # Update the index
    try:
        with open(INDEX_FILE, "r") as f:
            index = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        index = []

    if today not in index:
        index.append(today)
        index.sort(reverse=True)

    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)

    logger.info("Saved %d articles to archive for %s.", len(articles), today)
