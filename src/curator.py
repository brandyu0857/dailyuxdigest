import json
import logging
import os

import anthropic

from src.config import MODEL, NUM_ARTICLES, DATE_WINDOW_DAYS, SYSTEM_PROMPT, get_today_str, get_today_date, get_date_range

logger = logging.getLogger(__name__)


def curate_articles(sent_urls: list[str]) -> list[dict]:
    """Use Claude Haiku with web search to find and curate today's UX/Design/Product news."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    today = get_today_str()
    today_date = get_today_date()
    date_range = get_date_range()

    if sent_urls:
        dedup_instruction = (
            "IMPORTANT: Do NOT include any articles from these URLs, as they were already sent in recent days:\n"
            + "\n".join(f"- {url}" for url in sent_urls)
        )
    else:
        dedup_instruction = ""

    system = SYSTEM_PROMPT.format(
        num_articles=NUM_ARTICLES,
        today=today,
        date_window=DATE_WINDOW_DAYS,
        date_range=date_range,
        dedup_instruction=dedup_instruction,
    )

    user_message = (
        f"Search for the latest UX, Design, and Product news and articles.\n"
        f"Today is {today} ({today_date}). Look for articles from the last {DATE_WINDOW_DAYS} days ({date_range}).\n\n"
        f"Perform at least 5 separate web searches using these queries:\n"
        f"1. \"UX design news April 2026\"\n"
        f"2. \"Figma news\" OR \"design tools update\"\n"
        f"3. \"product design\" OR \"design system\" news\"\n"
        f"4. \"AI design tools\" OR \"AI UX\" latest\n"
        f"5. \"web design\" OR \"CSS\" OR \"front-end\" news this week\n\n"
        f"I need {NUM_ARTICLES} articles. Keep searching until you have enough.\n"
        f"Return ONLY a JSON array — no other text."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 10}],
        messages=[{"role": "user", "content": user_message}],
    )

    # Extract text content from the response (skip tool use/result blocks)
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text

    if not text_content.strip():
        raise RuntimeError("Claude returned no text content.")

    logger.info("Raw response (first 500 chars): %s", text_content[:500])

    cleaned = text_content.strip()

    # Remove markdown code blocks if present
    if "```" in cleaned:
        start = cleaned.find("```")
        end = cleaned.rfind("```")
        if start != end:
            inner = cleaned[start:end + 3]
            inner = inner.split("\n", 1)[1] if "\n" in inner else inner[3:]
            inner = inner.rsplit("```", 1)[0]
            cleaned = inner.strip()

    # Try to find JSON array in the text if direct parse fails
    try:
        articles = json.loads(cleaned)
    except json.JSONDecodeError:
        bracket_start = cleaned.find("[")
        bracket_end = cleaned.rfind("]")
        if bracket_start != -1 and bracket_end != -1 and bracket_end > bracket_start:
            json_str = cleaned[bracket_start:bracket_end + 1]
            articles = json.loads(json_str)
        else:
            logger.error("Could not find JSON array in response: %s", cleaned[:500])
            raise

    if not isinstance(articles, list):
        raise RuntimeError(f"Expected a JSON array, got: {type(articles)}")

    if len(articles) == 0:
        logger.warning("No articles met the date and topic criteria.")
        return []

    logger.info("Curated %d articles.", len(articles))
    for a in articles:
        logger.info("  - %s (%s)", a.get("title", "?"), a.get("source", "?"))

    return articles
