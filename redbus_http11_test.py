import logging
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("redbus_http11_test")

UA = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36"

URL = "https://www.redbus.in/"

if __name__ == "__main__":
    log.info("========== REDBUS HTTP/1.1 TEST START ==========")
    log.info("Testing RedBus with IPv4 + forced HTTP/1.1")

    try:
        result = subprocess.run(
            [
                "curl", "-4", "--http1.1",
                "-I", "-L",
                "--max-time", "20",
                "-A", UA,
                URL,
            ],
            capture_output=True,
            text=True,
            timeout=25,
        )

        log.info("curl return_code=%s", result.returncode)

        if result.stdout:
            log.info("curl stdout:\n%s", result.stdout[:6000])

        if result.stderr:
            log.info("curl stderr:\n%s", result.stderr[:3000])

    except Exception as e:
        log.exception("TEST FAILED | %s", e)

    log.info("========== REDBUS HTTP/1.1 TEST FINISHED ==========")
