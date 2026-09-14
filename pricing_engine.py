"""
Google Gemini (free tier) ko data bhej kar fare recommendation lena.
Anthropic Claude ki jagah ab Gemini use ho raha hai kyunki iska free
tier hai (koi card nahi chahiye).
"""

import json
import logging
import time
from datetime import datetime, timedelta
import requests

import config

logger = logging.getLogger("pricing_engine")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
GEMINI_MODEL = "gemini-3.6-flash"

SYSTEM_PROMPT = """You are the OWNER of an intercity bus operator in India, personally
deciding today's fare for one route. Think like a business owner protecting
margins while staying competitive - not a generic assistant following a
checklist.

You will be given: current fare, seat type, a pricing strategy, today's
date and day of week, competitor fares scraped from RedBus just now, and
an estimate of how many seats are still open on competitor buses.

Two possible strategies, given in the input as "strategy":
- "lowest_price": This route should undercut every competitor fare given,
  to win volume/market share. If competitor_fares is non-empty, price
  below the minimum competitor fare (never below min_fare). If empty,
  keep fare close to current_fare and say so.
- "competitive_balanced": Price near the average competitor fare - not
  cheapest, not priciest. Push up when demand looks strong, pull down
  when seats are sitting unsold.

Use your own judgement about demand, exactly like an owner would:
- Is today's date near a weekend, a long weekend, or a known Indian
  holiday/festival period? Say so and factor it in.
- Do the competitor seat numbers suggest buses filling up fast (raise
  price) or sitting empty (drop price to move seats)?
- If RedBus data wasn't available this cycle, say plainly you're pricing
  conservatively without fresh market data, using calendar sense instead.

Rules:
- Never suggest a fare below min_fare or above max_fare given in the input.
- Respond ONLY with valid JSON, no other text, no markdown fences.
- "reason" must read like the owner's own short note: 2-3 sentences,
  mentioning the actual competitor price range (or its absence), the date/
  demand reasoning, and the call you made. Write it in Hindi/Urdu using
  Roman script. No generic filler like "data not available" without
  explaining what you did instead.

Output JSON format exactly:
{
  "route": "<route name>",
  "seat_type": "<seat type>",
  "current_fare": <number>,
  "suggested_fare": <number>,
  "reason": "<2-3 sentence owner-style note in Hindi/Urdu (Roman script)>"
}
"""


def _call_gemini(input_data: dict) -> dict:
    full_input = SYSTEM_PROMPT + "\n\nInput data:\n" + json.dumps(input_data, indent=2)

    payload = {
        "model": GEMINI_MODEL,
        "input": full_input,
    }

    resp = requests.post(
        GEMINI_URL,
        json=payload,
        headers={
            "x-goog-api-key": config.GEMINI_API_KEY,
            "Content-Type": "application/json",
            "Api-Revision": "2026-05-20",
        },
        timeout=30,
    )
    if not resp.ok:
        logger.error(
            f"Gemini API error {resp.status_code}. Full response: {resp.text}"
        )
    resp.raise_for_status()
    data = resp.json()

    # Naye Interactions API mein jawab "steps" list ke andar aata hai -
    # sabse aakhri "model_output" step ka text nikalna hai.
    raw_text = ""
    for step in reversed(data.get("steps", [])):
        if step.get("type") == "model_output":
            for content_item in step.get("content", []):
                if content_item.get("type") == "text":
                    raw_text = content_item.get("text", "")
                    break
            break

    raw_text = raw_text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    if not raw_text:
        raise ValueError(
            f"Gemini returned no model output. Full response: {json.dumps(data)}"
        )

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini returned invalid JSON: {raw_text[:2000]}"
        ) from exc


def get_recommendation(route: dict, scraped: dict) -> dict:
    """
    route: entry from config.ROUTES (has base_fare, min_fare, max_fare, etc.)
    scraped: dict returned by scraper.get_route_data()
    """
    travel_date = datetime.now() + timedelta(days=1)
    input_data = {
        "route": route["name"],
        "seat_type": route["seat_type"],
        "current_fare": route["base_fare"],
        "min_fare": route["min_fare"],
        "max_fare": route["max_fare"],
        "strategy": route.get("strategy", "competitive_balanced"),
        "travel_date": travel_date.strftime("%Y-%m-%d"),
        "day_of_week": travel_date.strftime("%A"),
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
