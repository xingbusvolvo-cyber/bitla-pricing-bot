import logging
import socket
import subprocess
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("redbus_network_test")
UA = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36"

def dns_test(host):
    log.info("========== DNS: %s ==========", host)
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        ips = sorted(set(x[4][0] for x in infos))
        log.info("DNS OK | %s", ips)
    except Exception as e:
        log.error("DNS FAILED | %s", e)

def requests_test(url):
    log.info("========== REQUESTS: %s ==========", url)
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=(10, 10), allow_redirects=True)
        log.info("OK | status=%s | final=%s | bytes=%s", r.status_code, r.url, len(r.content))
    except Exception as e:
        log.error("FAILED | %s: %s", type(e).__name__, e)

def curl_ipv4_test(url):
    log.info("========== CURL IPv4: %s ==========", url)
    try:
        p = subprocess.run(
            ["curl", "-4", "-I", "-L", "--max-time", "15", "-A", UA, url],
            capture_output=True, text=True, timeout=20
        )
        log.info("curl return_code=%s", p.returncode)
        if p.stdout:
            log.info("curl stdout:\n%s", p.stdout[:4000])
        if p.stderr:
            log.info("curl stderr:\n%s", p.stderr[:2000])
    except Exception as e:
        log.error("CURL FAILED | %s", e)

if __name__ == "__main__":
    log.info("========== REDBUS NETWORK DIAGNOSTIC V2 START ==========")
    for host, url in [
        ("www.google.com", "https://www.google.com/"),
        ("example.com", "https://example.com/"),
        ("www.redbus.in", "https://www.redbus.in/"),
    ]:
        dns_test(host)
        requests_test(url)
        curl_ipv4_test(url)
    log.info("========== REDBUS NETWORK DIAGNOSTIC V2 FINISHED ==========")
