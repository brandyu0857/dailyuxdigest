import json
import logging
import os

import anthropic

from src.config import MODEL, NUM_ARTICLES, SYSTEM_PROMPT, get_today_str, get_yesterday_str, get_today_date, get_yesterday_date

logger = logging.getLogger(__name__)


def curate_articles(sent_urls: list[str]) -> list[dict]:
    """Use Claude Haiku with web search to find and curate today's UX/Design/Product news."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    today = get_today_str()
    yesterday = get_yesterday_str()
    today_date = get_today_date()
    yesterday_date = get_yesterday_date()

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
        yesterday=yesterday,
        today_date=today_date,
        yesterday_date=yesterday_date,
        dedup_instruction=dedup_instruction,
    )

    user_message = (
        f"Search for UX, Design, and Product news articles published on {today_date} or {yesterday_date} ONLY.\n"
        f"Today is {today}. Yesterday was {yesterday}.\n\n"
        f"Search for:\n"
        f"- UX design news from {today_date}\n"
        f"- Product design updates from {today_date}\n"
        f"- Figma, design systems, UX research news from {yesterday_date} or {today_date}\n\n"
        f"Verify every article's publish date. Reject anything older than {yesterday_date}.\n"
        f"Return the top {NUM_ARTICLES} on-topic articles as JSON. If fewer qualify, return fewer."
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
