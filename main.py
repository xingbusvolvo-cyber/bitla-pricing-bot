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
from telegram_notify import send_message, format_recommendation

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
        scraped = get_route_data(route)
        rec = get_recommendation(route, scraped)
        message = format_recommendation(rec)
        send_message(message)
        logger.info(f"Done: {route['name']} -> {rec['suggested_fare']}")

    send_message("✅ Pricing check complete. Dashboard mein manually update kar lein.")
    logger.info("=== Pricing check complete ===")


def main():
    logger.info("Bitla Pricing Bot start ho gaya.")
    send_message("🤖 Bitla Pricing Bot online ho gaya hai.")

    for t in config.CHECK_TIMES:
        schedule.every().day.at(t).do(run_check)
        logger.info(f"Scheduled check at {t} IST")

    # Startup pe ek baar turant bhi chala do (test ke liye)
    run_check()

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
