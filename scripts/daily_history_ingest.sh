#!/usr/bin/env bash
set -euo pipefail

WIKI_DIR="/home/dj/.nanobot/workspace/wiki"
HISTORY_FILE="/home/dj/.nanobot/workspace/memory/HISTORY.md"
STATE_DIR="$WIKI_DIR/data/state"
LAST_SHA_FILE="$STATE_DIR/last_history_sha.txt"
LAST_SUCCESS_FILE="$STATE_DIR/last_daily_refresh_success.json"
LOG_FILE="$WIKI_DIR/data/daily-refresh.log"
RUN_TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
LOCAL_DAY="$(TZ=America/New_York date +"%Y-%m-%d")"

mkdir -p "$STATE_DIR"
touch "$LOG_FILE"

log() {
  echo "[$RUN_TS] $*" | tee -a "$LOG_FILE"
}

current_sha="$(sha256sum "$HISTORY_FILE" | awk '{print $1}')"
previous_sha=""
if [[ -f "$LAST_SHA_FILE" ]]; then
  previous_sha="$(cat "$LAST_SHA_FILE")"
fi

if [[ "$current_sha" == "$previous_sha" ]]; then
  log "No new HISTORY.md content. Skipping refresh."
  exit 0
fi

cd "$WIKI_DIR"
log "New HISTORY.md content detected. Starting wiki refresh."

bash scripts/run_recent_daily_refresh.sh | tee -a "$LOG_FILE"

if git diff --quiet && git diff --cached --quiet; then
  log "Refresh completed but produced no git changes. Recording new HISTORY state."
  printf '%s\n' "$current_sha" > "$LAST_SHA_FILE"
  python - <<'PY'
from pathlib import Path
import json
from datetime import datetime
path = Path('/home/dj/.nanobot/workspace/wiki/data/state/last_daily_refresh_success.json')
payload = {
    'status': 'no_git_changes',
    'history_sha_recorded_at': datetime.utcnow().isoformat() + 'Z'
}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY
  exit 0
fi

git add data/extracted-history.json data/kernel.json data/search-index.json entries/history scripts/generate_entries_from_db.py scripts/run_recent_daily_refresh.sh scripts/daily_history_ingest.sh

if git diff --cached --quiet; then
  log "Nothing staged after git add. Recording new HISTORY state."
  printf '%s\n' "$current_sha" > "$LAST_SHA_FILE"
  python - <<'PY'
from pathlib import Path
import json
from datetime import datetime
path = Path('/home/dj/.nanobot/workspace/wiki/data/state/last_daily_refresh_success.json')
payload = {
    'status': 'nothing_staged',
    'history_sha_recorded_at': datetime.utcnow().isoformat() + 'Z'
}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY
  exit 0
fi

commit_msg="Daily wiki refresh from HISTORY.md: $LOCAL_DAY"
git commit -m "$commit_msg" | tee -a "$LOG_FILE"
git push origin main | tee -a "$LOG_FILE"

printf '%s\n' "$current_sha" > "$LAST_SHA_FILE"
python - <<'PY'
from pathlib import Path
import json
from datetime import datetime
path = Path('/home/dj/.nanobot/workspace/wiki/data/state/last_daily_refresh_success.json')
payload = {
    'status': 'pushed',
    'history_sha_recorded_at': datetime.utcnow().isoformat() + 'Z',
    'last_push_branch': 'main'
}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY

log "Daily wiki refresh finished and pushed successfully."
