#!/bin/sh
set -eu

: "${CODEX_API_KEY:?CODEX_API_KEY is required}"
: "${CODEX_REMOTE_URL:?CODEX_REMOTE_URL is required}"
: "${CODEX_ENVIRONMENT_ID:?CODEX_ENVIRONMENT_ID is required}"

case "$CODEX_REMOTE_URL" in
  wss://*) ;;
  *) echo "CODEX_REMOTE_URL must use wss://" >&2; exit 2 ;;
esac

exec codex exec-server \
  --remote "$CODEX_REMOTE_URL" \
  --environment-id "$CODEX_ENVIRONMENT_ID"
