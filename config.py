"""
Bitla Pricing Bot - Configuration
----------------------------------
Yahan par routes, seat types, aur base fares set hain.
Agar naya route add karna ho, ya fare range change karna ho,
sirf yahi file edit karo - baaki code touch nahi karna.
"""

import os

# ---- Secrets (Railway ke "Variables" tab se aayenge, code mein mat likho) ----
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ---- Routes ----
# har route ka: naam, seat_type, base_fare (current normal fare)
# min/max apne aap base_fare ke +/- 35% se calculate ho jata hai neeche.
ROUTES = [
    {
        "name": "Delhi to Manali",
        "seat_type": "Semi Sleeper",
        "base_fare": 800,
        "redbus_search": "https://www.redbus.in/bus-tickets/delhi-to-manali",
    },
    {
        "name": "Delhi to Kasol",
        "seat_type": "Semi Sleeper",
        "base_fare": 800,
        "redbus_search": "https://www.redbus.in/bus-tickets/delhi-to-kasol",
    },
    {
        "name": "Dehradun to Nainital via Haldwani",
        "seat_type": "Seater/Sleeper",
        "base_fare": 800,
        "redbus_search": "https://www.redbus.in/bus-tickets/dehradun-to-nainital",
    },
]

# Safety range: fare kabhi bhi base_fare ke is % se neeche/upar nahi jayegi
MIN_FARE_PERCENT = 0.65   # base_fare ka 65% = minimum allowed
MAX_FARE_PERCENT = 1.40   # base_fare ka 140% = maximum allowed

for r in ROUTES:
    r["min_fare"] = round(r["base_fare"] * MIN_FARE_PERCENT)
    r["max_fare"] = round(r["base_fare"] * MAX_FARE_PERCENT)

# Din mein kitni baar check ho (24-hour format, IST)
CHECK_TIMES = ["09:00", "14:00", "19:00"]
