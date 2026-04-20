# 🚀 India Startup & Grants — Automated News Digest

Automatically scrapes India startup and grants news every day at **9:00 AM IST** and emails a beautiful digest to your Gmail at **10:00 AM IST**.

---

## 📁 Project Structure

```
Scraper incubin/
├── main.py               ← Scheduler (keeps running, 9AM scrape + 10AM email)
├── scraper.py            ← RSS + Playwright multi-source scraper
├── processor.py          ← Keyword extraction & categorization
├── emailer.py            ← Gmail SMTP digest sender
├── template.html         ← Rich HTML email template
├── config.py             ← All settings (sources, keywords, schedule)
├── .env                  ← YOUR credentials (create from .env.example)
├── .env.example          ← Credential template
├── requirements.txt      ← Python dependencies
├── setup_scheduler.bat   ← Register Windows Task Scheduler jobs
└── articles.json         ← Auto-generated: scraped articles (daily)
```

---

## ⚡ Quick Setup (5 steps)

### Step 1 — Install dependencies
```bash
cd "Scraper incubin"
pip install -r requirements.txt
playwright install chromium
```

### Step 2 — Create your `.env` file
```bash
copy .env.example .env
```
Then open `.env` and fill in:
```
SENDER_EMAIL=youremail@gmail.com
SENDER_APP_PASSWORD=xxxx xxxx xxxx xxxx
RECIPIENT_EMAIL=recipient@gmail.com
```

> ⚠️ **Important**: Use a **Gmail App Password**, NOT your real Gmail password.
> Get one at: https://myaccount.google.com/apppasswords
> (Requires 2-Step Verification to be enabled)

### Step 3 — Test the email immediately
```bash
python emailer.py --test
```
Check your inbox — you should receive a sample digest email.

### Step 4 — Test the scraper manually
```bash
python scraper.py
```
This saves articles to `articles.json`. Check the output.

### Step 5A — Run with Python scheduler (keep window open)
```bash
python main.py
```
Leave this running. It will scrape at 9 AM and email at 10 AM every day.

### Step 5B — OR use Windows Task Scheduler (runs even when script isn't open)
Right-click `setup_scheduler.bat` → **Run as administrator**
This registers automatic daily tasks that run without keeping a Python window open.

---

## 📧 Email Preview

The digest contains:
- **🚀 Funding & Startups** section (purple cards)
- **🏛️ Government Grants & Schemes** section (green cards)
- Each article: title, source, date, summary, extracted keywords, and a "Read Article" button

---

## 📡 News Sources

| Source | Type |
|--------|------|
| YourStory | RSS |
| Inc42 | RSS |
| ET Startups (Economic Times) | RSS |
| Entrackr | RSS |
| VCCircle | RSS |
| PIB India (Press Info Bureau) | RSS |
| Business Standard Startups | RSS |
| Google News — India Startup Funding | RSS (via Google) |
| Google News — India Grants & Schemes | RSS (via Google) |
| Google News — DPIIT | RSS (via Google) |
| Google News — VC India | RSS (via Google) |
| Google News — Incubators | RSS (via Google) |
| Startup India Portal | Playwright |

---

## 🔧 Customisation

- **Add/remove sources** → edit `RSS_SOURCES` in `config.py`
- **Change schedule time** → edit `SCRAPE_HOUR` / `EMAIL_HOUR` in `config.py`
- **Add more keywords** → edit `TOPIC_TERMS` / `GRANT_TERMS` in `config.py`
- **Change email design** → edit `template.html`

---

## 🐛 Debugging

Run the scraper with visible browser (headed mode):
```bash
# In scraper.py → change headless=True to headless=False temporarily
```

View logs:
```bash
type scraper.log
```
