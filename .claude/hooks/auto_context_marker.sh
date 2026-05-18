#!/bin/bash
# Auto Context Marker + Rolling Swap Trigger — PostToolUse hook (no matcher)
#
# Two thresholds:
#   50% — Places the rolling-trim checkpoint marker via send_to_claude.sh
#   80% — Triggers a rolling swap (fork → trim → resume) via rolling_swap.sh
#
# The marker is sent once per session (flag file prevents duplicates).
# The swap is triggered once per session (separate flag file).
# Both flags cleared on session swap by on-session-swap.sh.
#
# Design: Amy + Nyx, 2026-05-18

CLAP_DIR="$HOME/claude-autonomy-platform"
LOG_FILE="$CLAP_DIR/logs/auto_context_marker.log"
STATUSLINE_DATA="$CLAP_DIR/data/statusline_data.json"
MARKER_FLAG="/tmp/${USER}_context_marker_placed"
SWAP_FLAG="/tmp/${USER}_rolling_swap_triggered"
MARKER_THRESHOLD=50
SWAP_THRESHOLD=80
MARKER="⟐ CONTEXT SEAM ⟐"

# Consume stdin (hook protocol requires reading it even if unused)
cat - > /dev/null

# If swap already triggered, nothing more to do
if [ -f "$SWAP_FLAG" ]; then
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

# Below marker threshold — nothing to do
if [ "$USED_PCT" -lt "$MARKER_THRESHOLD" ] 2>/dev/null; then
    exit 0
fi

# ─── Swap threshold (80%) ───────────────────────────────────────────

if [ "$USED_PCT" -ge "$SWAP_THRESHOLD" ] 2>/dev/null; then
    # Don't swap if a regular session swap is in progress
    if [ -f "/tmp/${USER}_session_swap.lock" ]; then
        exit 0
    fi

    echo "[$(date -Iseconds)] Context at ${USED_PCT}% — triggering rolling swap" >> "$LOG_FILE"
    echo "triggered=$(date -Iseconds) context=${USED_PCT}%" > "$SWAP_FLAG"

    # Launch rolling swap in its own session so it survives tmux kill
    # setsid puts it in a new process group; nohup protects from SIGHUP
    nohup setsid bash "$CLAP_DIR/utils/rolling_swap.sh" >> "$LOG_FILE" 2>&1 &

    exit 0
fi

# ─── Marker threshold (50%) ─────────────────────────────────────────

if [ -f "$MARKER_FLAG" ]; then
    exit 0
fi

echo "[$(date -Iseconds)] Context at ${USED_PCT}% (threshold ${MARKER_THRESHOLD}%) — placing marker" >> "$LOG_FILE"
echo "placed=$(date -Iseconds) context=${USED_PCT}%" > "$MARKER_FLAG"

# Background the send so the hook returns immediately
(
    source "$CLAP_DIR/utils/send_to_claude.sh"
    send_to_claude "$MARKER"
    echo "[$(date -Iseconds)] Marker sent successfully" >> "$LOG_FILE"
) &

exit 0
