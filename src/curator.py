import json
import logging
import os

from openai import OpenAI

from src.config import MODEL, NUM_ARTICLES, SYSTEM_PROMPT, get_today_str, get_yesterday_str, get_today_date, get_yesterday_date

logger = logging.getLogger(__name__)


def curate_articles(sent_urls: list[str]) -> list[dict]:
    """Use GPT-4o-mini with web search to find and curate today's UX/Design/Product news."""
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

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

    instructions = SYSTEM_PROMPT.format(
        num_articles=NUM_ARTICLES,
        today=today,
        yesterday=yesterday,
        today_date=today_date,
        yesterday_date=yesterday_date,
        dedup_instruction=dedup_instruction,
    )

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        tools=[{"type": "web_search_preview"}],
        input=f"Search for UX, Design, and Product news articles published on {today_date} or {yesterday_date} only. Today is {today}. Return the {NUM_ARTICLES} most relevant articles. Reject anything older or off-topic.",
    )

    # Extract text from the response
    text_content = response.output_text

    if not text_content or not text_content.strip():
        raise RuntimeError("GPT returned no text content.")

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
