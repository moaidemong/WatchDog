#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
CAMERA_ID="${1:?camera id is required}"

cd "$ROOT"
source .venv/bin/activate

CONFIG_PATH="${WATCHDOG_CONFIG:-configs/app.tapo.multi.example.yaml}"
RUN_DURATION_SECONDS="${WATCHDOG_ONVIF_DURATION_SECONDS:-300}"
COOLDOWN_SECONDS="${WATCHDOG_ONVIF_COOLDOWN_SECONDS:-20}"
PULL_TIMEOUT_SECONDS="${WATCHDOG_ONVIF_PULL_TIMEOUT_SECONDS:-5}"
MESSAGE_LIMIT="${WATCHDOG_ONVIF_MESSAGE_LIMIT:-20}"
LOCK_FILE="${WATCHDOG_PIPELINE_LOCK:-$ROOT/watchdog-onvif-pipeline.lock}"

exec python scripts/run_onvif_gated_pipeline.py \
  --config "$CONFIG_PATH" \
  --camera-id "$CAMERA_ID" \
  --duration-seconds "$RUN_DURATION_SECONDS" \
  --pull-timeout-seconds "$PULL_TIMEOUT_SECONDS" \
  --message-limit "$MESSAGE_LIMIT" \
  --cooldown-seconds "$COOLDOWN_SECONDS" \
  --pipeline-lock-file "$LOCK_FILE"
