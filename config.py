"""config.py — Central configuration for the scraper."""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Email ──────────────────────────────────────────────────────────
SENDER_EMAIL        = os.getenv("SENDER_EMAIL", "")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")
RECIPIENT_EMAILS    = os.getenv("RECIPIENT_EMAILS", "")  # Comma-separated list
SMTP_HOST           = "smtp.gmail.com"
SMTP_PORT           = 587

# ── Schedule (IST, 24-hour) ────────────────────────────────────────
SCRAPE_HOUR   = 9   # 9:00 AM IST  → run scraper
SCRAPE_MINUTE = 0
EMAIL_HOUR    = 10  # 10:00 AM IST → send digest
EMAIL_MINUTE  = 0

# ── File Paths ─────────────────────────────────────────────────────
OUTPUT_FILE = "articles.json"
LOG_FILE    = "scraper.log"

# ── RSS Sources ────────────────────────────────────────────────────
RSS_SOURCES = {
    # ── Startup / Business Media ───────────────────────────────────
    "YourStory":
        "https://yourstory.com/feed",
    "Inc42":
        "https://inc42.com/feed/",
    "ET Startups":
        "https://economictimes.indiatimes.com/small-biz/startups/rssfeeds/17239718.cms",
    "Entrackr":
        "https://entrackr.com/feed/",
    "VCCircle":
        "https://www.vccircle.com/feed",
    "PIB India":
        "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
    "Business Standard":
        "https://www.business-standard.com/rss/companies-and-markets/startups-1008101.rss",
    "Livemint Startups":
        "https://www.livemint.com/rss/companies/start-ups",
    "Trak.in":
        "https://trak.in/feed/",
    "MediaNama":
        "https://www.medianama.com/feed/",
    "The Ken (Public Feed)":
        "https://the-ken.com/feed/",
    "CNBC TV18 Startups":
        "https://www.cnbctv18.com/common/rss/startup.xml",
    "Hindu BusinessLine Startups":
        "https://www.thehindubusinessline.com/news/variety/startup/feeder/default.rss",

    # ── New: Additional Startup & Business Media ───────────────────
    "VC Circle Deals":
        "https://www.vccircle.com/category/deals/feed",
    "Mint Tech":
        "https://www.livemint.com/rss/technology",
    "Financial Express Startups":
        "https://www.financialexpress.com/about/startups/feed/",
    "NDTV Profit Business":
        "https://www.ndtvprofit.com/rss/news",
    "AIM - Analytics India Magazine":
        "https://analyticsindiamag.com/feed/",
    "Inc42 Funding":
        "https://inc42.com/buzz/funding/feed/",
    "Outlook Business":
        "https://www.outlookbusiness.com/rss/rss.xml",
    "ET Tech":
        "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "Moneycontrol Startups":
        "https://www.moneycontrol.com/rss/business.xml",
    "Deccan Herald Business":
        "https://www.deccanherald.com/rss-feeds/business",

    # ── New: Grants, Government & Policy ──────────────────────────
    "PIB - Ministry of Commerce":
        "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
    "PIB - MSME":
        "https://pib.gov.in/RssMain.aspx?ModId=21&Lang=1&Regid=3",
    "MyScheme.gov.in":
        "https://www.myscheme.gov.in/rss/scheme.xml",
    "Startup India News":
        "https://www.startupindia.gov.in/content/sih/en/rss.xml",
    "SIDBI News":
        "https://www.sidbi.in/en/rss.xml",

    # ── Google News RSS — Startup Funding & Ecosystem ─────────────
    "GNews - Startup Funding":
        "https://news.google.com/rss/search?q=India+startup+funding&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - Grants & Schemes":
        "https://news.google.com/rss/search?q=India+startup+grants+government+scheme&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - DPIIT":
        "https://news.google.com/rss/search?q=DPIIT+startup+India&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - VC India":
        "https://news.google.com/rss/search?q=India+venture+capital+seed+funding&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - Incubators":
        "https://news.google.com/rss/search?q=India+incubator+accelerator+startup&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - New Grants India":
        "https://news.google.com/rss/search?q=India+startup+grant+application+deadline&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - State Startup Policies":
        "https://news.google.com/rss/search?q=State+Startup+Policy+India+incentives&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - MeitY SAMRIDH":
        "https://news.google.com/rss/search?q=MeitY+SAMRIDH+scheme+startups&hl=en-IN&gl=IN&ceid=IN:en",

    # ── New: Additional Google News Queries ────────────────────────
    "GNews - Atal Innovation Mission":
        "https://news.google.com/rss/search?q=Atal+Innovation+Mission+AIM+India&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - Startup India Recognition":
        "https://news.google.com/rss/search?q=Startup+India+DPIIT+recognition+certificate&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - MSME Schemes":
        "https://news.google.com/rss/search?q=MSME+scheme+India+2025+funding&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - PLI Scheme":
        "https://news.google.com/rss/search?q=PLI+scheme+India+startup&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - Mudra Loan":
        "https://news.google.com/rss/search?q=Mudra+loan+scheme+PMMY+India&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - Deep Tech Startups":
        "https://news.google.com/rss/search?q=India+deep+tech+startup+funding&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - Women Entrepreneurs":
        "https://news.google.com/rss/search?q=India+women+entrepreneur+grant+startup&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - Budget Startup":
        "https://news.google.com/rss/search?q=India+union+budget+startup+announcement&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - Angel Tax":
        "https://news.google.com/rss/search?q=angel+tax+India+startup+policy&hl=en-IN&gl=IN&ceid=IN:en",
    "GNews - Unicorn India":
        "https://news.google.com/rss/search?q=India+unicorn+startup+valuation+2025&hl=en-IN&gl=IN&ceid=IN:en",
}

