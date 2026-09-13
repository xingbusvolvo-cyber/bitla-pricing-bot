"""
Ye ek baar chalane wali chhoti si script hai jo aapka Telegram "chat_id"
pata karti hai. Ye ID bot ko batati hai ke message KISKO bhejna hai.

Kaise use karein:
1. Pehle apne bot ko Telegram par dhundo (jo username aapne BotFather ko
   diya tha, jaise @bitla_pricing_bot) aur usay ek message bhejo, jaise "hi"
2. Phir is script ko chalao: python get_chat_id.py
3. Jo number print ho, wahi aapka TELEGRAM_CHAT_ID hai - Railway Variables
   mein daal dena.
"""

import os
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

if not TOKEN:
    print("TELEGRAM_BOT_TOKEN environment variable set nahi hai.")
else:
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    resp = requests.get(url, timeout=10).json()
    results = resp.get("result", [])
    if not results:
        print("Koi message nahi mila. Pehle bot ko Telegram par 'hi' bhejo, phir dobara try karo.")
    else:
        chat_id = results[-1]["message"]["chat"]["id"]
        print(f"Aapka chat_id: {chat_id}")
