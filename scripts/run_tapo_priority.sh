#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
LOOP=0
SLEEP_SECONDS=5

while (($# > 0)); do
  case "$1" in
    --loop)
      LOOP=1
      shift
      ;;
    --sleep-seconds)
      SLEEP_SECONDS="$2"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

CONFIG="${1:-configs/app.tapo.multi.example.yaml}"
if (($# > 0)); then
  shift
fi

CAMERAS=("$@")

if [ "${#CAMERAS[@]}" -eq 0 ]; then
  CAMERAS=(b c a)
fi

cd "$ROOT"
source .venv/bin/activate

run_cycle() {
  for camera_id in "${CAMERAS[@]}"; do
    echo "==> running pipeline for camera ${camera_id}"
    python scripts/run_pipeline.py --config "$CONFIG" --camera-id "$camera_id"
  done
}

if ((LOOP == 1)); then
  while true; do
    run_cycle
    sleep "$SLEEP_SECONDS"
  done
else
  run_cycle
fi
