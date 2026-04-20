"""
emailer.py — Renders the HTML digest and sends it via Gmail SMTP.
Usage:
    python emailer.py          → sends using current articles.json
    python emailer.py --test   → sends test email immediately
"""

import logging
import smtplib
import sys
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config import (
    SENDER_EMAIL, SENDER_APP_PASSWORD, RECIPIENT_EMAILS,
    SMTP_HOST, SMTP_PORT,
)
from processor import load_and_process

log = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))
TEMPLATE_FILE = "template.html"


def render_email(startups: list[dict], grants: list[dict]) -> str:
    """Render the Jinja2 HTML template."""
    now_ist = datetime.now(IST)
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent)))
    template = env.get_template(TEMPLATE_FILE)
    return template.render(
        startups=startups,
        grants=grants,
        total=len(startups) + len(grants),
        startup_count=len(startups),
        grants_count=len(grants),
        date_str=now_ist.strftime("%A, %d %B %Y"),
        generated_at=now_ist.strftime("%I:%M %p"),
    )


def send_email(html_body: str, subject: str) -> bool:
    """Send HTML email via Gmail SMTP to all recipients. Returns True on success."""
    if not all([SENDER_EMAIL, SENDER_APP_PASSWORD, RECIPIENT_EMAILS]):
        log.error("Missing Gmail credentials or recipients — check your .env file or Secrets")
        return False

    recipients = [e.strip() for e in RECIPIENT_EMAILS.split(",") if e.strip()]
    if not recipients:
        log.error("No valid recipient emails found.")
        return False

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            
            for recipient in recipients:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"]    = f"India Digest Bot <{SENDER_EMAIL}>"
                msg["To"]      = recipient
                msg.attach(MIMEText(html_body, "html", "utf-8"))
                
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
                log.info(f"✅ Email sent to {recipient}")
                
        return True
    except smtplib.SMTPAuthenticationError:
        log.error("Gmail auth failed — did you use an App Password? (not your real password)")
        return False
    except Exception as e:
        log.error(f"SMTP error: {e}")
        return False


def build_and_send():
    """Main entry: load articles → render → send."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    startups, grants = load_and_process()
    total = len(startups) + len(grants)

    now_ist = datetime.now(IST)
    subject = (
        f"🚀 India Startup & Grants Digest — "
        f"{now_ist.strftime('%d %b %Y')} | {total} articles"
    )

    log.info(f"Rendering email: {total} articles ({len(startups)} startups, {len(grants)} grants)")
    html = render_email(startups, grants)
    send_email(html, subject)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if "--test" in sys.argv:
        log.info("TEST MODE — using sample data")
        sample = [{
            "title": "Test Startup raises ₹50Cr Series A from XYZ Ventures",
            "url": "https://example.com",
            "source": "YourStory",
            "summary": "A Bengaluru-based fintech startup has raised ₹50 crore in a Series A round.",
            "published_at": "2026-04-17T08:00:00+05:30",
            "keywords": ["Series A", "fintech", "Bengaluru", "startup funding"],
            "category": "startups",
        }]
        grants_sample = [{
            "title": "DPIIT Launches ₹100Cr Innovation Grant for Deep Tech Startups",
            "url": "https://example.com/grant",
            "source": "PIB India",
            "summary": "The Department for Promotion of Industry and Internal Trade announced a new grant.",
            "published_at": "2026-04-17T09:00:00+05:30",
            "keywords": ["DPIIT", "grant", "deep tech", "innovation"],
            "category": "grants",
        }]
        html = render_email(sample, grants_sample)
        send_email(html, "🚀 TEST — India Startup & Grants Digest")
    else:
        build_and_send()
