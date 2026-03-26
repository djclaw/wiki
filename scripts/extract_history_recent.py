#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

from extract_history import HISTORY_PATH, OUTPUT_JSON, build_entities, extract_blocks


def filter_recent_history_text(history_text: str, days: int) -> str:
    cutoff = datetime.now() - timedelta(days=days)
    kept = []
    for ts, body in extract_blocks(history_text):
        try:
            dt = datetime.strptime(ts, '%Y-%m-%d %H:%M')
        except ValueError:
            continue
        if dt >= cutoff:
            kept.append(f'[{ts}] {body}')
    return '\n\n'.join(kept)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--output', default=str(OUTPUT_JSON))
    args = parser.parse_args()

    history_text = HISTORY_PATH.read_text(encoding='utf-8')
    filtered = filter_recent_history_text(history_text, args.days)
    items = build_entities(filtered)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(items)} items from last {args.days} days to {out}')


if __name__ == '__main__':
    main()
