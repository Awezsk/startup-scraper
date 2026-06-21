# C:\Users\awez7\OneDrive\Desktop\Scraper incubin\whatsapp_linkedin_scraper.py

import os
import re
import sys
import asyncio
import sqlite3
import requests
from pathlib import Path
from dotenv import load_dotenv
from whatsapp_bot_proto import init_db, is_already_sent, mark_as_sent, send_via_twilio, send_via_ultramsg

load_dotenv()

# Setup paths
IMAGE_DIR = Path("downloaded_images")
IMAGE_DIR.mkdir(exist_ok=True)

# Config options from .env
TARGET_URL = os.getenv("SCRAPE_TARGET_URL", "https://news.google.com") # fallback target
TARGET_PHONE = os.getenv("TARGET_PHONE")
KEYWORDS = [k.strip().lower() for k in os.getenv("TARGET_KEYWORDS", "register now,apply,apply now,register").split(",")]

async def scrape_page_and_send():
    """
    Crawls target website/LinkedIn public page using Playwright,
    extracts posts/articles, checks for keywords, downloads matching image,
    and sends a WhatsApp notification.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[!] Playwright is not installed. Please run: pip install playwright")
        return

    init_db()

    if not TARGET_PHONE:
        print("[!] TARGET_PHONE is missing in .env. Cannot send WhatsApp alerts.")
        return

    print(f"[*] Starting Scraper for target: {TARGET_URL}")
    print(f"[*] Looking for keywords: {KEYWORDS}")

    async with async_playwright() as p:
        # Launch browser with user agent to minimize detection
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # Navigate to target page
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=45000)
            await page.wait_for_timeout(3000) # Wait for JS to settle

            # We will search for standard cards/posts/articles.
            # Depending on if it's LinkedIn (public feed) or a generic blog/news portal,
            # we query general selectors.
            posts = []

            # Strategy 1: Look for common article / card elements
            card_elements = await page.query_selector_all("article, .card, .feed-shared-update-v2, .post, .entry")
            print(f"[i] Found {len(card_elements)} candidate posts/elements on page.")

            for i, card in enumerate(card_elements):
                text = await card.inner_text()
                text_lower = text.lower()
                
                # Check for keywords
                if any(kw in text_lower for kw in KEYWORDS):
                    print(f"[+] Match found in card #{i}!")

                    # Extract image URL
                    img_el = await card.query_selector("img")
                    img_url = ""
                    if img_el:
                        img_url = await img_el.get_attribute("src") or ""

                    # Create a unique ID for deduplication
                    post_id = f"post_{abs(hash(text[:100]))}"

                    if is_already_sent(post_id):
                        print(f"[-] Already sent card #{i}. Skipping.")
                        continue

                    # Extract clean description
                    description = text.strip()
                    # Limit size of description for WhatsApp
                    if len(description) > 900:
                        description = description[:900] + "... (truncated)"

                    posts.append({
                        "id": post_id,
                        "description": description,
                        "image_url": img_url,
                    })

            # Process matched posts
            for post in posts:
                print(f"[*] Processing Match: {post['id']}")
                
                # Download image locally
                local_img_path = None
                if post["image_url"] and post["image_url"].startswith("http"):
                    # Download image
                    try:
                        safe_id = re.sub(r'[^a-zA-Z0-9]', '_', post["id"])
                        local_path = IMAGE_DIR / f"{safe_id}.jpg"
                        res = requests.get(post["image_url"], timeout=10)
                        if res.status_code == 200:
                            with open(local_path, "wb") as f:
                                f.write(res.content)
                            local_img_path = str(local_path)
                            print(f"[+] Image saved to {local_img_path}")
                    except Exception as e:
                        print(f"[-] Failed to download image: {e}")

                # Send WhatsApp Notification
                sent = False
                media_to_send = post["image_url"] if post["image_url"].startswith("http") else None

                # 1. Twilio
                if os.getenv("TWILIO_ACCOUNT_SID"):
                    sent = send_via_twilio(TARGET_PHONE, post["description"], media_to_send)
                # 2. UltraMsg
                elif os.getenv("ULTRAMSG_INSTANCE_ID"):
                    sent = send_via_ultramsg(TARGET_PHONE, post["description"], media_to_send)
                else:
                    print("[!] No WhatsApp credentials configured. Simulation Mode:")
                    print(f"Description: {post['description']}")
                    print(f"Image Link: {post['image_url']}")
                    sent = True # Simulating success for verification

                if sent:
                    mark_as_sent(post["id"])

        except Exception as e:
            print(f"[-] Scrape failed: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    # If run directly, execute the script
    print("[*] Launching Web & LinkedIn WhatsApp Bot Scraper...")
    asyncio.run(scrape_page_and_send())
