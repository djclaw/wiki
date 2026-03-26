#!/usr/bin/env bash
set -euo pipefail

cd /home/dj/.nanobot/workspace/wiki
export WIKI_EXTRACTION_PROVIDER="${WIKI_EXTRACTION_PROVIDER:-groq}"
export WIKI_EXTRACTION_GROQ_MODEL="${WIKI_EXTRACTION_GROQ_MODEL:-moonshotai/kimi-k2-instruct}"
python scripts/extract_history_recent.py --days 7
python scripts/build_kernel_json.py
python scripts/build_db.py
python scripts/generate_entries_from_db.py
python scripts/build_search_index.py

echo '--- git status ---'
git status --short
