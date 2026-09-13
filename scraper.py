"""
RedBus se data uthane wala module.

IMPORTANT NOTE (Preet ke liye bhi, future editor ke liye bhi):
RedBus ki website JavaScript se load hoti hai (React-based), isliye
simple "requests" library se poora data nahi milta - isliye Playwright
(ek headless browser) use kiya hai jo asli browser jaisa page load karta hai.

RedBus apni website ki HTML structure (class names, layout) time-time par
badalte rehte hain. Agar kabhi scraper "0 results" ya galat data dena shuru
kare, iska matlab hai RedBus ne apni site thodi change kar di hai - tab
neeche wale CSS selectors (jo "SELECTOR:" comment ke sath likhe hain) ko
update karna padega. Ye normal hai scraping projects mein, koi bug nahi.

Rate-limiting: har route ke beech 3-5 second ka gap rakha gaya hai taake
RedBus ke server par load na pade aur IP block na ho.
"""

import time
import random
import logging
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper")


def get_route_data(route: dict) -> dict:
    """
    Ek route ke liye RedBus se data nikalta hai:
    - available seats (jitni bachi hain)
    - total seats (andaza, ya jo page se milay)
    - competitor operators ke fares (list)

    Return: dict with keys: available_seats, total_seats, competitor_fares
    Agar scraping fail ho jaye, safe default return karta hai (khaali data)
    taake pura system crash na ho - us waqt sirf apna base_fare use hoga.
    """
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d-%b-%Y")
    result = {
        "available_seats": None,
        "total_seats": None,
        "competitor_fares": [],
        "scrape_success": False,
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
                )
            )
            page.goto(route["redbus_search"], timeout=20000)
            page.wait_for_timeout(4000)  # page ko fully render hone do

            # SELECTOR: bus card list - RedBus par ye class time ke sath
            # badal sakti hai. Agar 0 buses milein, ye line check karo.
            bus_cards = page.query_selector_all("li.bus-item, div.bus-item")

            fares = []
            seats_left_list = []

            for card in bus_cards[:15]:  # top 15 buses hi check karo
                try:
                    fare_el = card.query_selector(".fare, .f-19")
                    seats_el = card.query_selector(".seat-left, .m-top-16")

                    if fare_el:
                        fare_text = fare_el.inner_text().replace(
                            "₹", ""
                        ).replace(",", "").strip()
                        if fare_text.replace(".", "").isdigit():
                            fares.append(float(fare_text))

                    if seats_el:
                        seats_text = "".join(
                            filter(str.isdigit, seats_el.inner_text())
                        )
                        if seats_text:
                            seats_left_list.append(int(seats_text))
                except Exception:
                    continue

            browser.close()

            if fares:
                result["competitor_fares"] = fares
                result["scrape_success"] = True
            if seats_left_list:
                result["available_seats"] = sum(seats_left_list) / len(
                    seats_left_list
                )

    except Exception as e:
        logger.warning(f"Scraping failed for {route['name']}: {e}")

    # rate limiting - agla route check karne se pehle thoda ruko
    time.sleep(random.uniform(3, 5))

    return result
