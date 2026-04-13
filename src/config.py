from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

EST = ZoneInfo("America/New_York")

MODEL = "claude-haiku-4-5-20251001"
NUM_ARTICLES = 5
DATE_WINDOW_DAYS = 2

RSS_FEEDS = [
    # UX & Design
    "https://www.smashingmagazine.com/feed/",
    "https://uxdesign.cc/feed",
    "https://www.nngroup.com/feed/rss/",
    "https://alistapart.com/main/feed/",
    "https://uxplanet.org/feed",
    "https://www.interaction-design.org/literature/articles/rss",
    "https://dribbble.com/stories.rss",
    "https://www.awwwards.com/blog/feed/",

    # Design Tools & Systems
    "https://www.figma.com/blog/feed/",
    "https://medium.com/sketch-app-sources/feed",
    "https://news.design.systems/issues.rss",

    # Product
    "https://www.svpg.com/feed/",
    "https://www.mindtheproduct.com/feed/",

    # CSS / Front-end Design
    "https://css-tricks.com/feed/",
    "https://web.dev/feed.xml",
    "https://blog.logrocket.com/feed/",

    # Accessibility
    "https://webaim.org/blog/feed/",

    # AI + Design
    "https://www.uxmatters.com/index.xml",
    "https://thegradient.pub/rss/",
    "https://design.google/feed",
    "https://blog.adobe.com/en/publish/feed.xml",
    "https://blog.prototypr.io/feed",
    "https://towardsdatascience.com/feed",
    "https://www.theverge.com/rss/design/index.xml",
]


def get_today_str() -> str:
    return datetime.now(EST).strftime("%A, %B %d, %Y")


def get_today_date() -> str:
    return datetime.now(EST).strftime("%Y-%m-%d")


def get_email_subject(date_str: str) -> str:
    return f"Daily Digest — Design, UX & Product — {date_str}"
