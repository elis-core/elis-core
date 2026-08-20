#!/usr/bin/env bash
# Start the ELIS pre-authoritative Temporal dev server.
# Loopback-only, SQLite-backed, dedicated `elis` namespace, zero root/Docker.
set -euo pipefail

TEMPORAL_HOME="/home/samurai/temporal"
BIN="$TEMPORAL_HOME/bin/temporal"
DB_FILE="$TEMPORAL_HOME/state/temporal.db"
LOG_FILE="$TEMPORAL_HOME/logs/dev-server.log"
PID_FILE="$TEMPORAL_HOME/state/dev-server.pid"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Already running (PID $(cat "$PID_FILE")). Use stop.sh first." >&2
    exit 1
fi

nohup "$BIN" server start-dev \
    --db-filename "$DB_FILE" \
    --ip 127.0.0.1 \
    --ui-ip 127.0.0.1 \
    --port 7233 \
    --ui-port 8233 \
    --namespace elis \
    --log-format json \
    > "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "Started, PID $(cat "$PID_FILE"). Logs: $LOG_FILE"
echo "Frontend: 127.0.0.1:7233   UI: http://127.0.0.1:8233"
