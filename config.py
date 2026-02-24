import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://digitalpractice.perkinswill.com"
WP_JSON = f"{BASE_URL}/wp-json"
API_BASE = f"{BASE_URL}/wp-json/wp/v2"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
CHUNK_DIR = DATA_DIR / "chunks"

RAW_DIR.mkdir(parents=True, exist_ok=True)
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

TOKENIZER_MODEL = "gpt-4o"
EMBED_MODEL = "text-embedding-3-large"

MAX_TOKENS = 800
OVERLAP_TOKENS = 150
BATCH_SIZE = 50