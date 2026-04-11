import logging
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import feedparser

from src.config import EST, RSS_FEEDS, DATE_WINDOW_DAYS

logger = logging.getLogger(__name__)


def _parse_date(entry) -> datetime | None:
    """Extract and parse the publish date from a feed entry."""
    for field in ("published", "updated"):
        raw = entry.get(field)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                return dt.astimezone(EST)
            except Exception:
                pass
        # feedparser also provides parsed versions
        parsed = entry.get(f"{field}_parsed")
        if parsed:
            try:
                dt = datetime(*parsed[:6], tzinfo=ZoneInfo("UTC"))
                return dt.astimezone(EST)
            except Exception:
                pass
    return None


def fetch_articles() -> list[dict]:
    """Fetch recent articles from all RSS feeds."""
    cutoff = datetime.now(EST) - timedelta(days=DATE_WINDOW_DAYS)
    articles = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source = feed.feed.get("title", feed_url)

            for entry in feed.entries:
                pub_date = _parse_date(entry)

                # Skip articles older than cutoff
                if pub_date and pub_date < cutoff:
                    continue

                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                summary = entry.get("summary", "").strip()

                # Clean HTML tags from summary
                if "<" in summary:
                    import re
                    summary = re.sub(r"<[^>]+>", "", summary)
                summary = summary[:500]  # Truncate long summaries

                if title and url:
                    articles.append({
                        "title": title,
                        "url": url,
                        "source": source,
                        "summary": summary,
                        "date": pub_date.strftime("%Y-%m-%d") if pub_date else "unknown",
                    })

            logger.info("Fetched %d recent articles from %s", sum(1 for a in articles if a["source"] == source), source)

        except Exception as e:
            logger.warning("Failed to fetch %s: %s", feed_url, e)
            continue

    logger.info("Total: %d articles from %d feeds.", len(articles), len(RSS_FEEDS))
    return articles
