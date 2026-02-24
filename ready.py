import json
from pathlib import Path
from bs4 import BeautifulSoup

WP_OUTPUT = Path("output/")
WP_EXTRACTED = Path("extracted/")

def clean_html(html):
    soup = BeautifulSoup(html or "", "html.parser")
    return soup.get_text(separator=" ", strip=True)

def load(path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

users_map = load(WP_EXTRACTED / "users.json") or {}
media_map = load(WP_EXTRACTED / "Media.json") or {}
categories_map = load(WP_EXTRACTED / "Categories.json") or {}
tags_map = load(WP_EXTRACTED / "Tags.json") or {}
docs_map = load(WP_EXTRACTED / "Docs.json") or {}
comments_map = load(WP_EXTRACTED / "Comments.json") or {}

posts = load(WP_OUTPUT / "posts.json") or []
pages = load(WP_OUTPUT / "pages.json") or []
portfolio = load(WP_OUTPUT / "portfolio.json") or []

rag_docs = []

def resolve_common_fields(item, item_type):
    author_id = str(item.get("author"))
    media_id = str(item.get("featured_media"))

    return {
        "doc_id": f"{item_type}_{item.get('id')}",
        "type": item_type,
        "title": clean_html(item.get("title", {}).get("rendered")),
        "url": item.get("link"),
        "slug": item.get("slug"),
        "published": item.get("date"),

        "author": users_map.get(author_id),

        "featured_media": media_map.get(media_id),

        "categories": [
            categories_map.get(str(cat_id))
            for cat_id in item.get("categories", [])
        ] if "categories" in item else [],

        "tags": [
            tags_map.get(str(tag_id))
            for tag_id in item.get("tags", [])
        ] if "tags" in item else [],

        "content": clean_html(item.get("content", {}).get("rendered")),

        "comments": [
            c.get("content")
            for c in comments_map.get(item.get("id"), [])
        ] if comments_map else []
    }

for post in posts:
    rag_docs.append(resolve_common_fields(post, "post"))

for page in pages:
    rag_docs.append(resolve_common_fields(page, "page"))

for p in portfolio:
    rag_docs.append(resolve_common_fields(p, "portfolio"))

for doc_id, doc in docs_map.items():
    rag_docs.append({
        "doc_id": f"docs_{doc_id}",
        "type": "docs",
        "title": clean_html(doc.get("title")),
        "url": doc.get("url"),
        "slug": doc.get("slug"),
        "published": doc.get("createdAt"),
        "author": None,
        "featured_media": None,
        "categories": [],
        "tags": [],
        "content": doc.get("content"),
        "comments": [
            c.get("content")
            for c in comments_map.get(int(doc_id), [])
        ] if comments_map else []
    })

OUTPUT_PATH = Path("sampled/rag_documents.json")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(rag_docs, f, indent=2, ensure_ascii=False)