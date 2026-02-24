import json
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

OUTPUT_DIR = Path("output")
EXTRACTED_DIR = Path("extracted")


def load_json(name):
    path = OUTPUT_DIR / f"{name}.json"
    if not path.exists():
        print(f"[WARN] Missing {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_html(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def ensure_output_dir():
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


categories = load_json("categories")
comments = load_json("comments")
docs = load_json("docs")
media = load_json("media")
portfolio = load_json("portfolio")
posts = load_json("posts")
tags = load_json("tags")
users = load_json("users")


users_map = {
    user["id"]: {
        "name": user.get("name"),
        "url": user.get("link"),
        "slug": user.get("slug"),
        "description": user.get("description"),
    }
    for user in users
}

media_map = {
    item["id"]: {
        "title": item.get("title", {}).get("rendered"),
        "url": item.get("source_url"),
        "slug": item.get("slug"),
        "type": item.get("media_type"),
        "mimeType": item.get("mime_type"),
    }
    for item in media
}

docs_map = {
    doc["id"]: {
        "title": doc.get("title", {}).get("rendered"),
        "url": doc.get("link"),
        "slug": doc.get("slug"),
        "content": clean_html(doc.get("content", {}).get("rendered")),
        "createdAt": doc.get("date"),
        "modifiedAt": doc.get("modified"),
        "status": doc.get("status"),
        "type": doc.get("type"),
    }
    for doc in docs
}

categories_map = {
    category["id"]: category.get("name")
    for category in categories
}

tags_map = {
    tag["id"]: tag.get("name", "").lstrip("+")
    for tag in tags
}


comments_sorted = sorted(
    comments,
    key=lambda x: datetime.fromisoformat(x["date"]),
    reverse=True
)

comments_map = {}

for comment in comments_sorted:
    post_id = comment.get("post")
    parent_id = comment.get("parent")

    comments_map.setdefault(post_id, [])

    comment_obj = {
        "id": comment.get("id"),
        "content": clean_html(comment.get("content", {}).get("rendered")),
        "author": users_map.get(comment.get("author")),
        "date": comment.get("date"),
        "status": comment.get("status"),
    }

    if not parent_id:
        comments_map[post_id].append(comment_obj)
    else:
        for parent_comment in comments_map[post_id]:
            if parent_comment["id"] == parent_id:
                parent_comment.setdefault("replies", []).append(comment_obj)
                break

ensure_output_dir()

with open(EXTRACTED_DIR / "users.json", "w", encoding="utf-8") as f:
    json.dump(users_map, f, indent=4, ensure_ascii=False)

with open(EXTRACTED_DIR / "Media.json", "w", encoding="utf-8") as f:
    json.dump(media_map, f, indent=4, ensure_ascii=False)

with open(EXTRACTED_DIR / "Docs.json", "w", encoding="utf-8") as f:
    json.dump(docs_map, f, indent=4, ensure_ascii=False)

with open(EXTRACTED_DIR / "Categories.json", "w", encoding="utf-8") as f:
    json.dump(categories_map, f, indent=4, ensure_ascii=False)

with open(EXTRACTED_DIR / "Tags.json", "w", encoding="utf-8") as f:
    json.dump(tags_map, f, indent=4, ensure_ascii=False)

with open(EXTRACTED_DIR / "Comments.json", "w", encoding="utf-8") as f:
    json.dump(comments_map, f, indent=4, ensure_ascii=False)

print("\nExtraction completed successfully.")