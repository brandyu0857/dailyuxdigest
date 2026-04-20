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
5. Estimate the reading time in minutes based on the article's likely length and depth (e.g. short blog post = 2-3 min, long essay = 8-12 min).
6. Ensure variety — don't pick multiple articles from the same source if possible.
Return ONLY a JSON array:
[
  {{
    "title": "Article Title",
    "url": "https://...",
    "source": "Source Name",
    "description": "Your 2-3 sentence summary.",
    "read_time": "5 min"
  }}
]"""


HIGHLIGHTS_PROMPT = """You are the editor of "Daily UX Digest". Given today's curated articles, identify 3 common themes or trends across ALL the articles.

Write exactly 3 short bullet points, each one a key theme shared by multiple articles. Be specific — reference actual topics, not generic statements.

Format:
• Theme one
• Theme two
• Theme three

Return ONLY the 3 bullet points, nothing else."""


FEATURED_PROMPT = """Given these curated articles for today's UX/Design/Product newsletter, pick the ONE most noteworthy article to feature.

Consider:
- Major announcements or product launches
- High-authority sources (Figma, Nielsen Norman Group, Google Design, Adobe)
- Broad relevance to UX/Design/Product professionals
- Timeliness and significance

Return ONLY the index number (0-based) of the featured article. Just the number, nothing else."""


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

    # Second call: pick the featured article
    articles = _pick_featured(client, articles)

    return articles


def generate_highlights(articles: list[dict]) -> str:
    """Third cheap call to generate a trends summary for the newsletter header."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    article_summary = "\n".join(
        f"- \"{a['title']}\" ({a.get('source', '?')}): {a.get('description', '')}"
        for a in articles
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=200,
            system=HIGHLIGHTS_PROMPT,
            messages=[{"role": "user", "content": article_summary}],
        )
        highlight = response.content[0].text.strip().strip('"')
        logger.info("Highlight: %s", highlight)
        return highlight
    except Exception as e:
        logger.warning("Failed to generate highlight: %s", e)
        return "Here's what's happening in design and product today."


def _pick_featured(client: anthropic.Anthropic, articles: list[dict]) -> list[dict]:
    """Second cheap call to pick the most noteworthy article."""
    if len(articles) <= 1:
        if articles:
            articles[0]["featured"] = True
        return articles

    article_summary = "\n".join(
        f"{i}. \"{a['title']}\" — {a['source']}"
        for i, a in enumerate(articles)
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=10,
            system=FEATURED_PROMPT,
            messages=[{"role": "user", "content": article_summary}],
        )

        idx_text = response.content[0].text.strip()
        idx = int(idx_text)

        if 0 <= idx < len(articles):
            # Move featured article to first position
            featured = articles.pop(idx)
            featured["featured"] = True
            articles = [featured] + articles
            logger.info("Featured: %s (%s)", featured["title"], featured["source"])
        else:
            articles[0]["featured"] = True
    except Exception as e:
        logger.warning("Failed to pick featured, defaulting to first: %s", e)
        articles[0]["featured"] = True

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
