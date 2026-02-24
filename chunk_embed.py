import json
import logging
import tiktoken
from openai import OpenAI
from config import RAW_DIR, CHUNK_DIR, TOKENIZER_MODEL, EMBED_MODEL, MAX_TOKENS, OVERLAP_TOKENS, BATCH_SIZE, OPENAI_API_KEY
from utils import clean_html, hash_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

def chunk_text(text: str):
    enc = tiktoken.encoding_for_model(TOKENIZER_MODEL)
    tokens = enc.encode(text)

    chunks = []
    start = 0

    while start < len(tokens):
        end = start + MAX_TOKENS
        chunk_tokens = tokens[start:end]
        chunks.append(enc.decode(chunk_tokens))
        start += MAX_TOKENS - OVERLAP_TOKENS

    return chunks

def embed_batch(texts):
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    )
    return [d.embedding for d in response.data]

def extract_text(item):
    return (
        item.get("content", {}).get("rendered")
        or item.get("description", {}).get("rendered")
        or item.get("excerpt", {}).get("rendered")
        or ""
    )

def main():
    all_chunks = []
    seen_hashes = set()

    raw_files = RAW_DIR.glob("*.json")

    for raw_file in raw_files:
        endpoint = raw_file.stem
        logger.info(f"Processing → {endpoint}")

        with open(raw_file, "r", encoding="utf-8") as f:
            items = json.load(f)

        for item in items:
            html = extract_text(item)
            text = clean_html(html)

            if not text.strip():
                continue

            chunks = chunk_text(text)

            for i, chunk in enumerate(chunks):
                h = hash_text(chunk)
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)

                all_chunks.append({
                    "chunk_id": f"{endpoint}_{item.get('id')}_{i}",
                    "endpoint": endpoint,
                    "item_id": item.get("id"),
                    "content": chunk,
                    "embedding": None
                })

    logger.info(f"Total chunks → {len(all_chunks)}")

    # Embed in batches
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i:i+BATCH_SIZE]
        texts = [c["content"] for c in batch]

        embeddings = embed_batch(texts)

        for chunk, emb in zip(batch, embeddings):
            chunk["embedding"] = emb

        logger.info(f"Embedded batch {i // BATCH_SIZE + 1}")

    path = CHUNK_DIR / "embedded_chunks.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    logger.info(f"Saved → {path}")
    logger.info("chunk + Embed complete")


if __name__ == "__main__":
    main()