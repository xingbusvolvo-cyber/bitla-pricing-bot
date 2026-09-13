"""
Telegram par message bhejne wala module.
"""

import logging
import requests

import config

logger = logging.getLogger("telegram_notify")


def send_message(text: str):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning("Telegram token/chat_id set nahi hai - message skip.")
        return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        r = requests.post(url, data=payload, timeout=10)
        if not r.ok:
            logger.error(f"Telegram send failed: {r.text}")
    except Exception as e:
        logger.error(f"Telegram send error: {e}")


def format_recommendation(rec: dict) -> str:
    arrow = "🔺" if rec["suggested_fare"] > rec["current_fare"] else (
        "🔻" if rec["suggested_fare"] < rec["current_fare"] else "➡️"
    )
    return (
        f"📍 <b>{rec['route']}</b> ({rec['seat_type']})\n"
        f"Current: ₹{rec['current_fare']} {arrow} Suggested: ₹{rec['suggested_fare']}\n"
        f"Reason: {rec['reason']}"
    )
