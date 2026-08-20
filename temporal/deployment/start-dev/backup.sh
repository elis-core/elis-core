#!/usr/bin/env bash
# Follows this host's existing timestamped-snapshot-before-risky-change
# convention (see /home/samurai/.hermes/backups/, kanban.db.backup.<ts>-<label>).
set -euo pipefail
TEMPORAL_HOME="/home/samurai/temporal"
DB_FILE="$TEMPORAL_HOME/state/temporal.db"
BACKUP_DIR="$TEMPORAL_HOME/backups"
TS="$(date +%Y%m%d-%H%M%S)"
LABEL="${1:-manual}"

if [[ ! -f "$DB_FILE" ]]; then
    echo "No persistence file at $DB_FILE yet — nothing to back up." >&2
    exit 1
fi

DEST="$BACKUP_DIR/temporal.db.backup.${TS}-${LABEL}"
cp "$DB_FILE" "$DEST"
echo "Backed up to $DEST"
