#!/usr/bin/env python3
"""
Extracts candidate entries from HISTORY.md into a JSON list.
This is a minimal placeholder for MVP3; logic can be expanded later.
"""
import json
import re
from pathlib import Path

HISTORY_PATH = Path("/home/dj/.nanobot/workspace/memory/HISTORY.md")
OUTPUT_JSON = Path("/home/dj/.nanobot/workspace/wiki/data/extracted-history.json")


def extract_lines(history_text: str):
    # Paragraph-based placeholder: split by blank lines, parse timestamped blocks
    items = []
    blocks = re.split(r"\n\s*\n", history_text.strip())
    ts_pattern = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s*(.*)")
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("#"):
            continue
        first_line = block.splitlines()[0].strip()
        match = ts_pattern.match(first_line)
        if not match:
            continue
        _, rest = match.groups()
        summary = block
        title = (rest or summary).strip()
        if not title:
            continue
        items.append({
            "title": title[:80],
            "summary": summary,
            "source": "history",
            "source_id": "history_md"
        })
    return items


def main():
    history_text = HISTORY_PATH.read_text(encoding="utf-8")
    items = extract_lines(history_text)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(items)} items to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