# ── Playwright Sources (JS-rendered) ──────────────────────────────
PLAYWRIGHT_SOURCES = {
    "Startup India Portal":
        "https://www.startupindia.gov.in/content/sih/en/recent-initiatives.html",
    # ── New Playwright Sources ─────────────────────────────────────
    "Atal Innovation Mission":
        "https://aim.gov.in/news.php",
    "MeitY Startup Hub":
        "https://msh.gov.in/latest-news",
    "Invest India - Startups":
        "https://www.investindia.gov.in/startups",
    "SIDBI MSME Pulse":
        "https://www.sidbi.in/en/press-releases",
    "iCreate Gujarat":
        "https://www.icreate.org.in/news",
}

# ── Google News Playwright search queries ─────────────────────────
GNEWS_PLAYWRIGHT_QUERIES = [
    "India startup funding news today",
    "India startup grants government scheme today",
    "DPIIT Startup India announcement",
    # ── New Queries ────────────────────────────────────────────────
    "MSME scheme India new announcement",
    "India incubator accelerator program 2025",
    "PLI scheme new sector India",
    "Atal Innovation Mission new cohort",
    "MeitY startup scheme announcement",
    "India deeptech startup government support",
    "women entrepreneur grant India 2025",
]

# ── Relevance Filters ──────────────────────────────────────────────
INDIA_TERMS = [
    "india", "indian", "bengaluru", "bangalore", "mumbai", "delhi",
    "hyderabad", "pune", "chennai", "kolkata", "ahmedabad", "noida",
    "gurugram", "gurgaon", "dpiit", "startup india", "msme", "sidbi",
    # ── New ────────────────────────────────────────────────────────
    "jaipur", "indore", "bhopal", "lucknow", "kochi", "chandigarh",
    "bhubaneswar", "nagpur", "surat", "coimbatore", "vizag",
    "invest india", "make in india", "digital india",
]

TOPIC_TERMS = [
    "startup", "grant", "funding", "seed round", "series a", "series b",
    "series c", "pre-seed", "venture capital", "angel investor", "incubator",
    "accelerator", "unicorn", "ipo", "term sheet", "valuation",
    "government scheme", "pli scheme", "mudra", "subsidy",
    "atma nirbhar", "make in india", "atal innovation", "raise", "raised",
    "crore", "fintech", "edtech", "healthtech", "agritech", "deeptech",
    # ── New ────────────────────────────────────────────────────────
    "spacetech", "cleantech", "climatetech", "insurtech", "legaltech",
    "b2b saas", "d2c", "ecommerce", "logistics", "mobility",
    "angel tax", "esop", "convertible note", "safe note",
    "revenue-based financing", "debt funding", "ncd",
    "iit incubator", "iim incubator", "t-hub", "nasscom",
    "bridge round", "growth stage", "late stage", "exit",
]

GRANT_TERMS = [
    "grant", "scheme", "dpiit", "government", "ministry", "subsidy",
    "pli", "mudra", "sidbi", "msme", "budget", "policy",
    "atma nirbhar", "make in india", "atal innovation",
    # ── New ────────────────────────────────────────────────────────
    "meity", "msh", "aim", "niti aayog", "invest india",
    "icreate", "t-hub", "startup hub", "csir", "dsir",
    "seed fund scheme", "sfs", "standup india", "nsic",
    "technology development board", "tdb", "birac", "dst",
    "istart", "kerala startup mission", "tnisea", "tansim",
    "wep", "women entrepreneurship platform", "mahila udyam",
    "ugc startup", "higher education incubation",
    "government tender", "expression of interest", "eoi",
    "call for applications", "open for applications", "last date",
]
