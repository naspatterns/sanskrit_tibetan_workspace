#!/usr/bin/env bash
# Bulk import all data-NNN.sql chunks to D1 stw-entries.
# Skips chunks with .done marker; safe to re-run after interrupt.
#
# Usage:
#   bash workers/import_all.sh
#
# Free tier 100K writes/day notice: each chunk ~50K rows × 4 writes/row
# (1 table + 2 indexes) = 200K billable writes. If rate-limited, the
# wrangler call returns with non-zero exit. Re-run later.

set -e
cd "$(dirname "$0")"

CHUNKS=$(ls sql/data-*.sql 2>/dev/null | sort)
TOTAL=$(echo "$CHUNKS" | wc -l | tr -d ' ')
DONE=0

for chunk in $CHUNKS; do
    DONE=$((DONE + 1))
    marker="${chunk}.done"
    if [ -f "$marker" ]; then
        echo "[$DONE/$TOTAL] $(basename $chunk) — already imported, skip"
        continue
    fi
    echo "[$DONE/$TOTAL] importing $(basename $chunk)…"
    if wrangler d1 execute stw-entries --remote --file="$chunk" 2>&1 | tail -5; then
        touch "$marker"
        echo "[$DONE/$TOTAL] ✓ done"
    else
        echo "[$DONE/$TOTAL] ✗ FAILED — abort. Re-run to resume."
        exit 1
    fi
done

echo ""
echo "✓ All $TOTAL chunks imported"
