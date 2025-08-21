#!/bin/bash
# Reusable wait function for Claude readiness
# Uses color-based detection to ensure Claude is not thinking

TMUX_SESSION="${CLAUDE_SESSION:-autonomous-claude}"
MAX_WAIT="${1:-30}"  # Default 30 seconds
OPERATION="${2:-operation}"  # What we're waiting for

echo "[WAIT] Waiting for Claude to be ready for: $OPERATION (max ${MAX_WAIT}s)"

# Get the Claude pane
claude_pane=$(tmux list-panes -t "$TMUX_SESSION" -F '#{pane_id}' 2>/dev/null | head -1)

if [ -z "$claude_pane" ]; then
    echo "[WAIT] ERROR: Could not find Claude pane"
    exit 1
fi

count=0
while [ $count -lt $MAX_WAIT ]; do
    # Capture with ANSI escape codes
    pane_content=$(tmux capture-pane -t "$claude_pane" -p -e -S -10)
    
    # Check for orange-red thinking indicators
    if echo "$pane_content" | grep -q '\[38;5;174m.*…'; then
        echo "[WAIT] Claude is thinking... (${count}s)"
        sleep 1
        ((count++))
        continue
    fi
    
    # Check for animated indicators with color
    if echo "$pane_content" | grep -E '\[38;5;174m[[:space:]]*[.+*❄✿✶]' | grep -v 'tokens'; then
        echo "[WAIT] Claude is thinking... (${count}s)"
        sleep 1
        ((count++))
        continue
    fi
    
    # Claude is ready!
    echo "[WAIT] Claude is ready after ${count}s"
    exit 0
done

echo "[WAIT] WARNING: Timeout after ${MAX_WAIT}s - proceeding anyway"
exit 1