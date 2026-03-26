#!/usr/bin/env bash
set -euo pipefail

cd /home/dj/.nanobot/workspace/wiki
python scripts/extract_history_recent.py --days 7
python scripts/build_kernel_json.py
python scripts/build_db.py
python scripts/generate_entries_from_db.py
python scripts/build_search_index.py

echo '--- git status ---'
git status --short
