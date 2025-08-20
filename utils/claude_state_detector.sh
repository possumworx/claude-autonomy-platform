#!/bin/bash
# Claude State Detection Utilities with Color Detection
# Functions to detect Claude's current state using both text patterns and ANSI colors

TMUX_SESSION="autonomous-claude"

# Check if Claude is currently thinking (processing but not using tokens)
is_claude_thinking() {
    # Get the current tmux pane content WITH ANSI escape codes
    # The -e flag preserves escape sequences
    local pane_content
    pane_content=$(tmux capture-pane -t "$TMUX_SESSION" -p -e 2>/dev/null)
    
    # Get the last several lines where the status appears
    # The status line can be a few lines up from the bottom
    local last_lines
    last_lines=$(echo "$pane_content" | tail -n 15)
    
    # Check for the specific orange-red color (38;5;174) WITH the ellipsis character
    # This combination is unique to Claude's thinking animation
    # The ellipsis might appear as UTF-8 (…) or be garbled in terminal capture
    if echo "$last_lines" | grep -E '\[38;5;174m.*(…|\.\.\.)' || echo "$last_lines" | grep -P '\[38;5;174m.*(\302\205|\342\200\246)'; then
        return 0  # True - Claude is thinking
    fi
    
    # Also check if the color appears with common "thinking" action words
    if echo "$last_lines" | grep -E '\[38;5;174m.*(Thinking|Processing|Reticulating|Analyzing|Reviewing|Searching|Reading|Writing|Editing|Running|Executing|Checking)'; then
        return 0  # True - Claude is thinking  
    fi
    
    # Also check for other thinking animation symbols with the same color
    # These appear during thinking: . + * ❄ ✿ ✶
    if echo "$last_lines" | grep -E '\[38;5;174m[[:space:]]*[.+*❄✿✶]' | grep -v 'tokens'; then
        return 0  # True - Claude is thinking
    fi
    
    # Check for the specific "Thinking" text with orange-red color
    if echo "$last_lines" | grep -q '\[38;5;174m.*Thinking'; then
        return 0  # True - Claude is thinking
    fi
    
    # NO FALLBACK - we only detect thinking if we see BOTH color AND symbol
    # This prevents false positives from user input containing ellipsis
    
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
        
        echo "[DETECTOR] Claude still thinking (red ellipsis detected)... (${elapsed}s/${max_wait}s)" >&2
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    echo "[DETECTOR] Warning: Timeout waiting for Claude (${max_wait}s)" >&2
    return 1
}

# Debug function to show what the detector sees
debug_tmux_content() {
    echo "[DETECTOR DEBUG] Raw tmux content with ANSI codes:" >&2
    tmux capture-pane -t "$TMUX_SESSION" -p -e | cat -v | tail -n 10 >&2
    echo "[DETECTOR DEBUG] Checking for thinking indicators..." >&2
    if is_claude_thinking; then
        echo "[DETECTOR DEBUG] Claude is THINKING (red ellipsis found)" >&2
    else
        echo "[DETECTOR DEBUG] Claude is READY (no red ellipsis)" >&2
    fi
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
    tmux send-keys -t "$TMUX_SESSION" "$command" && tmux send-keys -t "$TMUX_SESSION" "Enter"
    
    # Wait for command to be processed
    wait_for_claude_ready $max_wait
}

# Export functions for use by other scripts
export -f is_claude_thinking
export -f wait_for_claude_ready
export -f debug_tmux_content