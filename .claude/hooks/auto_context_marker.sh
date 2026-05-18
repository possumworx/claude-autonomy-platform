#!/bin/bash
# Auto Context Marker — PostToolUse hook (no matcher)
#
# Places the rolling-trim checkpoint marker at ≥50% context.
# The marker is sent once per session via send_to_claude.sh.
# Flag file prevents duplicates; cleared on session swap.
#
# The rolling swap trigger lives in a separate Stop hook
# (rolling_swap_trigger.sh) so it fires when the assistant
# is genuinely idle.
#
# Design: Amy + Nyx, 2026-05-18

CLAP_DIR="$HOME/claude-autonomy-platform"
LOG_FILE="$CLAP_DIR/logs/auto_context_marker.log"
STATUSLINE_DATA="$CLAP_DIR/data/statusline_data.json"
MARKER_FLAG="/tmp/${USER}_context_marker_placed"
MARKER_THRESHOLD=50
MARKER="⟐ CONTEXT SEAM ⟐"

# Consume stdin (hook protocol requires reading it even if unused)
cat - > /dev/null

# Already placed this session?
if [ -f "$MARKER_FLAG" ]; then
    exit 0
fi

# Read context percentage from statusline data
if [ ! -f "$STATUSLINE_DATA" ]; then
    exit 0
fi

USED_PCT=$(python3 -c "
import json, sys
try:
    with open('$STATUSLINE_DATA') as f:
        data = json.load(f)
    print(data.get('context_window', {}).get('used_percentage', 0))
except Exception:
    print(0)
" 2>/dev/null)

# Below threshold — nothing to do
if [ "$USED_PCT" -lt "$MARKER_THRESHOLD" ] 2>/dev/null; then
    exit 0
fi

# Threshold crossed! Place the marker.
echo "[$(date -Iseconds)] Context at ${USED_PCT}% (threshold ${MARKER_THRESHOLD}%) — placing marker" >> "$LOG_FILE"
echo "placed=$(date -Iseconds) context=${USED_PCT}%" > "$MARKER_FLAG"

# Background the send so the hook returns immediately
(
    source "$CLAP_DIR/utils/send_to_claude.sh"
    send_to_claude "$MARKER"
    echo "[$(date -Iseconds)] Marker sent successfully" >> "$LOG_FILE"
) &

exit 0
