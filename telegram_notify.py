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


def get_new_messages(offset=None):
    """
    Telegram se naye messages check karta hai (long polling).
    Returns: (list of message texts, next offset to use)
    """
    if not config.TELEGRAM_BOT_TOKEN:
        return [], offset

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 20}
    if offset is not None:
        params["offset"] = offset

    try:
        r = requests.get(url, params=params, timeout=25)
        r.raise_for_status()
        data = r.json()
        results = data.get("result", [])

        messages = []
        next_offset = offset
        for update in results:
            next_offset = update["update_id"] + 1
            msg = update.get("message", {})
            text = msg.get("text", "")
            chat_id = str(msg.get("chat", {}).get("id", ""))
            # sirf apne wale chat_id se aaye message par react karo
            if text and chat_id == str(config.TELEGRAM_CHAT_ID):
                messages.append(text)

        return messages, next_offset
    except Exception as e:
        logger.error(f"Telegram get_updates error: {e}")
        return [], offset


def format_recommendation(rec: dict) -> str:
    arrow = "🔺" if rec["suggested_fare"] > rec["current_fare"] else (
        "🔻" if rec["suggested_fare"] < rec["current_fare"] else "➡️"
    )
    return (
        f"📍 <b>{rec['route']}</b> ({rec['seat_type']})\n"
        f"Current: ₹{rec['current_fare']} {arrow} Suggested: ₹{rec['suggested_fare']}\n"
        f"Reason: {rec['reason']}"
    )
