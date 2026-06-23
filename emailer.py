"""
emailer.py — Fetches verified subscribers from Supabase and sends digest.
"""

import logging
import smtplib
import sys
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
import os

load_dotenv()

SENDER_EMAIL        = os.getenv("SENDER_EMAIL", "")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")
SUPABASE_URL        = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY        = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SMTP_HOST           = "smtp.gmail.com"
SMTP_PORT           = 587
IST                 = timezone(timedelta(hours=5, minutes=30))
TEMPLATE_FILE       = "template.html"

log = logging.getLogger(__name__)


def get_verified_subscribers() -> list[dict]:
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        result = sb.table("subscribers") \
                   .select("email, founder_name, startup_name, access_code") \
                   .eq("verified", True) \
                   .execute()
        subs = result.data or []
        log.info(f"Fetched {len(subs)} verified subscribers from Supabase")
        return subs
    except Exception as e:
        log.error(f"Failed to fetch subscribers: {e}")
        return []


def render_email(startups: list[dict], grants: list[dict],
                 founder_name: str = "", startup_name: str = "") -> str:
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
        founder_name=founder_name,
        startup_name=startup_name,
    )


def build_and_send():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    from processor import load_and_process
    startups, grants = load_and_process()
    total = len(startups) + len(grants)

    now_ist = datetime.now(IST)
    subject = (
        f"🚀 IncubeIn Startup Digest — "
        f"{now_ist.strftime('%d %b %Y')} | {total} articles"
    )

    subscribers = get_verified_subscribers()
    if not subscribers:
        log.warning("No verified subscribers — nothing to send.")
        return

    log.info(f"Sending to {len(subscribers)} subscribers...")
    success_count = 0
    fail_count = 0

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)

            for sub in subscribers:
                try:
                    html = render_email(
                        startups, grants,
                        founder_name=sub.get("founder_name", "Founder"),
                        startup_name=sub.get("startup_name", "Your Startup"),
                    )
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"]    = f"IncubeIn Digest <{SENDER_EMAIL}>"
                    msg["To"]      = sub["email"]
                    msg.attach(MIMEText(html, "html", "utf-8"))
                    server.sendmail(SENDER_EMAIL, sub["email"], msg.as_string())
                    log.info(f"  Sent -> {sub['email']}")
                    success_count += 1
                except Exception as e:
                    log.error(f"  Failed -> {sub['email']}: {e}")
                    fail_count += 1

    except smtplib.SMTPAuthenticationError:
        log.error("Gmail auth failed — check SENDER_APP_PASSWORD")
        sys.exit(1)
    except Exception as e:
        log.error(f"SMTP error: {e}")
        sys.exit(1)

    log.info(f"Done: {success_count} sent, {fail_count} failed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    if "--test" in sys.argv:
        log.info("TEST MODE — using sample data")
        sample = [{
            "title": "Test Startup raises ₹50Cr Series A from XYZ Ventures",
            "url": "https://example.com",
            "source": "YourStory",
            "summary": "A Bengaluru-based fintech startup has raised ₹50 crore.",
            "published_at": "2026-04-17T08:00:00+05:30",
            "keywords": ["Series A", "fintech"],
            "category": "startups",
        }]
        grants_sample = [{
            "title": "DPIIT Launches ₹100Cr Innovation Grant for Deep Tech Startups",
            "url": "https://example.com/grant",
            "source": "PIB India",
            "summary": "DPIIT announced a new grant for deep tech startups.",
            "published_at": "2026-04-17T09:00:00+05:30",
            "keywords": ["DPIIT", "grant"],
            "category": "grants",
        }]
        html = render_email(sample, grants_sample,
                            founder_name="Awez", startup_name="IncubeIn")
        # For test mode, send to your own email directly
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                msg = MIMEMultipart("alternative")
                msg["Subject"] = "🚀 TEST — IncubeIn Startup Digest"
                msg["From"]    = f"IncubeIn Digest <{SENDER_EMAIL}>"
                msg["To"]      = SENDER_EMAIL
                msg.attach(MIMEText(html, "html", "utf-8"))
                server.sendmail(SENDER_EMAIL, SENDER_EMAIL, msg.as_string())
                log.info(f"Test email sent to {SENDER_EMAIL}")
        except Exception as e:
            log.error(f"Test send failed: {e}")
    else:
        build_and_send()