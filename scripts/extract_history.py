#!/usr/bin/env python3
"""
Extract stable history entities into extracted-history.json using the canonical
LLM-backed history extraction pipeline (Groq + Kimi by default), then convert
structured candidates into the entry-shaped JSON expected by the current wiki
kernel builder.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from history_extraction import OUTPUT_JSON as STRUCTURED_OUTPUT_JSON
from history_extraction import choose_default_model, load_recent_entries, run_structured_extraction

HISTORY_PATH = Path('/home/dj/.nanobot/workspace/memory/HISTORY.md.bak')
OUTPUT_JSON = Path('/home/dj/.nanobot/workspace/wiki/data/extracted-history.json')

CATEGORY_BY_TYPE = {
    'tool': 'Tool',
    'project': 'Project',
    'place': 'Place',
    'org': 'Organization',
    'person': 'Person',
}


def _load_structured_candidates() -> list[dict]:
    if not STRUCTURED_OUTPUT_JSON.exists():
        return []
    return json.loads(STRUCTURED_OUTPUT_JSON.read_text(encoding='utf-8'))


def _timeline_line(entry: dict, event: dict | None) -> str:
    ts = entry.get('timestamp') or ''
    if event and event.get('summary'):
        return f"{ts} — {event['summary'].strip()}"
    evidence = ((entry.get('evidence') or {}).get('text') or '').strip()
    return f"{ts} — {evidence[:160]}"


def build_entities_from_candidates(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    related_counts: dict[str, defaultdict[str, int]] = {}

    for entry in rows:
        nodes = entry.get('nodes') or []
        events = entry.get('events') or []
        primary_event = events[0] if events else None
        labels_in_entry = []

        for node in nodes:
            title = (node.get('label') or '').strip()
            node_type = (node.get('type') or 'project').strip().lower()
            if not title:
                continue
            labels_in_entry.append(title)
            bucket = grouped.setdefault(title, {
                'title': title,
                'summary_parts': [],
                'timeline': [],
                'tags': [],
                'categories': [CATEGORY_BY_TYPE.get(node_type, 'Project')],
                'aliases': [title.lower()],
                'related': [],
                'source': 'history',
                'source_id': 'history_md',
            })
            line = _timeline_line(entry, primary_event)
            if line not in bucket['timeline']:
                bucket['timeline'].append(line)
            if primary_event and primary_event.get('summary'):
                summary = primary_event['summary'].strip()
                if summary and summary not in bucket['summary_parts']:
                    bucket['summary_parts'].append(summary)

        uniq_labels = []
        seen = set()
        for label in labels_in_entry:
            k = label.lower()
            if k in seen:
                continue
            seen.add(k)
            uniq_labels.append(label)
        for src in uniq_labels:
            rel_bucket = related_counts.setdefault(src, defaultdict(int))
            for dst in uniq_labels:
                if src != dst:
                    rel_bucket[dst] += 1

    items = []
    for title, payload in grouped.items():
        related = [name for name, _ in sorted(related_counts.get(title, {}).items(), key=lambda kv: (-kv[1], kv[0].lower()))[:8]]
        items.append({
            'title': payload['title'],
            'summary': ' / '.join(payload['summary_parts'][:2]),
            'timeline': payload['timeline'][:10],
            'tags': payload['tags'],
            'categories': payload['categories'],
            'aliases': payload['aliases'],
            'related': related,
            'source': payload['source'],
            'source_id': payload['source_id'],
        })

    items.sort(key=lambda x: x['title'].lower())
    return items


def build_entities(days: int = 7, limit: int = 0, provider: str = 'groq', model: str = '') -> list[dict]:
    model = (model or choose_default_model(provider)).strip()
    run_structured_extraction(provider=provider, model=model, days=days, limit=limit)
    rows = _load_structured_candidates()
    return build_entities_from_candidates(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--provider', choices=['gemini', 'groq', 'openai'], default='groq')
    parser.add_argument('--model', default='')
    parser.add_argument('--output', default=str(OUTPUT_JSON))
    args = parser.parse_args()

    _ = load_recent_entries(days=args.days)
    items = build_entities(days=args.days, limit=args.limit, provider=args.provider, model=args.model)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(items)} items to {out}')


if __name__ == '__main__':
    main()
