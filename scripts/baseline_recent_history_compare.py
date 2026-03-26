#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

HISTORY_PATH = Path('/home/dj/.nanobot/workspace/memory/HISTORY.md')
OUT_PATH = Path('/home/dj/.nanobot/workspace/wiki/data/extraction-pipeline/baseline-recent-history.json')
ENTRY_RE = re.compile(r'^\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})\]\s*(.*)$')

KEYWORDS = {
    'github pages': 'GitHub Pages',
    'github': 'GitHub',
    'git': 'Git',
    'logseq': 'Logseq',
    'seqlog': 'SeqLog',
    'wiki': 'wiki',
    'trips': 'trips',
    'new orleans': 'New Orleans',
    'new york': 'New York',
    'new jersey': 'New Jersey',
    'airbnb': 'Airbnb',
    'leaflet': 'Leaflet',
    'openstreetmap': 'OpenStreetMap',
    'djclaw': 'DJClaw',
    'lonely planet': 'Lonely Planet',
    'javits center': 'Javits Center',
}


def load_recent(days: int = 7):
    lines = HISTORY_PATH.read_text(encoding='utf-8', errors='ignore').splitlines()
    entries = []
    for line in lines:
        m = ENTRY_RE.match(line)
        if not m:
            continue
        dt = datetime.strptime(m.group(1) + ' ' + m.group(2), '%Y-%m-%d %H:%M')
        entries.append({'timestamp': dt, 'text': line})
    latest = max(x['timestamp'] for x in entries)
    cutoff = latest - timedelta(days=days)
    return [x for x in entries if x['timestamp'] >= cutoff]


def extract_keywords(text: str):
    low = text.lower()
    found = []
    for k, v in KEYWORDS.items():
        if k in low:
            found.append(v)
    return sorted(set(found))


def main():
    rows = []
    counter = Counter()
    for entry in load_recent(7):
        ents = extract_keywords(entry['text'])
        counter.update(ents)
        rows.append({
            'timestamp': entry['timestamp'].isoformat(timespec='minutes'),
            'text': entry['text'],
            'entities': ents,
        })
    payload = {
        'entries': rows,
        'entity_counts': counter.most_common(),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote baseline recent comparison to {OUT_PATH}')


if __name__ == '__main__':
    main()
