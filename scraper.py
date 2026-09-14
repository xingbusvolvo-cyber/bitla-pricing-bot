"""
RedBus se data uthane wala module.

Playwright-based scraper. RedBus JavaScript se render hota hai, isliye
normal requests ke bajaye headless browser use kiya gaya hai.

Important:
- Navigation ko DOMContentLoaded par block nahi karte; pehle "commit" par
  page accept karte hain, phir bus cards ke liye wait karte hain.
- Navigation retry hoti hai.
- Images/fonts/media block kiye jaate hain taake Railway par page jaldi aaye.
- RedBus ke CSS selectors badal sakte hain, isliye multiple selectors rakhe hain.
- Agar fresh data na mile to safe empty result return hota hai.
"""

import logging
import random
import re
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper")

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
)

NAVIGATION_TIMEOUT_MS = 25_000
CONTENT_WAIT_MS = 20_000
MAX_NAV_ATTEMPTS = 2

# RedBus classes/layout change over time, so keep a few fallbacks.
BUS_CARD_SELECTOR = (
    "li.bus-item, "
    "div.bus-item, "
    "li[class*='bus-item'], "
    "div[class*='bus-item']"
)

FARE_SELECTOR = (
    ".fare, "
    ".f-19, "
    "[class*='fare']"
)

SEAT_SELECTOR = (
    ".seat-left, "
    ".m-top-16, "
    "[class*='seat-left'], "
    "[class*='seatLeft']"
)


def _tomorrow_india() -> str:
    """Return tomorrow in the date format expected by the existing RedBus URL."""
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    return (now_ist + timedelta(days=1)).strftime("%d-%b-%Y")


def _parse_fare(text: str):
    """Extract a sensible INR fare from an element's text."""
    if not text:
        return None

    cleaned = text.replace(",", "").replace("₹", " ").strip()
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", cleaned)
    if not match:
        return None

    try:
        value = float(match.group(1))
        # Avoid accidentally treating tiny numbers (e.g. dates) as fares.
        if 50 <= value <= 100_000:
            return value
    except ValueError:
        pass

    return None


def _parse_seats(text: str):
    """Extract a small positive seat count from an element's text."""
    if not text:
        return None

    match = re.search(r"\b(\d{1,3})\b", text)
    if not match:
        return None

    try:
        value = int(match.group(1))
        if 0 <= value <= 100:
            return value
    except ValueError:
        pass

    return None


def _make_search_url(route: dict, travel_date: str) -> str:
    return (
        f"https://www.redbus.in/bus-tickets/{route['redbus_slug']}"
        f"?fromCityName={route['from_city_name']}"
        f"&fromCityId={route['from_city_id']}"
        f"&srcCountry=IND"
        f"&fromCityType=CITY"
        f"&toCityName={route['to_city_name']}"
        f"&toCityId={route['to_city_id']}"
        f"&destCountry=IND"
        f"&toCityType=CITY"
        f"&onward={travel_date}"
        f"&doj={travel_date}"
        f"&ref=home"
    )


def get_route_data(route: dict) -> dict:
    """
    Ek route ke liye RedBus se:
    - competitor fares
    - available seats estimate

    Failure par safe empty result return karta hai taake pricing system crash na ho.
    """
    travel_date = _tomorrow_india()

    result = {
        "available_seats": None,
        "total_seats": None,
        "competitor_fares": [],
        "scrape_success": False,
    }

    search_url = _make_search_url(route, travel_date)
    logger.info(
        "RedBus check: %s | travel_date=%s",
        route["name"],
        travel_date,
    )

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

            context = browser.new_context(
                user_agent=USER_AGENT,
                locale="en-IN",
                viewport={"width": 390, "height": 844},
            )

            # Static resources are not needed for fare/seat extraction.
            def handle_route(route_obj):
                resource_type = route_obj.request.resource_type
                if resource_type in {"image", "media", "font"}:
                    route_obj.abort()
                else:
                    route_obj.continue_()

            context.route("**/*", handle_route)
            page = context.new_page()

            navigation_ok = False

            for attempt in range(1, MAX_NAV_ATTEMPTS + 1):
                try:
                    logger.info(
                        "RedBus navigation attempt %d/%d: %s",
                        attempt,
                        MAX_NAV_ATTEMPTS,
                        route["name"],
                    )

                    # "commit" avoids waiting for RedBus's many long-lived
                    # requests. We then explicitly wait for the actual bus UI.
                    page.goto(
                        search_url,
                        timeout=NAVIGATION_TIMEOUT_MS,
                        wait_until="commit",
                    )
                    navigation_ok = True
                    break

                except PlaywrightTimeoutError as exc:
                    logger.warning(
                        "RedBus navigation timeout on attempt %d/%d for %s: %s",
                        attempt,
                        MAX_NAV_ATTEMPTS,
                        route["name"],
                        exc,
                    )
                    if attempt < MAX_NAV_ATTEMPTS:
                        time.sleep(2)

                except Exception as exc:
                    logger.warning(
                        "RedBus navigation error on attempt %d/%d for %s: %s",
                        attempt,
                        MAX_NAV_ATTEMPTS,
                        route["name"],
                        exc,
                    )
                    if attempt < MAX_NAV_ATTEMPTS:
                        time.sleep(2)

            if not navigation_ok:
                browser.close()
                return result

            # Give React time to render, but don't wait forever for network idle.
            try:
                page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=10_000,
                )
            except PlaywrightTimeoutError:
                logger.info(
                    "DOMContentLoaded timeout for %s; continuing with rendered page.",
                    route["name"],
                )

            try:
                page.wait_for_selector(
                    BUS_CARD_SELECTOR,
                    timeout=CONTENT_WAIT_MS,
                )
            except PlaywrightTimeoutError:
                logger.warning(
                    "No RedBus bus cards appeared within %ss for %s.",
                    CONTENT_WAIT_MS // 1000,
                    route["name"],
                )

            # Small extra render window for fare/seat text.
            page.wait_for_timeout(2_000)

            bus_cards = page.query_selector_all(BUS_CARD_SELECTOR)
            logger.info(
                "RedBus bus cards found for %s: %d",
                route["name"],
                len(bus_cards),
            )

            fares = []
            seats_left_list = []

            for card in bus_cards[:15]:
                try:
                    fare_el = card.query_selector(FARE_SELECTOR)
                    seats_el = card.query_selector(SEAT_SELECTOR)

                    if fare_el:
                        fare = _parse_fare(fare_el.inner_text())
                        if fare is not None:
                            fares.append(fare)

                    if seats_el:
                        seats = _parse_seats(seats_el.inner_text())
                        if seats is not None:
                            seats_left_list.append(seats)

                except Exception:
                    continue

            if fares:
                result["competitor_fares"] = fares
                result["scrape_success"] = True

            if seats_left_list:
                result["available_seats"] = (
                    sum(seats_left_list) / len(seats_left_list)
                )

            if not fares:
                # Useful diagnostic if RedBus changed its selectors or returned
                # a block/error page instead of the bus list.
                try:
                    title = page.title()
                except Exception:
                    title = ""

                logger.warning(
                    "No fares extracted for %s. Page title=%r, cards=%d",
                    route["name"],
                    title,
                    len(bus_cards),
                )

            browser.close()

    except Exception as exc:
        logger.warning(
            "Scraping failed for %s: %s",
            route["name"],
            exc,
        )

    # Rate limiting: next route se pehle 3-5 sec gap.
    time.sleep(random.uniform(3, 5))

    return result
