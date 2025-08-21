#!/bin/bash
# Claude State Detection Utilities
# Functions to detect Claude's current state (thinking, ready, etc)

TMUX_SESSION="autonomous-claude"

# Check if Claude is currently thinking (processing but not using tokens)
is_claude_thinking() {
    # Get the current tmux pane content
    local pane_content
    pane_content=$(tmux capture-pane -t "$TMUX_SESSION" -p 2>/dev/null)
    
    # First, filter out known false positives:
    # - Collapsed content indicators: "… +N lines (ctrl+r to expand)"
    # - These appear when Claude collapses long outputs
    local filtered_content
    filtered_content=$(echo "$pane_content" | grep -v "… +[0-9]* lines")
    
    # Check for the ellipsis character (…) which indicates active thinking
    # This is Unicode U+2026, not three dots
    if echo "$filtered_content" | grep -q "…"; then
        return 0  # True - Claude is thinking
    fi
    
    # Also check for animated indicators at line start
    # These appear during thinking: . + * ❄ ✿ ✶
    if echo "$pane_content" | grep -qE '^[.+*❄✿✶]'; then
        return 0  # True - Claude is thinking
    fi
    
    # If no thinking indicators found, Claude is ready
    return 1  # False - Claude appears ready
}

# Wait for Claude to finish thinking with timeout
wait_for_claude_ready() {
    local max_wait=${1:-120}  # Default 2 minutes
    local check_interval=${2:-2}  # Check every 2 seconds
    local elapsed=0
    
    echo "[DETECTOR] Waiting for Claude to be ready (max ${max_wait}s)..." >&2
    
    while [ $elapsed -lt $max_wait ]; do
        if ! is_claude_thinking; then
            echo "[DETECTOR] Claude is ready after ${elapsed}s" >&2
            return 0
        fi
        
        echo "[DETECTOR] Claude still thinking (ellipsis detected)... (${elapsed}s/${max_wait}s)" >&2
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    echo "[DETECTOR] Warning: Timeout waiting for Claude (${max_wait}s)" >&2
    return 1
}

# Send command and wait for it to execute
send_command_and_wait() {
    local command="$1"
    local max_wait=${2:-30}
    
    if ! tmux list-sessions 2>/dev/null | grep -q "$TMUX_SESSION"; then
        echo "[DETECTOR] Error: Tmux session not responsive" >&2
        return 1
    fi
    
    echo "[DETECTOR] Sending command: $command" >&2
    tmux send-keys -t "$TMUX_SESSION" "$command" && tmux send-keys -t "$TMUX_SESSION" "Enter"
    
    # Wait for command to be processed
    wait_for_claude_ready $max_wait
}

# Export functions for use by other scripts
export -f is_claude_thinking
export -f wait_for_claude_ready
export -f send_command_and_wait