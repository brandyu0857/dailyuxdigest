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

    # Use multiple focused searches to get date-accurate results
    search_queries = [
        f"UX design news {today_date}",
        f"product design news {today_date}",
        f"Figma OR design system OR UX research news {yesterday_date} OR {today_date}",
    ]

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        tools=[{"type": "web_search_preview"}],
        input=(
            f"Perform these web searches to find today's UX/Design/Product news:\n"
            + "\n".join(f"- {q}" for q in search_queries)
            + f"\n\nFrom ALL search results, select only articles published on {today_date} or {yesterday_date}. "
            f"Check each article's publish date — if it says April 7 or earlier, EXCLUDE it. "
            f"Only articles from {yesterday} or {today} are acceptable. "
            f"Return the top {NUM_ARTICLES} on-topic articles as JSON. If fewer qualify, return fewer."
        ),
    )

    # Extract text from the response
    text_content = response.output_text

    if not text_content or not text_content.strip():
        raise RuntimeError("GPT returned no text content.")

    # Parse JSON from the response — GPT may wrap it in markdown or add text around it
    logger.info("Raw response (first 500 chars): %s", text_content[:500])

    cleaned = text_content.strip()

    # Remove markdown code blocks if present
    if "```" in cleaned:
        # Extract content between first ``` and last ```
        start = cleaned.find("```")
        end = cleaned.rfind("```")
        if start != end:
            inner = cleaned[start:end + 3]
            # Remove opening ```json or ```
            inner = inner.split("\n", 1)[1] if "\n" in inner else inner[3:]
            inner = inner.rsplit("```", 1)[0]
            cleaned = inner.strip()

    # Try to find JSON array in the text if direct parse fails
    try:
        articles = json.loads(cleaned)
    except json.JSONDecodeError:
        # Look for [ ... ] in the text
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
