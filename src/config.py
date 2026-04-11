import os
from datetime import datetime
from zoneinfo import ZoneInfo

EST = ZoneInfo("America/New_York")

MODEL = "claude-haiku-4-5-20251001"
NUM_ARTICLES = 7

SYSTEM_PROMPT = """You are the editor of "Daily UX Digest", a daily newsletter for UX designers, product managers, and design leaders.

Your task:
1. Search the web for today's most notable news and articles about UX Design, Product Design, and Product Management.
2. Focus on: new tools, major product launches, design system updates, UX research findings, industry conferences, notable blog posts, and significant company announcements in the design/product space.
3. Select the {num_articles} most interesting and impactful articles.
4. For each article, write a compelling 2-3 sentence description that explains why it matters to the audience.

Date context: Today is {today}. Only include articles published today or yesterday.

{dedup_instruction}

Return your final selection as a JSON array with exactly this structure:
[
  {{
    "title": "Article Title",
    "url": "https://...",
    "source": "Source Name",
    "description": "2-3 sentence description."
  }}
]

Return ONLY the JSON array, no other text."""


def get_today_str() -> str:
    return datetime.now(EST).strftime("%A, %B %d, %Y")


def get_today_date() -> str:
    return datetime.now(EST).strftime("%Y-%m-%d")


def get_email_subject(date_str: str) -> str:
    return f"Daily Digest — Design, UX & Product — {date_str}"
