import json
import logging
import os

import anthropic

from src.config import MODEL, NUM_ARTICLES, SYSTEM_PROMPT, get_today_str

logger = logging.getLogger(__name__)


def curate_articles(sent_urls: list[str]) -> list[dict]:
    """Use Claude Haiku with web search to find and curate today's UX/Design/Product news."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    today = get_today_str()

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
        dedup_instruction=dedup_instruction,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[
            {
                "role": "user",
                "content": f"Find and curate today's top {NUM_ARTICLES} UX, Design, and Product news articles. Today is {today}.",
            }
        ],
    )

    # Extract the text content from the response (skip tool use/result blocks)
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text

    if not text_content.strip():
        raise RuntimeError("Claude returned no text content. Response may have been truncated.")

    # Parse JSON from the response
    # Handle cases where JSON might be wrapped in markdown code blocks
    cleaned = text_content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]  # remove first ```json line
        cleaned = cleaned.rsplit("```", 1)[0]  # remove trailing ```
    cleaned = cleaned.strip()

    articles = json.loads(cleaned)

    if not isinstance(articles, list) or len(articles) == 0:
        raise RuntimeError(f"Expected a non-empty JSON array, got: {type(articles)}")

    logger.info("Curated %d articles.", len(articles))
    for a in articles:
        logger.info("  - %s (%s)", a.get("title", "?"), a.get("source", "?"))

    return articles
