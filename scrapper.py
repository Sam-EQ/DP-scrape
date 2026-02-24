import requests
import json
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://digitalpractice.perkinswill.com"
API_ROOT = f"{BASE_URL}/wp-json"
API_BASE = f"{API_ROOT}/wp/v2"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

MAX_WORKERS = 5

SAVE_WHITELIST = {
    "posts",
    "pages",
    "media",
    "categories",
    "tags",
    "comments",
    "users",
    "portfolio",
    "docs",
    "portfolio_entities",
    "doc_tag"
}


def discover_endpoints():
    try:
        res = requests.get(API_ROOT, headers=HEADERS)
        if res.status_code != 200:
            logger.error(f"Failed API root → {res.status_code}")
            return []

        routes = res.json().get("routes", {})
        endpoints = set()

        for route in routes:
            if route.startswith("/wp/v2/"):
                parts = route.split("/")
                if len(parts) >= 4:
                    endpoints.add(parts[3])

        endpoints = sorted(endpoints)
        logger.info(f"Discovered → {endpoints}")
        return endpoints

    except Exception as e:
        logger.error(f"Discovery failed → {e}")
        return []


def probe_endpoint(rest_base):
    url = f"{API_BASE}/{rest_base}?per_page=1&page=1"

    try:
        res = requests.get(url, headers=HEADERS)

        if res.status_code == 200:
            logger.info(f"Active → {rest_base}")
            return rest_base

        logger.info(f"Skip → {rest_base} ({res.status_code})")
        return None

    except Exception as e:
        logger.warning(f"Probe failed → {rest_base} → {e}")
        return None


def fetch_endpoint(rest_base):
    page = 1
    items = []

    while True:
        url = f"{API_BASE}/{rest_base}?per_page=100&page={page}"
        logger.info(f"Fetching {rest_base} - Page {page}")

        res = requests.get(url, headers=HEADERS)

        if res.status_code in (400, 404):
            break

        if res.status_code == 403:
            logger.warning(f"Denied → {rest_base}")
            break

        if res.status_code != 200:
            logger.warning(f"Stop {rest_base} → {res.status_code}")
            break

        data = res.json()
        if not data:
            break

        items.extend(data)
        page += 1

    logger.info(f"Done {rest_base} → {len(items)} items")
    return rest_base, items


def main():
    logger.info("Starting WordPress export")

    discovered = discover_endpoints()
    filtered = [ep for ep in discovered if ep in SAVE_WHITELIST]

    logger.info(f"Filtered → {filtered}")

    valid_endpoints = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(probe_endpoint, ep) for ep in filtered]

        for future in as_completed(futures):
            result = future.result()
            if result:
                valid_endpoints.append(result)

    logger.info(f"Valid → {valid_endpoints}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_endpoint, ep) for ep in valid_endpoints]

        for future in as_completed(futures):
            endpoint, data = future.result()

            output_file = OUTPUT_DIR / f"{endpoint}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved → {output_file}")

    logger.info("Export complete")


if __name__ == "__main__":
    main()