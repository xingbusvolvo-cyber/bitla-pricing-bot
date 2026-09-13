"""
Claude (Anthropic API) ko data bhej kar fare recommendation lena.
"""

import json
import logging
import anthropic

import config

logger = logging.getLogger("pricing_engine")

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a pricing analyst for an intercity bus operator in India.
You will be given data about one bus route: its current fare, seat type,
competitor fares scraped from RedBus, and available seat estimates.

Your job: suggest a new fare for this route.

Rules:
- Never suggest a fare below min_fare or above max_fare given in the input.
- If data is missing (competitor_fares empty, available_seats null), be
  conservative and suggest a fare close to the current base_fare.
- Consider: if seats are scarce (high demand) relative to typical booking
  patterns, price can move up; if many seats are open, price can move down
  to stay competitive with RedBus operators.
- Respond ONLY with valid JSON, no other text, no markdown fences.

Output JSON format exactly:
{
  "route": "<route name>",
  "seat_type": "<seat type>",
  "current_fare": <number>,
  "suggested_fare": <number>,
  "reason": "<one short sentence in Hindi/Urdu (Roman script) explaining why>"
}
"""


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
        "competitor_fares": scraped.get("competitor_fares", []),
        "available_seats_estimate": scraped.get("available_seats"),
        "scrape_success": scraped.get("scrape_success", False),
    }

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(input_data, indent=2),
                }
            ],
        )
        raw_text = message.content[0].text.strip()
        # safety: agar Claude ne kabhi ```json fence laga di ho to hata do
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        recommendation = json.loads(raw_text)

        # double safety-check: min/max ke bahar kabhi na jaye
        suggested = recommendation.get("suggested_fare", route["base_fare"])
        suggested = max(route["min_fare"], min(route["max_fare"], suggested))
        recommendation["suggested_fare"] = suggested

        return recommendation

    except Exception as e:
        logger.error(f"Claude recommendation failed for {route['name']}: {e}")
        return {
            "route": route["name"],
            "seat_type": route["seat_type"],
            "current_fare": route["base_fare"],
            "suggested_fare": route["base_fare"],
            "reason": "Data analyze nahi ho paya, fare same rakhi gayi hai.",
        }
