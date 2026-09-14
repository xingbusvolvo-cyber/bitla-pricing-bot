import logging
import requests
from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("redbus_diagnostic")

UA = (
    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
)

ROUTE_URL = (
    "https://www.redbus.in/bus-tickets/delhi-to-manali"
    "?fromCityName=Delhi&fromCityId=733&srcCountry=IND"
    "&fromCityType=CITY&toCityName=Manali&toCityId=757"
    "&destCountry=IND&toCityType=CITY&toCityId=757"
    "&destCountry=IND&toCityType=CITY"
    "&onward=15-Sep-2026&doj=15-Sep-2026&ref=home"
)

def requests_test(url, name):
    logger.info("========== REQUESTS TEST: %s ==========", name)
    try:
        r = requests.get(
            url,
            headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"},
            timeout=15,
            allow_redirects=True,
        )
        logger.info("SUCCESS | status=%s | final_url=%s | bytes=%s",
                    r.status_code, r.url, len(r.content))
        logger.info("CONTENT-TYPE: %s", r.headers.get("content-type"))
        logger.info("SERVER: %s", r.headers.get("server"))
    except Exception as e:
        logger.exception("FAILED | %s", e)

def playwright_test(url, name):
    logger.info("========== PLAYWRIGHT TEST: %s ==========", name)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-http2"],
            )
            page = browser.new_page(user_agent=UA)

            def on_failed(req):
                logger.warning(
                    "REQUEST FAILED | %s | %s",
                    req.url,
                    req.failure,
                )

            def on_response(resp):
                if "redbus.in" in resp.url:
                    logger.info(
                        "RESPONSE | %s | %s | %s",
                        resp.status,
                        resp.request.method,
                        resp.url,
                    )

            page.on("requestfailed", on_failed)
            page.on("response", on_response)

            logger.info("Navigating...")
            response = page.goto(
                url,
                timeout=20000,
                wait_until="domcontentloaded",
            )

            logger.info(
                "NAVIGATION SUCCESS | status=%s | final_url=%s",
                response.status if response else "NO_RESPONSE",
                page.url,
            )
            logger.info("TITLE: %s", page.title())
            html = page.content()
            logger.info("HTML BYTES: %s", len(html))

            browser.close()

    except Exception as e:
        logger.exception("PLAYWRIGHT FAILED | %s", e)

if __name__ == "__main__":
    logger.info("RED BUS RAILWAY DIAGNOSTIC STARTED")

    requests_test("https://www.redbus.in/", "HOMEPAGE")
    requests_test(ROUTE_URL, "DELHI-MANALI ROUTE")

    playwright_test("https://www.redbus.in/", "HOMEPAGE")
    playwright_test(ROUTE_URL, "DELHI-MANALI ROUTE")

    logger.info("RED BUS RAILWAY DIAGNOSTIC FINISHED")
