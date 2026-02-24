import json
from pathlib import Path

SOURCE_DIRS = ["output", "extracted"]
TARGET_ROOT = Path("sampled")

LIMIT = 3


def process_folder(folder_name):
    source_path = Path(folder_name)
    target_path = TARGET_ROOT / folder_name

    target_path.mkdir(parents=True, exist_ok=True)

    for json_file in source_path.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                continue

        if isinstance(data, list):
            sampled = data[:LIMIT]

        elif isinstance(data, dict):
            sampled = dict(list(data.items())[:LIMIT])

        else:
            continue

        output_file = target_path / json_file.name

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sampled, f, indent=2, ensure_ascii=False)

        print(f"Saved → {output_file}")


def main():
    TARGET_ROOT.mkdir(exist_ok=True)

    for folder in SOURCE_DIRS:
        if Path(folder).exists():
            process_folder(folder)

    print("Done")


if __name__ == "__main__":
    main()