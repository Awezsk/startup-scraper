"""
dashboard.py — Generates a standalone dashboard.html from articles.json.
Run manually:  python dashboard.py
Also called automatically by scraper.py after each scrape.
"""

import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from processor import load_and_process, resolve_all_urls

log = logging.getLogger(__name__)
IST = timezone(timedelta(hours=5, minutes=30))
DASHBOARD_FILE = "dashboard.html"

# ── HTML template (inline — no external files needed) ──────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>India Startup & Grants Digest — {date_str}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg:        #0b0b18;
    --surface:   #13132a;
    --card:      #1a1a35;
    --card-hover:#20203f;
    --border:    #2a2a50;
    --purple:    #7c5cf4;
    --purple-lt: #a78bfa;
    --green:     #10b981;
    --green-lt:  #34d399;
    --blue:      #3b82f6;
    --text:      #e2e2f8;
    --muted:     #8888bb;
    --tag-bg:    rgba(124,92,244,0.15);
    --tag-gr:    rgba(16,185,129,0.15);
  }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
  }}

  /* ── Header ── */
  .header {{
    background: linear-gradient(135deg, #1e0a5e 0%, #0d2b6b 100%);
    border-bottom: 1px solid var(--border);
    padding: 40px 24px 32px;
    text-align: center;
  }}
  .header-icon {{ font-size: 48px; margin-bottom: 12px; }}
  .header h1 {{ font-size: 28px; font-weight: 800; letter-spacing: -0.5px; color: #fff; }}
  .header .sub {{
    margin-top: 8px;
    color: rgba(255,255,255,0.6);
    font-size: 14px;
  }}

  /* ── Stats Bar ── */
  .stats {{
    display: flex;
    justify-content: center;
    gap: 24px;
    padding: 20px 24px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }}
  .stat {{
    text-align: center;
    min-width: 100px;
  }}
  .stat-num {{ font-size: 32px; font-weight: 800; color: var(--purple-lt); }}
  .stat-num.green {{ color: var(--green-lt); }}
  .stat-num.blue {{ color: #60a5fa; }}
  .stat-label {{
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
  }}

  /* ── Controls ── */
  .controls {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 24px;
    max-width: 960px;
    margin: 0 auto;
    flex-wrap: wrap;
  }}
  .search-wrap {{
    flex: 1;
    min-width: 200px;
    position: relative;
  }}
  .search-wrap input {{
    width: 100%;
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 10px;
    padding: 10px 16px 10px 40px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
  }}
  .search-wrap input:focus {{ border-color: var(--purple); }}
  .search-icon {{
    position: absolute;
    left: 14px; top: 50%;
    transform: translateY(-50%);
    color: var(--muted);
    pointer-events: none;
  }}
  .filter-btns {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .filter-btn {{
    padding: 8px 18px;
    border-radius: 20px;
    border: 1px solid var(--border);
    background: var(--card);
    color: var(--muted);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .filter-btn:hover {{ background: var(--card-hover); color: var(--text); }}
  .filter-btn.active-all {{ background: var(--blue); border-color: var(--blue); color: #fff; }}
  .filter-btn.active-startups {{ background: var(--purple); border-color: var(--purple); color: #fff; }}
  .filter-btn.active-grants {{ background: var(--green); border-color: var(--green); color: #fff; }}

  /* ── Grid ── */
  .grid {{
    max-width: 960px;
    margin: 0 auto;
    padding: 0 24px 48px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(440px, 1fr));
    gap: 16px;
  }}

  /* ── Card ── */
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    transition: background 0.2s, transform 0.2s, border-color 0.2s;
    text-decoration: none;
    color: inherit;
    cursor: pointer;
    border-left: 3px solid var(--purple);
  }}
  .card.grants-card {{ border-left-color: var(--green); }}
  .card:hover {{
    background: var(--card-hover);
    transform: translateY(-2px);
    border-color: var(--purple-lt);
  }}
  .card.grants-card:hover {{ border-color: var(--green-lt); }}

  .card-badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 3px 10px;
    border-radius: 20px;
    align-self: flex-start;
    background: var(--tag-bg);
    color: var(--purple-lt);
  }}
  .card.grants-card .card-badge {{
    background: var(--tag-gr);
    color: var(--green-lt);
  }}

  .card-title {{
    font-size: 15px;
    font-weight: 600;
    line-height: 1.45;
    color: var(--text);
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}

  .card-meta {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    color: var(--muted);
    flex-wrap: wrap;
  }}
  .card-meta .source {{
    background: rgba(255,255,255,0.06);
    padding: 2px 8px;
    border-radius: 6px;
  }}

  .card-summary {{
    font-size: 13px;
    color: var(--muted);
    line-height: 1.55;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}

  .keywords {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .kw {{
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 20px;
    background: var(--tag-bg);
    color: var(--purple-lt);
    font-weight: 500;
  }}
  .grants-card .kw {{ background: var(--tag-gr); color: var(--green-lt); }}

  .read-btn {{
    align-self: flex-start;
    margin-top: 4px;
    font-size: 12px;
    font-weight: 600;
    color: var(--purple-lt);
    display: flex;
    align-items: center;
    gap: 4px;
  }}
  .grants-card .read-btn {{ color: var(--green-lt); }}

  /* ── Empty state ── */
  .empty {{
    grid-column: 1 / -1;
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
  }}
  .empty-icon {{ font-size: 48px; margin-bottom: 16px; }}

  /* ── Footer ── */
  .footer {{
    text-align: center;
    padding: 24px;
    color: var(--muted);
    font-size: 12px;
    border-top: 1px solid var(--border);
    max-width: 960px;
    margin: 0 auto;
  }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

  @media (max-width: 600px) {{
    .grid {{ grid-template-columns: 1fr; }}
    .header h1 {{ font-size: 22px; }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-icon">🚀</div>
  <h1>India Startup &amp; Grants Digest</h1>
  <p class="sub">{date_str} &nbsp;·&nbsp; Last 24 hours &nbsp;·&nbsp; Generated at {generated_at} IST</p>
</div>

<div class="stats">
  <div class="stat">
    <div class="stat-num blue" id="total-count">{total}</div>
    <div class="stat-label">Total Articles</div>
  </div>
  <div class="stat">
    <div class="stat-num" id="startup-count">{startup_count}</div>
    <div class="stat-label">Startup &amp; Funding</div>
  </div>
  <div class="stat">
    <div class="stat-num green" id="grants-count">{grants_count}</div>
    <div class="stat-label">Grants &amp; Schemes</div>
  </div>
</div>

<div class="controls">
  <div class="search-wrap">
    <span class="search-icon">🔍</span>
    <input type="text" id="search-input" placeholder="Search articles, sources, keywords…" oninput="filterArticles()">
  </div>
  <div class="filter-btns">
    <button class="filter-btn active-all" id="btn-all"      onclick="setFilter('all')">All</button>
    <button class="filter-btn"            id="btn-startups" onclick="setFilter('startups')">🚀 Startups</button>
    <button class="filter-btn"            id="btn-grants"   onclick="setFilter('grants')">🏛️ Grants</button>
  </div>
</div>

<div class="grid" id="articles-grid"></div>

<div class="footer">
  🤖 Auto-generated by India Startup Digest Bot &nbsp;·&nbsp;
  Sources: YourStory · Inc42 · ET Startups · Google News · PIB · Startup India Portal
</div>

<script>
const ARTICLES = {articles_json};

let activeFilter = 'all';

function setFilter(f) {{
  activeFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => {{
    b.className = 'filter-btn';
  }});
  const map = {{ all: 'active-all', startups: 'active-startups', grants: 'active-grants' }};
  document.getElementById('btn-' + f).classList.add(map[f]);
  filterArticles();
}}

function filterArticles() {{
  const query = document.getElementById('search-input').value.toLowerCase();
  const grid  = document.getElementById('articles-grid');
  grid.innerHTML = '';

  const filtered = ARTICLES.filter(a => {{
    const catOk = activeFilter === 'all' || a.category === activeFilter;
    const searchOk = !query ||
      a.title.toLowerCase().includes(query) ||
      (a.source || '').toLowerCase().includes(query) ||
      (a.summary || '').toLowerCase().includes(query) ||
      (a.keywords || []).some(k => k.toLowerCase().includes(query));
    return catOk && searchOk;
  }});

  if (filtered.length === 0) {{
    grid.innerHTML = `<div class="empty"><div class="empty-icon">📭</div><p>No articles match your search.</p></div>`;
    return;
  }}

  filtered.forEach(a => {{
    const isGrant  = a.category === 'grants';
    const badge    = isGrant ? '🏛️ Grants' : '🚀 Startup';
    const kwHtml   = (a.keywords || []).map(k => `<span class="kw">#${{k}}</span>`).join('');
    const date     = a.published_at ? a.published_at.substring(0, 10) : '';
    const summary  = a.summary ? `<p class="card-summary">${{a.summary}}</p>` : '';

    const card = document.createElement('a');
    card.href        = a.url;
    card.target      = '_blank';
    card.rel         = 'noopener noreferrer';
    card.className   = 'card' + (isGrant ? ' grants-card' : '');
    card.innerHTML   = `
      <span class="card-badge">${{badge}}</span>
      <p class="card-title">${{a.title}}</p>
      <div class="card-meta">
        <span class="source">${{a.source || ''}}</span>
        ${{date ? `<span>📅 ${{date}}</span>` : ''}}
      </div>
      ${{summary}}
      ${{kwHtml ? `<div class="keywords">${{kwHtml}}</div>` : ''}}
      <span class="read-btn">Read Article →</span>
    `;
    grid.appendChild(card);
  }});
}}

filterArticles();
</script>
</body>
</html>"""


def generate_dashboard(articles: list[dict] | None = None) -> str:
    """Generate dashboard.html from articles. Returns path to file."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if articles is None:
        # Load and process from file
        startups, grants = load_and_process()
        articles = startups + grants
    
    now_ist   = datetime.now(IST)
    startups  = [a for a in articles if a.get("category") == "startups"]
    grants    = [a for a in articles if a.get("category") == "grants"]

    html = HTML_TEMPLATE.format(
        date_str      = now_ist.strftime("%A, %d %B %Y"),
        generated_at  = now_ist.strftime("%I:%M %p"),
        total         = len(articles),
        startup_count = len(startups),
        grants_count  = len(grants),
        articles_json = json.dumps(articles, ensure_ascii=False, indent=2),
    )

    out_path = Path(__file__).parent / DASHBOARD_FILE
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    log.info(f"Dashboard saved -> {out_path}")
    return str(out_path)


if __name__ == "__main__":
    path = generate_dashboard()
    print(f"\nDashboard ready: {path}")
    # Only open browser locally, not in GitHub Actions / CI
    import os
    if not os.getenv("CI") and not os.getenv("GITHUB_ACTIONS"):
        import webbrowser
        webbrowser.open(f"file:///{path}")
