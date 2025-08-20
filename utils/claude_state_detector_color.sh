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
    
    # The actual Claude thinking animation uses specific ANSI color codes
    # Look for the orange-red color that Claude uses for the thinking animation
    # This is specifically \033[38;5;174m (or ^[[38;5;174m in raw form)
    # Combined with the ellipsis character (…) or thinking symbols
    
    # Check for the specific orange-red color (38;5;174) used by Claude's thinking animation
    # This is the most reliable indicator since user output won't have this exact color
    # We check only the last few lines to avoid false positives from old output
    
    local last_lines
    last_lines=$(echo "$pane_content" | tail -n 5)
    
    # Check for orange-red colored ellipsis in recent output
    if echo "$last_lines" | grep -q '\[38;5;174m.*…'; then
        return 0  # True - Claude is thinking
    fi
    
    # Check for orange-red colored thinking animation symbols in recent output
    # These appear during thinking: . + * ❄ ✿ ✶
    if echo "$last_lines" | grep -E '\[38;5;174m[[:space:]]*[.+*❄✿✶]' | grep -v 'tokens'; then
        # Exclude lines with "tokens" to avoid matching the status line
        return 0  # True - Claude is thinking
    fi
    
    # Check for the specific "Thinking" text with orange-red color
    if echo "$last_lines" | grep -q '\[38;5;174m.*Thinking'; then
        return 0  # True - Claude is thinking
    fi
    
    # Fallback: If we can't detect colors properly, still check for plain ellipsis
    # but only at the very end of output (to reduce false positives)
    if echo "$pane_content" | tail -n 3 | grep -q "…$"; then
        # Log this as a warning since we're using fallback detection
        echo "[DETECTOR] Warning: Using fallback detection (no color info)" >&2
        return 0  # True - Claude might be thinking
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
        
        echo "[DETECTOR] Claude still thinking (colored animation detected)... (${elapsed}s/${max_wait}s)" >&2
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
        echo "[DETECTOR DEBUG] Claude is THINKING" >&2
    else
        echo "[DETECTOR DEBUG] Claude is READY" >&2
    fi
}

# Export functions for use by other scripts
export -f is_claude_thinking
export -f wait_for_claude_ready
export -f debug_tmux_content