#!/usr/bin/env bash
# Full, clean teardown of the pre-authoritative Temporal dev environment.
# Does NOT touch anything outside /home/samurai/temporal/ — no systemd
# units were created by this deployment (dev server runs as a plain
# background process via start.sh/nohup, not a service), so there is
# nothing to disable/mask, and no root action is required to remove it.
set -euo pipefail
TEMPORAL_HOME="/home/samurai/temporal"

"$TEMPORAL_HOME/deployment/start-dev/stop.sh" || true

read -r -p "This will delete $TEMPORAL_HOME/state/temporal.db (all pre-authoritative workflow history). Back it up first with backup.sh if needed. Type 'yes' to continue: " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted. Nothing removed."
    exit 0
fi

rm -f "$TEMPORAL_HOME/state/temporal.db"
echo "Removed $TEMPORAL_HOME/state/temporal.db. Binary, code, and docs left in place — delete $TEMPORAL_HOME manually for a full removal."
