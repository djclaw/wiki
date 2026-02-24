#!/usr/bin/env python3
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRIES_DIR = ROOT / "entries"
OUTPUT = ROOT / "data" / "search-index.json"

class EntryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_h1 = False
        self.in_p = False
        self.title = None
        self.first_p = None
        self._buf = []
        self.tags = []
        self.categories = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "article" and attrs_dict.get("class") == "entity":
            tags_raw = attrs_dict.get("data-tags", "")
            categories_raw = attrs_dict.get("data-categories", "")
            self.tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            self.categories = [c.strip() for c in categories_raw.split(",") if c.strip()]
        if tag == "h1":
            self.in_h1 = True
            self._buf = []
        elif tag == "p" and self.first_p is None:
            self.in_p = True
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "h1" and self.in_h1:
            text = "".join(self._buf).strip()
            if text:
                self.title = text
            self.in_h1 = False
        elif tag == "p" and self.in_p:
            text = "".join(self._buf).strip()
            if text:
                self.first_p = text
            self.in_p = False

    def handle_data(self, data):
        if self.in_h1 or self.in_p:
            self._buf.append(data)


def parse_entry(path: Path):
    parser = EntryParser()
    content = path.read_text(encoding="utf-8", errors="ignore")
    parser.feed(content)

    title = parser.title
    if not title:
        m = re.search(r"<title>(.*?)</title>", content, re.I | re.S)
        title = m.group(1).strip() if m else path.stem

    snippet = parser.first_p
    if snippet:
        snippet = re.sub(r"\s+", " ", snippet).strip()

    return {
        "title": title,
        "url": f"entries/{path.name}",
        "snippet": snippet or "",
        "tags": parser.tags,
        "categories": parser.categories,
    }


def main():
    entries = sorted(ENTRIES_DIR.glob("*.html"))
    index = [parse_entry(p) for p in entries]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(index)} entries")


if __name__ == "__main__":
    main()
