import logging
import os
import sys

from dotenv import load_dotenv

from src.archive import save_to_archive
from src.config import get_email_subject, get_today_str
from src.curator import curate_articles
from src.dedup import load_sent_urls, save_sent_articles
from src.email_sender import send_email
from src.email_template import build_email
from src.feeds import fetch_articles
from src.sheets_reader import get_subscribers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    load_dotenv()

    logger.info("=== Daily UX Digest ===")

    # 1. Fetch articles from RSS feeds
    logger.info("Fetching articles from RSS feeds...")
    raw_articles = fetch_articles()
    if not raw_articles:
        logger.warning("No articles from RSS feeds. Skipping.")
        return

    # 2. Load dedup history
    sent_urls = load_sent_urls()
    logger.info("Loaded %d previously sent URLs for dedup.", len(sent_urls))

    # 3. Curate articles with Claude Haiku
    logger.info("Curating with Claude Haiku...")
    articles = curate_articles(raw_articles, sent_urls)
    if not articles:
        logger.warning("No articles curated. Skipping email send.")
        return

    # 4. Build HTML email
    date_str = get_today_str()
    html = build_email(articles, date_str)
    subject = get_email_subject(date_str)

    # 5. Get subscribers — use TEST_EMAIL if set, otherwise read from Google Sheets
    test_email = os.environ.get("TEST_EMAIL")
    if test_email:
        subscribers = [test_email]
        logger.info("Test mode: sending only to %s", test_email)
    else:
        subscribers = get_subscribers()
        if not subscribers:
            logger.warning("No subscribers found. Skipping email send.")
            return

    # 6. Send email
    logger.info("Sending email to %d subscribers...", len(subscribers))
    send_email(html, subject, subscribers)

    # 7. Update dedup history
    new_urls = [a["url"] for a in articles if "url" in a]
    save_sent_articles(new_urls)

    # 8. Save to archive for GitHub Pages
    save_to_archive(articles)

    logger.info("Done! Sent %d articles to %d subscribers.", len(articles), len(subscribers))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        sys.exit(1)
