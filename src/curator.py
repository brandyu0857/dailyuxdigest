import json
import logging
import os

import anthropic

from src.config import MODEL, NUM_ARTICLES

logger = logging.getLogger(__name__)

CURATOR_PROMPT = """You are the editor of "Daily UX Digest", a daily newsletter for UX designers, product managers, and design leaders.

Below is a list of recent articles from UX, Design, and Product RSS feeds. Your job:

1. Select the {num_articles} most interesting, impactful, and diverse articles.
2. Prioritize: major product launches, tool updates, insightful essays, research findings, and practical guides.
3. Skip: job listings, sponsor posts, generic listicles, or low-quality content.
4. For each selected article, rewrite the description as a compelling 2-3 sentence summary that explains why it matters.
5. Ensure variety — don't pick multiple articles from the same source if possible.

Return ONLY a JSON array:
[
  {{
    "title": "Article Title",
    "url": "https://...",
    "source": "Source Name",
    "description": "Your 2-3 sentence summary."
  }}
]"""


def curate_articles(raw_articles: list[dict], sent_urls: list[str]) -> list[dict]:
    """Use Claude Haiku to select and summarize the best articles from RSS feeds."""
    # Filter out previously sent articles
    fresh = [a for a in raw_articles if a["url"] not in sent_urls]
    logger.info("After dedup: %d articles (filtered %d sent).", len(fresh), len(raw_articles) - len(fresh))

    if not fresh:
        logger.warning("No fresh articles after dedup.")
        return []

    # Format articles for Claude
    article_list = "\n\n".join(
        f"---\nTitle: {a['title']}\nURL: {a['url']}\nSource: {a['source']}\nDate: {a['date']}\nSummary: {a['summary']}"
        for a in fresh
    )

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=CURATOR_PROMPT.format(num_articles=NUM_ARTICLES),
        messages=[{
            "role": "user",
            "content": f"Here are {len(fresh)} recent articles. Select the best {NUM_ARTICLES} and return as JSON.\n\n{article_list}",
        }],
    )

    text = response.content[0].text
    logger.info("Curator response (first 300 chars): %s", text[:300])

    # Parse JSON
    articles = _extract_json(text)
    if not articles:
        logger.warning("Could not parse curator response as JSON.")
        return []

    logger.info("Curated %d articles.", len(articles))
    for a in articles:
        logger.info("  - %s (%s)", a.get("title", "?"), a.get("source", "?"))

    return articles


def _extract_json(text: str) -> list[dict] | None:
    """Try to extract a JSON array from text."""
    cleaned = text.strip()

    # Remove markdown code blocks
    if "```" in cleaned:
        start = cleaned.find("```")
        end = cleaned.rfind("```")
        if start != end:
            inner = cleaned[start:end + 3]
            inner = inner.split("\n", 1)[1] if "\n" in inner else inner[3:]
            inner = inner.rsplit("```", 1)[0]
            cleaned = inner.strip()

    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Find [ ... ] in text
    s = cleaned.find("[")
    e = cleaned.rfind("]")
    if s != -1 and e != -1 and e > s:
        try:
            result = json.loads(cleaned[s:e + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return None
