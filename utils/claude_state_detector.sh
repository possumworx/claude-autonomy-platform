#!/bin/bash
# Claude State Detector
# Functions for detecting Claude's current state

# Function to wait for Claude to be ready (no thinking indicator)
wait_for_claude_ready() {
    local max_wait=${1:-30}
    local count=0
    echo "[DETECTOR] Waiting for Claude to be ready (max ${max_wait}s)..." >&2
    
    # Get the Claude pane in the claude session
    local claude_pane=$(tmux list-panes -t claude -F '#{pane_id}' 2>/dev/null | head -1)
    
    if [ -z "$claude_pane" ]; then
        echo "[DETECTOR] Warning: Could not find Claude pane" >&2
        return 1
    fi
    
    while [ $count -lt $max_wait ]; do
        # Capture the last few lines of the pane
        local pane_content=$(tmux capture-pane -t "$claude_pane" -p -S -10)
        
        # Check for thinking indicators and the ellipsis pattern
        # The animated indicators appear at line start: . + * ❄ ✿ ✶
        # More importantly: any word followed by … (single ellipsis char) indicates thinking
        if ! echo "$pane_content" | grep -qE '^[.+*❄✿✶]|…'; then
            echo "[DETECTOR] Claude is ready after ${count}s" >&2
            sleep 1  # Extra safety pause
            return 0
        fi
        
        sleep 1
        ((count++))
    done
    
    echo "[DETECTOR] Warning: Claude may still be thinking after ${max_wait}s" >&2
    return 1
}