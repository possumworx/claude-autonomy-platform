#!/bin/bash
# Source this file to get the trysend function
# Usage: trysend "command" [max_retries] [operation_name]

trysend() {
    local command="$1"
    local max_retries="${2:-0}"  # Default 0 = indefinite wait
    local operation="${3:-command}"
    local claude_pane=$(tmux list-panes -t "${TMUX_SESSION:-autonomous-claude}" -F '#{pane_id}' 2>/dev/null | head -1)
    
    if [ -z "$claude_pane" ]; then
        echo "[TRYSEND] ERROR: Could not find Claude pane" >&2
        return 1
    fi
    
    echo "[TRYSEND] Preparing to send $operation: $command" >&2
    
    local attempt=0
    local wait_logged=0
    while [ $max_retries -eq 0 ] || [ $attempt -lt $max_retries ]; do
        # Check Claude's state
        local pane_content=$(tmux capture-pane -t "$claude_pane" -p -e -S -10)
        
        # Check for thinking indicators
        if echo "$pane_content" | grep -q '\[38;5;174m.*…' || \
           echo "$pane_content" | grep -E '\[38;5;174m[[:space:]]*[.+*❄✿✶]' | grep -qv 'tokens'; then
            if [ $max_retries -eq 0 ]; then
                # Log every 30 seconds for indefinite waits
                if [ $((attempt % 30)) -eq 0 ]; then
                    echo "[TRYSEND] Claude thinking... (waiting indefinitely, ${attempt}s elapsed)" >&2
                    # Alert after 10 minutes
                    if [ $attempt -ge 600 ] && [ $wait_logged -eq 0 ]; then
                        echo "[TRYSEND] WARNING: Waiting over 10 minutes - possible false positive" >&2
                        wait_logged=1
                    fi
                fi
            else
                echo "[TRYSEND] Claude thinking, retry $((attempt+1))/$max_retries..." >&2
            fi
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