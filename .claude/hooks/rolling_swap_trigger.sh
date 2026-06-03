#!/bin/bash
# Rolling Swap Trigger — Stop hook
#
# Fires at the end of every assistant turn. If context is ≥80%
# and no swap has been triggered yet this session, launches
# rolling_swap.sh in its own process group.
#
# Using Stop (not PostToolUse) because at Stop the assistant is
# genuinely idle at the prompt — no thinking indicators, no tool
# execution. This means rolling_swap.sh can send /branch and /exit
# without fighting the thinking-detection logic.
#
# Design: Amy + Nyx, 2026-05-18

CLAP_DIR="$HOME/claude-autonomy-platform"
LOG_FILE="$CLAP_DIR/logs/auto_context_marker.log"
STATUSLINE_DATA="$CLAP_DIR/data/statusline_data.json"
SWAP_FLAG="/tmp/${USER}_rolling_swap_triggered"
SWAP_THRESHOLD=80

# Consume stdin (hook protocol requires reading it)
cat - > /dev/null

# Keep swap_CLAUDE.md warm — always-current conversation context
# so any kind of restart (crash, stale lock, manual) has recent context
python3 "$CLAP_DIR/utils/export_transcript.py" > /dev/null 2>&1 && \
    python3 "$CLAP_DIR/utils/update_conversation_history.py" "$CLAP_DIR/context/current_export.txt" > /dev/null 2>&1

# Already triggered this session?
if [ -f "$SWAP_FLAG" ]; then
    exit 0
fi

# Don't swap if a regular session swap is in progress
if [ -f "/tmp/${USER}_session_swap.lock" ]; then
    exit 0
fi

# Read context percentage
if [ ! -f "$STATUSLINE_DATA" ]; then
    exit 0
fi

USED_PCT=$(python3 -c "
import json
try:
    with open('$STATUSLINE_DATA') as f:
        data = json.load(f)
    print(data.get('context_window', {}).get('used_percentage', 0))
except Exception:
    print(0)
" 2>/dev/null)

# Below threshold
if [ "$USED_PCT" -lt "$SWAP_THRESHOLD" ] 2>/dev/null; then
    exit 0
fi

echo "[$(date -Iseconds)] Context at ${USED_PCT}% — triggering rolling swap (Stop hook)" >> "$LOG_FILE"
echo "triggered=$(date -Iseconds) context=${USED_PCT}%" > "$SWAP_FLAG"

# Launch in its own process group so it survives tmux kill
nohup setsid bash "$CLAP_DIR/utils/rolling_swap.sh" >> "$CLAP_DIR/logs/rolling_swap.log" 2>&1 &

exit 0
