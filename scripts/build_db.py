#!/usr/bin/env python3
"""
Builds a local SQLite DB from extracted JSON.
DB path is local-only and excluded from git.
"""
import json
import sqlite3
from pathlib import Path

INPUT_JSON = Path("/home/dj/.nanobot/workspace/wiki/data/extracted-history.json")
DB_PATH = Path("/home/dj/.nanobot/workspace/memory/wiki.db")


def ensure_schema(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            timeline TEXT,
            tags TEXT,
            categories TEXT,
            aliases TEXT,
            related TEXT,
            source TEXT,
            source_id TEXT
        )
        """
    )
    conn.commit()


def load_items():
    if not INPUT_JSON.exists():
        return []
    return json.loads(INPUT_JSON.read_text(encoding="utf-8"))


def main():
    items = load_items()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)

    conn.execute("DELETE FROM entries")
    for it in items:
        conn.execute(
            """
            INSERT INTO entries (title, summary, timeline, tags, categories, aliases, related, source, source_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                it.get("title"),
                it.get("summary"),
                json.dumps(it.get("timeline") or [], ensure_ascii=False),
                json.dumps(it.get("tags") or [], ensure_ascii=False),
                json.dumps(it.get("categories") or [], ensure_ascii=False),
                json.dumps(it.get("aliases") or [], ensure_ascii=False),
                json.dumps(it.get("related") or [], ensure_ascii=False),
                it.get("source"),
                it.get("source_id"),
            ),
        )
    conn.commit()
    conn.close()
    print(f"Wrote {len(items)} entries to {DB_PATH}")


if __name__ == "__main__":
    main()
