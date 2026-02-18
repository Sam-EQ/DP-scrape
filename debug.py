import json
from pathlib import Path

FILE = Path("output/embedded_chunks.json")

def main():
    if not FILE.exists():
        print("embedded_chunks.json not found")
        return

    with open(FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"\nTotal chunks: {len(chunks)}\n")

    for i, chunk in enumerate(chunks[:5]): 
        print("=" * 80)
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Title   : {chunk['title']}")
        print(f"Tokens  : {chunk['token_count']}")
        print(f"Embed Dim: {len(chunk['embedding']) if chunk['embedding'] else 0}")
        print("\nContent Preview:")
        print(chunk["content"][:300] + "...\n")
        print("Chunk Finished")
if __name__ == "__main__":
    main()
