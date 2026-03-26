#!/usr/bin/env python3
"""
Bridge current extracted entry-shaped JSON into a minimal kernel-shaped JSON.
This does not replace the current pipeline yet.
It creates a second normalized artifact for MVP2/MVP3 evolution.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

INPUT_JSON = Path('/home/dj/.nanobot/workspace/wiki/data/extracted-history.json')
OUTPUT_JSON = Path('/home/dj/.nanobot/workspace/wiki/data/kernel.json')


def slugify(text: str) -> str:
    text = (text or '').strip().lower()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^a-z0-9\-\u4e00-\u9fff]', '', text)
    return text[:80] or 'item'


def uniq_preserve(seq):
    seen = set()
    out = []
    for item in seq or []:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def node_type_from_categories(categories):
    cats = [c.lower() for c in (categories or [])]
    if 'tool' in cats:
        return 'tool'
    if 'project' in cats:
        return 'project'
    return 'topic'


def main():
    items = json.loads(INPUT_JSON.read_text(encoding='utf-8')) if INPUT_JSON.exists() else []

    source_id = 'history_md'
    sources = [{
        'source_id': source_id,
        'source_type': 'history_md',
        'path': '/home/dj/.nanobot/workspace/memory/HISTORY.md',
        'display_name': 'HISTORY.md'
    }]

    evidence = []
    relations = []
    events = []
    seen_rel = set()

    grouped = defaultdict(list)
    for item in items:
        grouped[slugify(item.get('title') or 'Untitled')].append(item)

    nodes = []
    node_index = {}
    for base_slug, bucket in grouped.items():
        primary = bucket[0]
        title = primary.get('title') or 'Untitled'
        aliases = []
        tags = []
        categories = []
        summaries = []
        related_values = []
        timelines = []

        for item in bucket:
            aliases.extend(item.get('aliases') or [])
            tags.extend(item.get('tags') or [])
            categories.extend(item.get('categories') or [])
            if item.get('summary'):
                summaries.append(item.get('summary'))
            related_values.extend(item.get('related') or [])
            timelines.extend(item.get('timeline') or [])

        node = {
            'node_id': base_slug,
            'node_type': node_type_from_categories(categories),
            'title': title,
            'summary': summaries[0] if summaries else '',
            'aliases': uniq_preserve(aliases),
            'tags': uniq_preserve(tags),
            'categories': uniq_preserve(categories),
            'status': 'candidate',
            'visibility': 'review'
        }
        nodes.append(node)
        node_index[base_slug] = {
            'related': uniq_preserve(related_values),
            'timeline': uniq_preserve(timelines),
        }

    for node in nodes:
        node_id = node['node_id']
        detail = node_index[node_id]

        for idx, line in enumerate(detail['timeline'], start=1):
            evidence_id = f'ev-{node_id}-{idx:03d}'
            event_id = f'event-{node_id}-{idx:03d}'
            ts = line[:16] if len(line) >= 16 and line[4] == '-' else None
            evidence.append({
                'evidence_id': evidence_id,
                'source_id': source_id,
                'timestamp': ts,
                'raw_text': line,
                'redacted_text': line,
                'publishable': True,
            })
            events.append({
                'event_id': event_id,
                'timestamp': ts,
                'summary': line,
                'node_ids': [node_id],
                'evidence_id': evidence_id,
                'source_id': source_id,
            })

        for related in detail['related']:
            to_node = slugify(related)
            key = (node_id, to_node, 'related_to')
            if not to_node or to_node == node_id or key in seen_rel:
                continue
            seen_rel.add(key)
            relations.append({
                'relation_id': f'rel-{node_id}-{to_node}-related',
                'from_node': node_id,
                'to_node': to_node,
                'relation_type': 'related_to',
                'weight': 1,
                'evidence_ids': [],
                'status': 'candidate'
            })

    payload = {
        'sources': sources,
        'evidence': evidence,
        'nodes': nodes,
        'relations': relations,
        'events': events,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote kernel JSON to {OUTPUT_JSON}')
    print(json.dumps({
        'sources': len(sources),
        'nodes': len(nodes),
        'relations': len(relations),
        'events': len(events),
        'evidence': len(evidence),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
