#!/usr/bin/env bash
# Idempotent: the `elis` namespace is normally created at server startup via
# `--namespace elis` on start.sh. This script exists for the case where the
# server is already running without it (e.g. someone started the raw binary
# without start.sh) and needs the namespace registered after the fact.
set -euo pipefail
TEMPORAL_HOME="/home/samurai/temporal"
BIN="$TEMPORAL_HOME/bin/temporal"

if "$BIN" operator namespace describe --namespace elis --address 127.0.0.1:7233 >/dev/null 2>&1; then
    echo "Namespace 'elis' already registered."
else
    "$BIN" operator namespace create --namespace elis --address 127.0.0.1:7233
    echo "Namespace 'elis' created."
fi
