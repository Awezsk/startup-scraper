"""
scraper.py — Multi-source India startup & grants news scraper.
Uses feedparser for RSS + Playwright for JS-rendered pages.
"""

import asyncio
import io
import sys
# Force UTF-8 output on Windows so emoji/symbols don't crash logging
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import feedparser
import json
import logging
import re
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

from config import (
    RSS_SOURCES, PLAYWRIGHT_SOURCES, GNEWS_PLAYWRIGHT_QUERIES,
    INDIA_TERMS, TOPIC_TERMS, GRANT_TERMS, OUTPUT_FILE,
)

# ── Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────

def clean_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text).strip()


def parse_entry_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def within_24h(dt: datetime | None) -> bool:
    if dt is None:
        return True  # include articles with unknown publish time
    return (datetime.now(timezone.utc) - dt) <= timedelta(hours=24)


def is_relevant(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    has_india = any(t in text for t in INDIA_TERMS)
    has_topic = any(t in text for t in TOPIC_TERMS)
    return has_india and has_topic


def categorize(title: str, summary: str = "") -> str:
    text = (title + " " + summary).lower()
    return "grants" if any(t in text for t in GRANT_TERMS) else "startups"


def make_article(title, url, source, summary="", published=None) -> dict:
    return {
        "title": title.strip(),
        "url": url,
        "source": source,
        "summary": clean_html(summary)[:350],
        "published_at": published.isoformat() if published else None,
        "keywords": [],
        "category": categorize(title, summary),
    }


# ── Layer 1: RSS Feeds ─────────────────────────────────────────────

def scrape_rss_sources() -> list[dict]:
    articles = []
    for name, url in RSS_SOURCES.items():
        log.info(f"RSS -> {name}")
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            count = 0
            for entry in feed.entries:
                title   = clean_html(getattr(entry, "title", ""))
                summary = clean_html(getattr(entry, "summary", "") or getattr(entry, "description", ""))
                link    = getattr(entry, "link", "")
                pub     = parse_entry_date(entry)

                if not title or not link:
                    continue
                if not within_24h(pub):
                    continue
                if not is_relevant(title, summary):
                    continue

                articles.append(make_article(title, link, name, summary, pub))
                count += 1

            log.info(f"   OK {count} articles")
        except Exception as e:
            log.warning(f"   FAILED: {e}")
    return articles


# ── Layer 2: Playwright (Google News + Startup India) ──────────────

async def _scrape_google_news(browser) -> list[dict]:
    articles = []
    for query in GNEWS_PLAYWRIGHT_QUERIES:
        page = await browser.new_page()
        try:
            url = f"https://news.google.com/search?q={quote(query)}&hl=en-IN&gl=IN&ceid=IN%3Aen"
            log.info(f"Playwright -> Google News: {query}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # Try multiple selector strategies for Google News cards
            cards = await page.query_selector_all("article")
            if not cards:
                cards = await page.query_selector_all("[data-n-tid]")

            for card in cards[:20]:
                try:
                    # Try multiple title selectors
                    title_el = await card.query_selector("h3, h4, a[target='_blank']")
                    if not title_el:
                        continue
                    title = (await title_el.inner_text()).strip()
                    if not title or len(title) < 10:
                        continue

                    # Get link — try anchor in h3/h4, then first anchor
                    link_el = await card.query_selector("h3 a, h4 a, a[href*='articles']")
                    href = (await link_el.get_attribute("href") or "") if link_el else ""
                    if href.startswith("./"):
                        href = "https://news.google.com/" + href[2:]
                    if not href.startswith("http"):
                        href = "https://news.google.com" + href

                    # Source name
                    src_el = await card.query_selector("time + span, .vr1PYe, [data-n-tid]")
                    source = (await src_el.inner_text()).strip() if src_el else "Google News"

                    # Published time
                    time_el = await card.query_selector("time")
                    pub = None
                    if time_el:
                        ta = await time_el.get_attribute("datetime")
                        if ta:
                            try:
                                pub = datetime.fromisoformat(ta.replace("Z", "+00:00"))
                            except Exception:
                                pass

                    if not within_24h(pub) or not is_relevant(title):
                        continue

                    articles.append(make_article(title, href, f"Google News ({source})", "", pub))
                except Exception:
                    continue

            log.info(f"   OK {len(articles)} articles collected from Google News so far")
        except Exception as e:
            log.warning(f"   Google News failed for query '{query}': {e}")
        finally:
            await page.close()
    return articles



async def _scrape_startup_india(browser) -> list[dict]:
    articles = []
    page = await browser.new_page()
    try:
        log.info("Playwright -> Startup India Portal")
        await page.goto(
            "https://www.startupindia.gov.in/content/sih/en/recent-initiatives.html",
            wait_until="domcontentloaded", timeout=30000,
        )
        await page.wait_for_timeout(2500)

        items = await page.query_selector_all(".news-card, .card, article, .initiative-card")
        for item in items[:15]:
            try:
                title_el = await item.query_selector("h2, h3, h4, .title, .card-title")
                title    = (await title_el.inner_text()).strip() if title_el else ""
                link_el  = await item.query_selector("a")
                href     = await link_el.get_attribute("href") if link_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.startupindia.gov.in" + href
                if title:
                    articles.append(make_article(title, href or "https://www.startupindia.gov.in",
                                                 "Startup India"))
            except Exception:
                continue
        log.info(f"   OK {len(articles)} articles from Startup India")
    except Exception as e:
        log.warning(f"   ✘ Startup India failed: {e}")
    finally:
        await page.close()
    return articles


async def _run_playwright() -> list[dict]:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log.warning("Playwright not installed — skipping browser scraping")
        return []

    articles = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            articles += await _scrape_google_news(browser)
            articles += await _scrape_startup_india(browser)
        finally:
            await browser.close()
    return articles


# ── Main Entry Point ───────────────────────────────────────────────

def run_scraper() -> list[dict]:
    log.info("=" * 55)
    log.info("  India Startup & Grants Scraper - Starting")
    log.info("=" * 55)

    # Layer 1: RSS
    rss = scrape_rss_sources()
    log.info(f"RSS total: {len(rss)} articles")

    # Layer 2: Playwright
    try:
        pw = asyncio.run(_run_playwright())
        log.info(f"Playwright total: {len(pw)} articles")
    except Exception as e:
        log.warning(f"Playwright stage failed: {e}")
        pw = []

    all_articles = rss + pw

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for a in all_articles:
        if a["url"] not in seen_urls:
            seen_urls.add(a["url"])
            unique.append(a)

    log.info(f"Total unique articles: {len(unique)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    log.info(f"Saved -> {OUTPUT_FILE}")

    # Auto-generate HTML dashboard
    try:
        from dashboard import generate_dashboard
        generate_dashboard(unique)
    except Exception as e:
        log.warning(f"Dashboard generation failed: {e}")

    log.info("=" * 55)
    return unique


if __name__ == "__main__":
    arts = run_scraper()
    print(f"\nDone - {len(arts)} articles scraped")
    for a in arts[:5]:
        print(f"  [{a['category'].upper():8}] {a['title'][:70]} ({a['source']})")
