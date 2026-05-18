#!/bin/bash
# Auto Context Marker — PostToolUse hook (no matcher)
#
# Checks context usage after every tool use. When usage crosses the
# threshold (default 50%), sends the rolling-trim checkpoint marker
# via send_to_claude.sh so it arrives as a user message.
#
# The marker is sent once per session. A flag file prevents duplicates;
# it's cleared on session swap by on-session-swap.sh.
#
# Design from conversation 2026-05-18 with Amy:
#   "a post-tool-use hook, somewhere around 50% context use,
#    to automatically insert the marker"

CLAP_DIR="$HOME/claude-autonomy-platform"
LOG_FILE="$CLAP_DIR/logs/auto_context_marker.log"
STATUSLINE_DATA="$CLAP_DIR/data/statusline_data.json"
FLAG_FILE="/tmp/${USER}_context_marker_placed"
THRESHOLD=50
MARKER="⟐ CONTEXT SEAM ⟐"

# Consume stdin (hook protocol requires reading it even if unused)
cat - > /dev/null

# Already placed this session?
if [ -f "$FLAG_FILE" ]; then
    exit 0
fi

# Read context percentage from statusline data
if [ ! -f "$STATUSLINE_DATA" ]; then
    echo "[$(date -Iseconds)] No statusline data found" >> "$LOG_FILE"
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
if [ "$USED_PCT" -lt "$THRESHOLD" ] 2>/dev/null; then
    exit 0
fi

# Threshold crossed! Place the marker.
echo "[$(date -Iseconds)] Context at ${USED_PCT}% (threshold ${THRESHOLD}%) — placing marker" >> "$LOG_FILE"

# Create flag file to prevent duplicates
echo "placed=$(date -Iseconds) context=${USED_PCT}%" > "$FLAG_FILE"

# Background the send so the hook returns immediately
# send_to_claude.sh waits for Claude to be idle before delivering
(
    source "$CLAP_DIR/utils/send_to_claude.sh"
    send_to_claude "$MARKER"
    echo "[$(date -Iseconds)] Marker sent successfully" >> "$LOG_FILE"
) &

exit 0
