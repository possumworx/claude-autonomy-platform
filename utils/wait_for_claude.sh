#!/bin/bash
# Reusable wait function for Claude readiness
# Uses color-based detection to ensure Claude is not thinking

TMUX_SESSION="${CLAUDE_SESSION:-autonomous-claude}"
MAX_WAIT="${1:-0}"  # Default 0 = indefinite wait
OPERATION="${2:-operation}"  # What we're waiting for

echo "[WAIT] Waiting for Claude to be ready for: $OPERATION (max ${MAX_WAIT}s)"

# Get the Claude pane
claude_pane=$(tmux list-panes -t "$TMUX_SESSION" -F '#{pane_id}' 2>/dev/null | head -1)

if [ -z "$claude_pane" ]; then
    echo "[WAIT] ERROR: Could not find Claude pane"
    exit 1
fi

count=0
wait_logged=0
while [ $MAX_WAIT -eq 0 ] || [ $count -lt $MAX_WAIT ]; do
    # Capture with ANSI escape codes
    pane_content=$(tmux capture-pane -t "$claude_pane" -p -e -S -10)
    
    # Check for orange-red thinking indicators
    if echo "$pane_content" | grep -q '\[38;5;174m.*…'; then
        if [ $MAX_WAIT -eq 0 ]; then
            # Log every 30 seconds for indefinite waits
            if [ $((count % 30)) -eq 0 ]; then
                echo "[WAIT] Claude thinking... (waiting indefinitely, ${count}s elapsed)"
                # Alert after 10 minutes
                if [ $count -ge 600 ] && [ $wait_logged -eq 0 ]; then
                    echo "[WAIT] WARNING: Waiting over 10 minutes - possible false positive"
                    wait_logged=1
                fi
            fi
        else
            echo "[WAIT] Claude is thinking... (${count}s)"
        fi
        sleep 1
        ((count++))
        continue
    fi
    
    # Check for animated indicators with color
    if echo "$pane_content" | grep -E '\[38;5;174m[[:space:]]*[.+*❄✿✶]' | grep -v 'tokens'; then
        if [ $MAX_WAIT -eq 0 ]; then
            # Use same logging for animated indicators
            if [ $((count % 30)) -eq 0 ]; then
                echo "[WAIT] Claude thinking... (waiting indefinitely, ${count}s elapsed)"
                if [ $count -ge 600 ] && [ $wait_logged -eq 0 ]; then
                    echo "[WAIT] WARNING: Waiting over 10 minutes - possible false positive"
                    wait_logged=1
                fi
            fi
        else
            echo "[WAIT] Claude is thinking... (${count}s)"
        fi
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