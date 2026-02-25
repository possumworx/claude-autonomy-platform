#!/bin/bash
# Collaborative Mode Hook - UserPromptSubmit
# Detects when a human sends start/end trigger words via Remote Control
# Sets/clears a flag file that the autonomous timer checks
#
# Each Claude has personalised trigger words in their config.
# Amy learns them all - like a password for each hearth.

# Ensure PATH is set (hooks may run with minimal environment)
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

CLAP_DIR="$HOME/claude-autonomy-platform"
LOG_FILE="$CLAP_DIR/logs/collaborative_mode.log"

# Debug: log that hook was called
echo "[$(date)] Hook invoked" >> "$LOG_FILE"

source "$CLAP_DIR/config/claude_env.sh"

LINUX_USER=$(read_config "LINUX_USER" 2>/dev/null || echo "$USER")
COLLABORATIVE_START=$(read_config "COLLABORATIVE_START" 2>/dev/null || echo "")
COLLABORATIVE_END=$(read_config "COLLABORATIVE_END" 2>/dev/null || echo "")
FLAG_FILE="/tmp/${LINUX_USER}_collaborative_mode"

# Debug: log config values
echo "[$(date)] LINUX_USER=$LINUX_USER START=$COLLABORATIVE_START END=$COLLABORATIVE_END" >> "$LOG_FILE"

# Capture stdin first, then process
RAW_INPUT=$(cat -)
echo "[$(date)] RAW_INPUT: $RAW_INPUT" >> "$LOG_FILE"

# The prompt comes via stdin as JSON from Claude Code
PROMPT=$(echo "$RAW_INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('prompt', '').strip())
except Exception as e:
    print('')
" 2>/dev/null)

echo "[$(date)] PARSED_PROMPT: $PROMPT" >> "$LOG_FILE"

# Check for trigger words (case-insensitive, exact match)
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')
START_LOWER=$(echo "$COLLABORATIVE_START" | tr '[:upper:]' '[:lower:]')
END_LOWER=$(echo "$COLLABORATIVE_END" | tr '[:upper:]' '[:lower:]')

if [[ -n "$START_LOWER" && "$PROMPT_LOWER" == "$START_LOWER" ]]; then
    touch "$FLAG_FILE"
    echo "[COLLAB] Collaborative mode activated by trigger word" >> "$CLAP_DIR/logs/collaborative_mode.log" 2>/dev/null
elif [[ -n "$END_LOWER" && "$PROMPT_LOWER" == "$END_LOWER" ]]; then
    rm -f "$FLAG_FILE"
    echo "[COLLAB] Collaborative mode deactivated by trigger word" >> "$CLAP_DIR/logs/collaborative_mode.log" 2>/dev/null
fi
