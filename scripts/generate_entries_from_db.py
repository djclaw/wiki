#!/usr/bin/env python3
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/home/dj/.nanobot/workspace/memory/wiki.db")
OUTPUT_DIR = Path("/home/dj/.nanobot/workspace/wiki/entries/history")
TEMPLATES_DIR = Path("/home/dj/.nanobot/workspace/wiki/templates")
LIMIT = 50


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9\-\u4e00-\u9fff]", "", text)
    return text[:60] or "entry"


def load_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def build_infobox_rows(entry):
    rows = []
    rows.append(f"<dt>Source</dt><dd>{entry['source']}</dd>")
    rows.append(f"<dt>Source ID</dt><dd>{entry['source_id']}</dd>")
    if entry.get("created_at"):
        rows.append(f"<dt>Created</dt><dd>{entry['created_at']}</dd>")
    categories = entry.get("categories", [])
    if categories:
        rows.append(f"<dt>Category</dt><dd>{', '.join(categories)}</dd>")
    return "\n".join(rows)


def build_sections(entry):
    summary = entry.get("summary", "").strip()
    if not summary:
        summary = "(No summary yet.)"

    timeline = entry.get("timeline", [])
    timeline_items = []
    for item in timeline:
        timeline_items.append(f"<li>{item}</li>")
    if not timeline_items:
        timeline_items.append("<li>(No events yet.)</li>")

    related = entry.get("related", [])
    related_items = []
    for item in related:
        related_items.append(f"<li>{item}</li>")
    if not related_items:
        related_items.append("<li>(No related entries yet.)</li>")

    sections = [
        "<section id=\"summary\">",
        "<h2>Overview</h2>",
        f"<p>{summary}</p>",
        "</section>",
        "<section id=\"timeline\">",
        "<h2>Timeline</h2>",
        "<ul>",
        *timeline_items,
        "</ul>",
        "</section>",
        "<section id=\"related\">",
        "<h2>Related</h2>",
        "<ul>",
        *related_items,
        "</ul>",
        "</section>",
    ]
    return "\n".join(sections)


def build_toc_items():
    return "".join(
        [
            "<li><a href=\"#summary\">Overview</a></li>",
            "<li><a href=\"#timeline\">Timeline</a></li>",
            "<li><a href=\"#related\">Related</a></li>",
        ]
    )


def render_entity(entry):
    entity_tpl = load_template("entity.html")
    infobox_rows = build_infobox_rows(entry)
    toc_items = build_toc_items()
    sections = build_sections(entry)
    entity = entity_tpl
    entity = entity.replace("{{title}}", entry["title"])
    entity = entity.replace("{{summary}}", entry.get("summary", "") or "")
    entity = entity.replace("{{infobox_rows}}", infobox_rows)
    entity = entity.replace("{{toc_items}}", toc_items)
    entity = entity.replace("{{sections}}", sections)
    return entity


def render_page(title: str, content: str):
    layout = load_template("layout.html")
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    page = layout.replace("{{title}}", title)
    page = page.replace("{{content}}", content)
    page = page.replace("{{updated_at}}", updated_at)
    return page


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, title, summary, timeline, categories, related, source, source_id FROM entries ORDER BY id LIMIT ?",
        (LIMIT,),
    ).fetchall()
    conn.close()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for idx, row in enumerate(rows, start=1):
        title = row["title"]
        entry = dict(row)
        entry["created_at"] = None
        entry["timeline"] = json.loads(entry.get("timeline") or "[]")
        entry["categories"] = json.loads(entry.get("categories") or "[]")
        entry["related"] = json.loads(entry.get("related") or "[]")
        entity_html = render_entity(entry)
        full_page = render_page(title, entity_html)

        filename = f"history-{idx:04d}.html"
        (OUTPUT_DIR / filename).write_text(full_page, encoding="utf-8")

    print(f"Generated {len(rows)} history entries in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
