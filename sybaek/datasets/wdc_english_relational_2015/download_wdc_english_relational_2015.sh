#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOWNLOAD_DIR="$ROOT/downloads"
LOG_DIR="$ROOT/logs"
BASE_URL="https://data.dws.informatik.uni-mannheim.de/webtables/2015-07/englishCorpus/compressed"

mkdir -p "$DOWNLOAD_DIR" "$LOG_DIR"

echo "[$(date '+%F %T')] initial backoff before contacting WDC server"
sleep "${WDC_INITIAL_BACKOFF_SECONDS:-600}"

for idx in $(seq -w 0 50); do
  file="${idx}.tar.gz"
  echo "[$(date '+%F %T')] downloading $file"
  curl -L --fail --retry 999 --retry-all-errors --retry-delay 120 --connect-timeout 30 \
    --speed-limit 1024 --speed-time 300 \
    --limit-rate "${WDC_LIMIT_RATE:-20M}" \
    -C - \
    -o "$DOWNLOAD_DIR/$file" \
    "$BASE_URL/$file"
  sleep "${WDC_BETWEEN_FILES_SECONDS:-10}"
done
