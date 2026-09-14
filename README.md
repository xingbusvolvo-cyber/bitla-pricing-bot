# Bitla Pricing Bot - Final Setup

Ye poora system fresh se deploy karne ke liye hai. Sab files is folder mein
hain — GitHub par sab ek saath upload karo (purana repo khaali karke ya
naya repo bana kar).

## Files (total 7)
- config.py — routes, seat types, fares, min/max, schedule
- scraper.py — RedBus se live data uthata hai (Playwright)
- pricing_engine.py — Google Gemini se pricing recommendation (owner-mindset)
- telegram_notify.py — Telegram par message bhejna + naye messages sunna
- main.py — sabko jodta hai, schedule + on-demand trigger
- requirements.txt — Python libraries
- Dockerfile — Playwright ka ready-made environment (Railway isay use karega)

## Zaroori Railway Variables (worker service ke Variables tab mein)
| Name | Value |
|------|-------|
| GEMINI_API_KEY | Google AI Studio wali key |
| TELEGRAM_BOT_TOKEN | BotFather wala token |
| TELEGRAM_CHAT_ID | Aapka Telegram chat ID |

## Railway Settings
- Builder: **Dockerfile** (Settings mein select karna, "Railpack" nahi)
- Custom Build Command: khaali chhod do (Dockerfile khud sab karega)
- Custom Start Command: khaali chhod do

## Deploy steps
1. GitHub repo mein saari 7 files upload karo, commit karo
2. Railway → naya project → GitHub repo select karo
3. Settings mein Builder ko "Dockerfile" set karo
4. Variables tab mein 3 keys daalo (upar wali table)
5. Deploy hone do (5-10 min pehli baar, Docker image download hogi)
6. Telegram par bot khud "online ho gaya" message bhejega, phir turant
   pehla pricing-check chalega

## Roz kya hota hai
- Bot din mein 3 baar (9 AM, 2 PM, 7 PM IST) khud check karta hai
- Kabhi bhi turant check chalane ke liye, bot ko Telegram par koi bhi
  message bhej do (jaise "check")
- Har route ke liye RedBus se kal ki date ka live data uthata hai,
  phir Gemini ko diya jata hai jo ek "business owner" ki tarah sochta hai
  (date, weekend/holiday, competitor prices, demand — sab dekh kar)
- Result Telegram par aata hai, aapko sirf Bitla/TicketSimply dashboard
  mein manually daalna hai

## Fare adjust karna
`config.py` mein `MIN_FARE_PERCENT` / `MAX_FARE_PERCENT` change karke
range set karo. Naya route add karna ho to `ROUTES` list mein entry add
karo, RedBus city ID redbus.in URL se dhoond kar.
