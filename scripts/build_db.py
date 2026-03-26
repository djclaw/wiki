#!/usr/bin/env python3
"""
Build a local SQLite DB from kernel-shaped JSON.
This replaces the old entry-table-only build.
DB path is local-only and excluded from git.
"""
import json
import sqlite3
from pathlib import Path

INPUT_JSON = Path('/home/dj/.nanobot/workspace/wiki/data/kernel.json')
DB_PATH = Path('/home/dj/.nanobot/workspace/memory/wiki.db')


def ensure_schema(conn: sqlite3.Connection):
    conn.executescript(
        """
        DROP TABLE IF EXISTS sources;
        DROP TABLE IF EXISTS evidence;
        DROP TABLE IF EXISTS nodes;
        DROP TABLE IF EXISTS relations;
        DROP TABLE IF EXISTS events;
        DROP TABLE IF EXISTS entries;

        CREATE TABLE sources (
            source_id TEXT PRIMARY KEY,
            source_type TEXT,
            path TEXT,
            display_name TEXT,
            ingested_at TEXT
        );

        CREATE TABLE evidence (
            evidence_id TEXT PRIMARY KEY,
            source_id TEXT,
            timestamp TEXT,
            raw_text TEXT,
            redacted_text TEXT,
            publishable INTEGER,
            confidence REAL,
            FOREIGN KEY (source_id) REFERENCES sources(source_id)
        );

        CREATE TABLE nodes (
            node_id TEXT PRIMARY KEY,
            node_type TEXT,
            title TEXT NOT NULL,
            summary TEXT,
            aliases_json TEXT,
            tags_json TEXT,
            categories_json TEXT,
            status TEXT,
            visibility TEXT
        );

        CREATE TABLE relations (
            relation_id TEXT PRIMARY KEY,
            from_node TEXT,
            to_node TEXT,
            relation_type TEXT,
            weight INTEGER,
            evidence_ids_json TEXT,
            status TEXT,
            FOREIGN KEY (from_node) REFERENCES nodes(node_id),
            FOREIGN KEY (to_node) REFERENCES nodes(node_id)
        );

        CREATE TABLE events (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT,
            summary TEXT,
            node_ids_json TEXT,
            evidence_id TEXT,
            source_id TEXT,
            FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id),
            FOREIGN KEY (source_id) REFERENCES sources(source_id)
        );

        CREATE INDEX idx_evidence_source_id ON evidence(source_id);
        CREATE INDEX idx_evidence_timestamp ON evidence(timestamp);
        CREATE INDEX idx_nodes_title ON nodes(title);
        CREATE INDEX idx_nodes_type ON nodes(node_type);
        CREATE INDEX idx_relations_from_node ON relations(from_node);
        CREATE INDEX idx_relations_to_node ON relations(to_node);
        CREATE INDEX idx_events_timestamp ON events(timestamp);
        """
    )
    conn.commit()


def load_payload():
    if not INPUT_JSON.exists():
        return {'sources': [], 'evidence': [], 'nodes': [], 'relations': [], 'events': []}
    return json.loads(INPUT_JSON.read_text(encoding='utf-8'))


def main():
    payload = load_payload()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)

    for row in payload.get('sources', []):
        conn.execute(
            'INSERT INTO sources (source_id, source_type, path, display_name, ingested_at) VALUES (?, ?, ?, ?, ?)',
            (
                row.get('source_id'),
                row.get('source_type'),
                row.get('path'),
                row.get('display_name'),
                row.get('ingested_at'),
            ),
        )

    for row in payload.get('evidence', []):
        conn.execute(
            'INSERT INTO evidence (evidence_id, source_id, timestamp, raw_text, redacted_text, publishable, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                row.get('evidence_id'),
                row.get('source_id'),
                row.get('timestamp'),
                row.get('raw_text'),
                row.get('redacted_text'),
                1 if row.get('publishable') else 0,
                row.get('confidence'),
            ),
        )

    for row in payload.get('nodes', []):
        conn.execute(
            'INSERT INTO nodes (node_id, node_type, title, summary, aliases_json, tags_json, categories_json, status, visibility) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                row.get('node_id'),
                row.get('node_type'),
                row.get('title'),
                row.get('summary'),
                json.dumps(row.get('aliases') or [], ensure_ascii=False),
                json.dumps(row.get('tags') or [], ensure_ascii=False),
                json.dumps(row.get('categories') or [], ensure_ascii=False),
                row.get('status'),
                row.get('visibility'),
            ),
        )

    for row in payload.get('relations', []):
        conn.execute(
            'INSERT INTO relations (relation_id, from_node, to_node, relation_type, weight, evidence_ids_json, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                row.get('relation_id'),
                row.get('from_node'),
                row.get('to_node'),
                row.get('relation_type'),
                row.get('weight'),
                json.dumps(row.get('evidence_ids') or [], ensure_ascii=False),
                row.get('status'),
            ),
        )

    for row in payload.get('events', []):
        conn.execute(
            'INSERT INTO events (event_id, timestamp, summary, node_ids_json, evidence_id, source_id) VALUES (?, ?, ?, ?, ?, ?)',
            (
                row.get('event_id'),
                row.get('timestamp'),
                row.get('summary'),
                json.dumps(row.get('node_ids') or [], ensure_ascii=False),
                row.get('evidence_id'),
                row.get('source_id'),
            ),
        )

    conn.commit()

    counts = {
        'sources': conn.execute('SELECT COUNT(*) FROM sources').fetchone()[0],
        'evidence': conn.execute('SELECT COUNT(*) FROM evidence').fetchone()[0],
        'nodes': conn.execute('SELECT COUNT(*) FROM nodes').fetchone()[0],
        'relations': conn.execute('SELECT COUNT(*) FROM relations').fetchone()[0],
        'events': conn.execute('SELECT COUNT(*) FROM events').fetchone()[0],
    }
    conn.close()
    print(f'Wrote kernel DB to {DB_PATH}')
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
