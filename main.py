"""
main.py — Scheduler entry point.
Runs scraper at 9:00 AM IST and sends email at 10:00 AM IST every day.
Keep this script running in the background (or use setup_scheduler.bat).

Usage:
    python main.py
"""

import logging
import sys
from datetime import timezone, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import SCRAPE_HOUR, SCRAPE_MINUTE, EMAIL_HOUR, EMAIL_MINUTE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


def job_scrape():
    log.info("Scheduled job: SCRAPE + DASHBOARD starting...")
    try:
        from scraper import run_scraper
        articles = run_scraper()
        log.info(f"Scrape complete - {len(articles)} articles saved")
        # Dashboard is auto-generated inside run_scraper(), nothing extra needed
    except Exception as e:
        log.error(f"Scrape job failed: {e}", exc_info=True)


def job_email():
    log.info("⏰ Scheduled job: EMAIL starting...")
    try:
        from emailer import build_and_send
        build_and_send()
        log.info("⏰ Email job complete")
    except Exception as e:
        log.error(f"Email job failed: {e}", exc_info=True)


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    # 9:00 AM IST — scrape
    scheduler.add_job(
        job_scrape,
        CronTrigger(hour=SCRAPE_HOUR, minute=SCRAPE_MINUTE, timezone="Asia/Kolkata"),
        id="daily_scrape",
        name="Daily News Scraper (9 AM IST)",
    )

    # 10:00 AM IST — send email
    scheduler.add_job(
        job_email,
        CronTrigger(hour=EMAIL_HOUR, minute=EMAIL_MINUTE, timezone="Asia/Kolkata"),
        id="daily_email",
        name="Daily Digest Email (10 AM IST)",
    )

    log.info("=" * 55)
    log.info("  India Startup & Grants Digest — Scheduler Running")
    log.info(f"  Scrape:  {SCRAPE_HOUR:02d}:{SCRAPE_MINUTE:02d} IST daily")
    log.info(f"  Email:   {EMAIL_HOUR:02d}:{EMAIL_MINUTE:02d} IST daily")
    log.info("  Press Ctrl+C to stop")
    log.info("=" * 55)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")
