import json
import logging
import os

import anthropic

from src.config import MODEL, NUM_ARTICLES, DATE_WINDOW_DAYS, SYSTEM_PROMPT, get_today_str, get_today_date, get_date_range

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> list[dict] | None:
    """Try to extract a JSON array from text. Returns None if not found."""
    cleaned = text.strip()

    # Remove markdown code blocks if present
    if "```" in cleaned:
        start = cleaned.find("```")
        end = cleaned.rfind("```")
        if start != end:
            inner = cleaned[start:end + 3]
            inner = inner.split("\n", 1)[1] if "\n" in inner else inner[3:]
            inner = inner.rsplit("```", 1)[0]
            cleaned = inner.strip()

    # Try direct parse
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try to find [ ... ] in the text
    bracket_start = cleaned.find("[")
    bracket_end = cleaned.rfind("]")
    if bracket_start != -1 and bracket_end != -1 and bracket_end > bracket_start:
        try:
            result = json.loads(cleaned[bracket_start:bracket_end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return None


def _convert_to_json(client: anthropic.Anthropic, raw_text: str) -> list[dict]:
    """Second cheap call: convert free-text article list to JSON."""
    logger.info("Converting free-text response to JSON with a second call...")

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": (
                "Convert the following article list into a JSON array. "
                "Extract the title, url, source name, and description for each article.\n\n"
                "Return ONLY a valid JSON array in this format:\n"
                '[{"title": "...", "url": "https://...", "source": "...", "description": "..."}]\n\n'
                f"Article list:\n{raw_text}"
            ),
        }],
    )

    text = response.content[0].text
    result = _extract_json(text)
    return result if result else []


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
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
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

    # Try to extract JSON from the response
    articles = _extract_json(text_content)

    # If no JSON found, Claude likely returned a text list — convert it with a second call
    if articles is None:
        logger.info("No JSON in web search response. Attempting conversion...")
        articles = _convert_to_json(client, text_content)

    if not articles:
        logger.warning("No articles found. Skipping today.")
        return []

    logger.info("Curated %d articles.", len(articles))
    for a in articles:
        logger.info("  - %s (%s)", a.get("title", "?"), a.get("source", "?"))

    return articles
