#!/bin/bash
# Source this file to get the trysend function
# Usage: trysend "command" [max_retries] [operation_name]

trysend() {
    local command="$1"
    local max_retries="${2:-180}"  # Default 3 minutes (180 seconds)
    local operation="${3:-command}"
    local claude_pane=$(tmux list-panes -t "${TMUX_SESSION:-autonomous-claude}" -F '#{pane_id}' 2>/dev/null | head -1)
    
    if [ -z "$claude_pane" ]; then
        echo "[TRYSEND] ERROR: Could not find Claude pane" >&2
        return 1
    fi
    
    echo "[TRYSEND] Preparing to send $operation: $command" >&2
    
    local attempt=0
    while [ $attempt -lt $max_retries ]; do
        # Check Claude's state
        local pane_content=$(tmux capture-pane -t "$claude_pane" -p -e -S -10)
        
        # Check for thinking indicators
        if echo "$pane_content" | grep -q '\[38;5;174m.*…' || \
           echo "$pane_content" | grep -E '\[38;5;174m[[:space:]]*[.+*❄✿✶]' | grep -qv 'tokens'; then
            echo "[TRYSEND] Claude thinking, retry $((attempt+1))/$max_retries..." >&2
            sleep 1
            ((attempt++))
            continue
        fi
        
        # Ready to send
        echo "[TRYSEND] Sending $operation" >&2
        tmux send-keys -t "${TMUX_SESSION:-autonomous-claude}" "$command"
        
        # Add Enter if not included
        if [[ ! "$command" =~ Enter$ ]] && [[ "$command" != *$'\n'* ]]; then
            tmux send-keys -t "${TMUX_SESSION:-autonomous-claude}" Enter
        fi
        
        return 0
    done
    
    echo "[TRYSEND] WARNING: Timeout after $max_retries attempts" >&2
    return 1
}

# Export the function for use in other scripts
export -f trysend