#!/usr/bin/env bash
# Real health check — process-alive AND namespace-registered AND UI responds.
# Exits non-zero on any failure, printing which check failed.
set -uo pipefail
TEMPORAL_HOME="/home/samurai/temporal"
BIN="$TEMPORAL_HOME/bin/temporal"

fail() { echo "HEALTH CHECK FAILED: $1" >&2; exit 1; }

ss -tln 2>/dev/null | grep -q "127.0.0.1:7233" || fail "frontend port 7233 not listening on 127.0.0.1"
ss -tln 2>/dev/null | grep -q "127.0.0.1:8233" || fail "UI port 8233 not listening on 127.0.0.1"

"$BIN" operator namespace describe --namespace elis --address 127.0.0.1:7233 >/dev/null 2>&1 \
    || fail "elis namespace not registered / server not responding to gRPC"

UI_STATUS="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8233)"
[[ "$UI_STATUS" == "200" ]] || fail "UI returned HTTP $UI_STATUS, expected 200"

echo "OK: frontend + UI listening on loopback, elis namespace registered, UI returns 200"
