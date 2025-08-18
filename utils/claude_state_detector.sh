#!/bin/bash
# Claude State Detection Utilities
# Functions to detect Claude's current state (thinking, ready, etc)

TMUX_SESSION="autonomous-claude"

# Check if Claude is currently thinking (processing but not using tokens)
is_claude_thinking() {
    # Get the current tmux pane content
    local pane_content
    pane_content=$(tmux capture-pane -t "$TMUX_SESSION" -p 2>/dev/null)
    
    # Check for thinking indicators
    if echo "$pane_content" | grep -q "Thinking\.\.\." || \
       echo "$pane_content" | grep -q "Processing\.\.\." || \
       echo "$pane_content" | grep -q "⚙️" || \
       echo "$pane_content" | grep -q "🤔"; then
        return 0  # True - Claude is thinking
    fi
    
    # Check if cursor is at end of a prompt (ready state)
    if echo "$pane_content" | tail -1 | grep -q ">" || \
       echo "$pane_content" | tail -1 | grep -q "\$"; then
        return 1  # False - Claude appears ready
    fi
    
    # If we can't determine, assume thinking for safety
    return 0
}

# Wait for Claude to finish thinking with timeout
wait_for_claude_ready() {
    local max_wait=${1:-120}  # Default 2 minutes
    local check_interval=${2:-2}  # Check every 2 seconds
    local elapsed=0
    
    echo "[DETECTOR] Waiting for Claude to be ready (max ${max_wait}s)..."
    
    while [ $elapsed -lt $max_wait ]; do
        if ! is_claude_thinking; then
            echo "[DETECTOR] Claude is ready after ${elapsed}s"
            return 0
        fi
        
        echo "[DETECTOR] Claude still thinking... (${elapsed}s/${max_wait}s)"
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    echo "[DETECTOR] Warning: Timeout waiting for Claude (${max_wait}s)"
    return 1
}

# Check if tmux session exists and is responsive
is_tmux_responsive() {
    tmux list-sessions 2>/dev/null | grep -q "$TMUX_SESSION"
    return $?
}

# Send command and wait for it to execute
send_command_and_wait() {
    local command="$1"
    local max_wait=${2:-30}
    
    if ! is_tmux_responsive; then
        echo "[DETECTOR] Error: Tmux session not responsive"
        return 1
    fi
    
    echo "[DETECTOR] Sending command: $command"
    tmux send-keys -t "$TMUX_SESSION" "$command" "Enter"
    
    # Wait for command to be processed
    wait_for_claude_ready $max_wait
}