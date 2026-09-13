"""
Google Gemini (free tier) ko data bhej kar fare recommendation lena.
Anthropic Claude ki jagah ab Gemini use ho raha hai kyunki iska free
tier hai (koi card nahi chahiye).
"""

import json
import logging
import time
import requests

import config

logger = logging.getLogger("pricing_engine")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash-lite:generateContent"
)

SYSTEM_PROMPT = """You are a strict, business-minded pricing analyst for an intercity
bus operator in India. You think like someone protecting margins while
staying competitive - not a generic assistant.

You will be given data about one bus route: its current fare, seat type,
a pricing strategy to follow, competitor fares scraped from RedBus, and
available seat estimates.

Two possible strategies, given in the input as "strategy":
- "lowest_price": This route should be priced BELOW every competitor fare
  given, to win volume/market share. If competitor_fares is non-empty,
  the suggested_fare should be lower than the minimum competitor fare
  (but never below min_fare). If competitor_fares is empty, keep the
  fare close to current_fare and say so clearly.
- "competitive_balanced": Price close to the average competitor fare -
  not the cheapest, not the most expensive. Adjust up if seats are
  scarce (high demand), down if many seats are unsold, always stying
  within min_fare/max_fare.

Rules:
- Never suggest a fare below min_fare or above max_fare given in the input.
- If data is missing (competitor_fares empty, available_seats null), be
  conservative and say plainly that fare is being kept close to current
  because live market data wasn't available this cycle.
- Your "reason" must read like a short business note: mention the actual
  competitor price range you saw (or note that none was available),
  the occupancy/demand signal if present, and which strategy you applied.
  2-3 sentences, in Hindi/Urdu written in Roman script. No generic filler.
- Respond ONLY with valid JSON, no other text, no markdown fences.

Output JSON format exactly:
{
  "route": "<route name>",
  "seat_type": "<seat type>",
  "current_fare": <number>,
  "suggested_fare": <number>,
  "reason": "<2-3 sentence business-style explanation in Hindi/Urdu (Roman script)>"
}
"""


def _call_gemini(input_data: dict) -> dict:
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": json.dumps(input_data, indent=2)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 500,
            "responseMimeType": "application/json",
        },
    }

    resp = requests.post(
        f"{GEMINI_URL}?key={config.GEMINI_API_KEY}",
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
    return json.loads(raw_text)


def get_recommendation(route: dict, scraped: dict) -> dict:
    """
    route: entry from config.ROUTES (has base_fare, min_fare, max_fare, etc.)
    scraped: dict returned by scraper.get_route_data()
    """
    input_data = {
        "route": route["name"],
        "seat_type": route["seat_type"],
        "current_fare": route["base_fare"],
        "min_fare": route["min_fare"],
        "max_fare": route["max_fare"],
        "strategy": route.get("strategy", "competitive_balanced"),
        "competitor_fares": scraped.get("competitor_fares", []),
        "available_seats_estimate": scraped.get("available_seats"),
        "scrape_success": scraped.get("scrape_success", False),
    }

    last_error = None
    backoff_seconds = [15, 30, 60]
    for attempt in range(3):
        try:
            recommendation = _call_gemini(input_data)

            suggested = recommendation.get("suggested_fare", route["base_fare"])
            suggested = max(route["min_fare"], min(route["max_fare"], suggested))
            recommendation["suggested_fare"] = suggested

            return recommendation
        except Exception as e:
            last_error = e
            logger.warning(
                f"Gemini attempt {attempt + 1} failed for {route['name']}: {e}"
            )
            time.sleep(backoff_seconds[attempt])

    logger.error(f"Gemini recommendation failed for {route['name']}: {last_error}")
    return {
        "route": route["name"],
        "seat_type": route["seat_type"],
        "current_fare": route["base_fare"],
        "suggested_fare": route["base_fare"],
        "reason": "Data analyze nahi ho paya, fare same rakhi gayi hai.",
    }
