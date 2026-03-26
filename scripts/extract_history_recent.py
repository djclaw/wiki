#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from extract_history import OUTPUT_JSON, build_entities


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--output', default=str(OUTPUT_JSON))
    args = parser.parse_args()

    items = build_entities(days=args.days, limit=args.limit)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(items)} items from last {args.days} days to {out}')


if __name__ == '__main__':
    main()
