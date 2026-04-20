"""
processor.py — Keyword extraction and article enrichment.
Reads articles.json, resolves redirect URLs, extracts top keywords using YAKE.
"""

import json
import logging
from config import OUTPUT_FILE

log = logging.getLogger(__name__)


# ── URL Resolver ───────────────────────────────────────────────────

def resolve_url_playwright(url: str) -> str:
    """Use Playwright to follow Google News JS-redirect and get the real article URL."""
    if not url or 'news.google.com' not in url:
        return url
    try:
        import asyncio
        from playwright.async_api import async_playwright

        async def _get_final_url():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                try:
                    # Google News redirects to the actual article on navigation
                    resp = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(2000)
                    final = page.url
                    return final
                except Exception:
                    return url
                finally:
                    await browser.close()

        return asyncio.run(_get_final_url())
    except Exception:
        return url


def resolve_all_urls(articles: list[dict]) -> list[dict]:
    """Resolve Google News redirect URLs for all articles using Playwright (batched)."""
    google_articles = [a for a in articles if 'news.google.com' in a.get('url', '')]
    if not google_articles:
        log.info("No Google News URLs to resolve")
        return articles

    log.info(f"Resolving {len(google_articles)} Google News redirect URLs via Playwright...")
    try:
        import asyncio
        from playwright.async_api import async_playwright

        async def _resolve_batch():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                sem = asyncio.Semaphore(3)  # max 3 parallel pages

                async def _resolve_one(article):
                    async with sem:
                        page = await browser.new_page()
                        try:
                            await page.goto(article['url'], wait_until="domcontentloaded", timeout=15000)
                            await page.wait_for_timeout(1500)
                            final = page.url
                            if final != article['url'] and 'news.google.com' not in final:
                                log.info(f"  Resolved -> {final[:80]}")
                                article['url'] = final
                        except Exception:
                            pass
                        finally:
                            await page.close()

                await asyncio.gather(*[_resolve_one(a) for a in google_articles])
                await browser.close()

        asyncio.run(_resolve_batch())
    except Exception as e:
        log.warning(f"Batch URL resolution failed: {e}")

    log.info(f"URL resolution done for {len(articles)} articles")
    return articles


def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """Extract top keywords from text using YAKE."""
    if not text or len(text) < 20:
        return []
    try:
        import yake
        extractor = yake.KeywordExtractor(
            lan="en", n=2, dedupLim=0.8, top=top_n * 2, features=None
        )
        kws = extractor.extract_keywords(text)
        # Lower score = more relevant in YAKE
        kws_sorted = sorted(kws, key=lambda x: x[1])
        return [kw for kw, _score in kws_sorted[:top_n]]
    except Exception as e:
        log.warning(f"Keyword extraction failed: {e}")
        return []


def enrich_articles(articles: list[dict]) -> list[dict]:
    """Add keywords to each article."""
    for article in articles:
        text = article["title"] + " " + article.get("summary", "")
        article["keywords"] = extract_keywords(text)
    return articles


def split_by_category(articles: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split into startup and grants buckets."""
    startups = [a for a in articles if a.get("category") == "startups"]
    grants   = [a for a in articles if a.get("category") == "grants"]
    return startups, grants


def load_and_process() -> tuple[list[dict], list[dict]]:
    """Load articles.json, enrich with keywords, split by category."""
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)
    except FileNotFoundError:
        log.error(f"{OUTPUT_FILE} not found — run scraper.py first")
        return [], []
    except json.JSONDecodeError as e:
        log.error(f"Bad JSON in {OUTPUT_FILE}: {e}")
        return [], []

    log.info(f"Loaded {len(articles)} articles from {OUTPUT_FILE}")
    log.info("Resolving redirect URLs (Google News links)...")
    articles = resolve_all_urls(articles)
    articles = enrich_articles(articles)
    startups, grants = split_by_category(articles)
    log.info(f"Category split → Startups: {len(startups)} | Grants: {len(grants)}")
    return startups, grants


if __name__ == "__main__":
    s, g = load_and_process()
    print(f"\n🚀 Startups ({len(s)})")
    for a in s[:3]:
        print(f"  • {a['title'][:70]}")
        print(f"    Keywords: {', '.join(a['keywords'])}")
    print(f"\n🏛️  Grants ({len(g)})")
    for a in g[:3]:
        print(f"  • {a['title'][:70]}")
        print(f"    Keywords: {', '.join(a['keywords'])}")
