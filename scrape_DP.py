import requests
from bs4 import BeautifulSoup
import spacy
from spacy.cli import download
import tiktoken
from math import floor
import json
import logging
from openai import OpenAI
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
 

WP_API_BASE = "https://digitalpractice.perkinswill.com/wp-json/wp/v2/posts"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

PRE_CHUNK_FILE = OUTPUT_DIR / "pre_chunk_documents.json"
CHUNK_FILE = OUTPUT_DIR / "embedded_chunks.json"

TOKENIZER_MODEL = "gpt-4o"
EMBED_MODEL = "text-embedding-3-large"

MAX_TOKENS = 3000
MAX_WORKERS = 10 


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("Downloading SpaCy model...")
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")



def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["style", "script", "noscript"]):
        tag.decompose()

    return soup.get_text(separator=" ", strip=True)


def generate_markdown(post):
    clean_text = clean_html(post["content"]["rendered"])

    markdown = f"""# {post['title']['rendered']}

**Post ID:** {post['id']}  
**Date:** {post['date']}  
**Author:** {post.get('author_info', {}).get('display_name', 'Unknown')}  

---

## Content

{clean_text}
"""
    return markdown, clean_text


def splitter(text: str, max_tokens: int = MAX_TOKENS, overlap_tokens: int = None):
    if overlap_tokens is None:
        overlap_tokens = floor(max_tokens * 0.2)

    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]

    if not sentences:
        return []

    enc = tiktoken.encoding_for_model(TOKENIZER_MODEL)
    token_counts = [len(enc.encode(s)) for s in sentences]

    chunks = []
    start = 0

    while start < len(sentences):
        end = start
        token_acc = 0

        while end < len(sentences):
            if token_acc + token_counts[end] <= max_tokens:
                token_acc += token_counts[end]
                end += 1
            else:
                break

        if end == start:
            chunks.append(sentences[start])
            start += 1
            continue

        chunks.append(" ".join(sentences[start:end]))
        start = end

    return chunks


def generate_embedding(text):
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return response.data[0].embedding



def fetch_all_posts():
    page = 1
    posts = []

    while True:
        url = f"{WP_API_BASE}?per_page=100&page={page}"
        logger.info(f"Fetching page {page}...")

        res = requests.get(url, headers=HEADERS)

        if res.status_code != 200:
            logger.warning(f"Stopping pagination → Status {res.status_code}")
            break

        data = res.json()

        if not data:
            break

        posts.extend(data)
        page += 1

    logger.info(f"Total posts fetched: {len(posts)}")
    return posts



def embed_chunk(chunk):
    try:
        embedding = generate_embedding(chunk["content"])
        chunk["embedding"] = embedding
    except Exception as e:
        logger.error(f"Embedding failed → {chunk['chunk_id']} → {e}")
        chunk["embedding"] = None

    return chunk


def main():
    try:
        enc = tiktoken.encoding_for_model(TOKENIZER_MODEL)
        posts = fetch_all_posts()

        pre_chunk_docs = []
        chunk_jobs = []

        for post in posts:
            logger.info(f"Processing → {post['title']['rendered']}")

            markdown, clean_text = generate_markdown(post)

            pre_chunk_docs.append({
                "post_id": post["id"],
                "title": post["title"]["rendered"],
                "date": post["date"],
                "author": post.get("author_info", {}).get("display_name"),
                "content_raw": clean_text,
                "content_markdown": markdown
            })

            chunks = splitter(markdown)

            for i, chunk_text in enumerate(chunks):
                chunk_jobs.append({
                    "chunk_id": f"{post['id']}_{i}",
                    "post_id": post["id"],
                    "title": post["title"]["rendered"],
                    "date": post["date"],
                    "author": post.get("author_info", {}).get("display_name"),
                    "content": chunk_text,
                    "token_count": len(enc.encode(chunk_text)),
                    "embedding": None
                })

        logger.info(f"\nTotal chunks to embed: {len(chunk_jobs)}")

        embedded_chunks = []

        logger.info(f"Generating embeddings with {MAX_WORKERS} workers...")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(embed_chunk, chunk) for chunk in chunk_jobs]

            for future in as_completed(futures):
                embedded_chunks.append(future.result())

        embedded_chunks.sort(key=lambda x: x["chunk_id"])

        with open(PRE_CHUNK_FILE, "w", encoding="utf-8") as f:
            json.dump(pre_chunk_docs, f, indent=2)

        logger.info(f"Saved → {PRE_CHUNK_FILE}")

        with open(CHUNK_FILE, "w", encoding="utf-8") as f:
            json.dump(embedded_chunks, f, indent=2)

        logger.info(f"Saved → {CHUNK_FILE}")

        logger.info("\nPipeline Complete")

    except Exception as e:
        logger.error(f"Pipeline failed → {e}")


if __name__ == "__main__":
    main()
