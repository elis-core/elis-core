#!/usr/bin/env bash
set -euo pipefail
TEMPORAL_HOME="/home/samurai/temporal"
PID_FILE="$TEMPORAL_HOME/state/dev-server.pid"

if [[ ! -f "$PID_FILE" ]]; then
    echo "No PID file — not tracked as running by this script." >&2
    exit 1
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "Sent SIGTERM to PID $PID."
else
    echo "PID $PID not alive; removing stale PID file." >&2
fi
rm -f "$PID_FILE"
