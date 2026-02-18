import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from markdownify import markdownify as md
from pathlib import Path
import json
import time

BASE_URL = "https://perkinswill.gitbook.io/areasync/"
  
MD_DIR = Path("scraped_markdown")
JSON_DIR = Path("scraped_json")

OUTPUT_JSON_FILE = JSON_DIR / "scraped_content.json"

visited = set()
to_visit = {BASE_URL}
pages = []

MD_DIR.mkdir(exist_ok=True)
JSON_DIR.mkdir(exist_ok=True)


def normalize_url(url):
    """Remove fragments & query params for deduplication"""
    parsed = urlparse(url)
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path.rstrip("/"),
        "",
        "",
        ""
    ))

def is_valid_url(url):
    parsed = urlparse(url)
    return (
        parsed.netloc == urlparse(BASE_URL).netloc
        and parsed.scheme in {"http", "https"}
    )


def clean_filename(url):
    path = urlparse(url).path.strip("/")
    if not path:
        return "index.md"
    return path.replace("/", "_") + ".md"

def extract_content(soup):
    main = soup.find("main")

    if not main:
        main = soup.find("div", {"data-testid": "page-content"})

    if not main:
        return None

    for tag in main(["nav", "footer", "script", "style", "button", "svg"]):
        tag.decompose()

    return main


print("\nStarting crawl...\n")

while to_visit:
    raw_url = to_visit.pop()
    url = normalize_url(raw_url)

    if url in visited:
        continue

    visited.add(url)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed: {url} → {e}")
        continue

    soup = BeautifulSoup(response.text, "html.parser")
    content = extract_content(soup)

    if content:
        markdown = md(str(content), heading_style="ATX").strip()
        title = soup.title.string.strip() if soup.title else "No Title"

        filename = clean_filename(url)
        filepath = MD_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(markdown)

        print(f"Saved MD: {filename}")

        pages.append({
            "url": url,
            "title": title,
            "content": markdown
        })

    for link in soup.find_all("a", href=True):
        next_url = normalize_url(urljoin(url, link["href"]))

        if is_valid_url(next_url) and next_url not in visited:
            to_visit.add(next_url)

    time.sleep(0.5)

with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(pages, f, indent=2, ensure_ascii=False)
print("\nScraping complete!")
print(f"Unique pages scraped: {len(visited)}")
print(f"Markdown folder: {MD_DIR.resolve()}")
print(f"JSON folder: {JSON_DIR.resolve()}")
print(f"JSON file: {OUTPUT_JSON_FILE.resolve()}")
