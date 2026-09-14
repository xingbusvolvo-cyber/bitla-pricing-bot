"""
Bitla Pricing Bot - Configuration
----------------------------------
Yahan par routes, seat types, aur base fares set hain.
Agar naya route add karna ho, ya fare range change karna ho,
sirf yahi file edit karo - baaki code touch nahi karna.
"""

import os

# ---- Secrets (Railway ke "Variables" tab se aayenge, code mein mat likho) ----
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
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
        "from_city_id": 733,
        "from_city_name": "Delhi",
        "to_city_id": 757,
        "to_city_name": "Manali",
        "redbus_slug": "delhi-to-manali",
        "strategy": "lowest_price",
    },
    {
        "name": "Delhi to Kasol",
        "seat_type": "Semi Sleeper",
        "base_fare": 800,
        "from_city_id": 733,
        "from_city_name": "Delhi",
        "to_city_id": 197688,
        "to_city_name": "Kasol",
        "redbus_slug": "delhi-to-kasol",
        "strategy": "competitive_balanced",
    },
    {
        "name": "Dehradun to Nainital via Haldwani",
        "seat_type": "Seater",
        "base_fare": 800,
        "from_city_id": 777,
        "from_city_name": "Dehradun",
        "to_city_id": 771,
        "to_city_name": "Nainital",
        "redbus_slug": "dehradun-to-nainital",
        "strategy": "competitive_balanced",
    },
    {
        "name": "Dehradun to Nainital via Haldwani",
        "seat_type": "Sleeper",
        "base_fare": 800,
        "from_city_id": 777,
        "from_city_name": "Dehradun",
        "to_city_id": 771,
        "to_city_name": "Nainital",
        "redbus_slug": "dehradun-to-nainital",
        "strategy": "competitive_balanced",
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
