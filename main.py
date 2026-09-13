"""
Bitla Pricing Bot - Main entry point.
Ye file 24/7 chalti rahegi (Railway par) aur din mein config.CHECK_TIMES
par set kiye gaye time par har route check karegi.
"""

import logging
import time
from datetime import datetime

import schedule

import config
from scraper import get_route_data
from pricing_engine import get_recommendation
from telegram_notify import send_message, format_recommendation, get_new_messages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


def run_check():
    logger.info("=== Pricing check shuru ===")
    send_message("🔄 Pricing check shuru ho raha hai...")

    for route in config.ROUTES:
        logger.info(f"Checking: {route['name']}")
        send_message(f"🔍 <b>{route['name']}</b> — RedBus se live data nikal raha hoon...")

        scraped = get_route_data(route)
        if scraped.get("scrape_success"):
            send_message(
                f"✅ RedBus data mil gaya ({len(scraped.get('competitor_fares', []))} "
                f"competitor fares). Ab Gemini se analysis karwa raha hoon..."
            )
        else:
            send_message(
                "⚠️ RedBus se live data nahi mil paya is baar. Phir bhi Gemini se "
                "best possible analysis karwa raha hoon..."
            )

        rec = get_recommendation(route, scraped)
        message = format_recommendation(rec)
        send_message(message)
        logger.info(f"Done: {route['name']} -> {rec['suggested_fare']}")
        time.sleep(20)  # Gemini free-tier rate limit se bachne ke liye gap

    send_message("✅ Pricing check complete. Dashboard mein manually update kar lein.")
    logger.info("=== Pricing check complete ===")


def main():
    logger.info("Bitla Pricing Bot start ho gaya.")
    send_message(
        "🤖 Bitla Pricing Bot online ho gaya hai.\n"
        "Kabhi bhi turant check chalane ke liye, mujhe koi bhi message bhej dena "
        "(jaise 'check')."
    )

    for t in config.CHECK_TIMES:
        schedule.every().day.at(t).do(run_check)
        logger.info(f"Scheduled check at {t} IST")

    # Startup pe ek baar turant bhi chala do (test ke liye)
    run_check()

    telegram_offset = None
    while True:
        schedule.run_pending()

        # Telegram se naye messages check karo - agar koi bhi message
        # aaye, turant naya check chala do
        messages, telegram_offset = get_new_messages(telegram_offset)
        if messages:
            logger.info(f"Manual trigger received via Telegram: {messages}")
            run_check()

        time.sleep(3)


if __name__ == "__main__":
    main()
