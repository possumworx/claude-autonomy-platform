#!/bin/bash
# Unified function for sending messages to Claude with intelligent waiting
# Sources: claude_safe_send.sh, wait_for_claude.sh, and today's improvements
#
# Usage: send_to_claude "message" [skip_clear]
# Example: send_to_claude "/export context/current_export.txt"
# Example: send_to_claude "You have 80% context used"
# Example: send_to_claude "2" "true"  # For menu selections, skip clearing Enter

send_to_claude() {
    local message="$1"
    local skip_clear="${2:-false}"  # Optional: set to "true" to skip clearing Enter
    local tmux_session="${TMUX_SESSION:-autonomous-claude}"

    if [ -z "$message" ]; then
        echo "[SEND_TO_CLAUDE] ERROR: No message provided" >&2
        return 1
    fi
    
    # Get Claude pane
    local claude_pane=$(tmux list-panes -t "$tmux_session" -F '#{pane_id}' 2>/dev/null | head -1)
    if [ -z "$claude_pane" ]; then
        echo "[SEND_TO_CLAUDE] ERROR: Could not find Claude pane in session $tmux_session" >&2
        return 1
    fi
    
    echo "[SEND_TO_CLAUDE] Preparing to send: $message" >&2
    
    # Send clearing Enter first (unless skipped)
    if [ "$skip_clear" != "true" ]; then
        echo "[SEND_TO_CLAUDE] Sending clearing Enter" >&2
        tmux send-keys -t "$tmux_session" Enter
        sleep 0.1  # Brief pause to let it process
    fi
    
    local attempt=0
    local notification_sent=0
    
    # Indefinite retry loop
    while true; do
        # Capture pane content with ANSI escape codes for color detection
        local pane_content=$(tmux capture-pane -t "$claude_pane" -p -e -S -10)
        
        # Check for thinking indicators - looking for ellipsis (…) in orange/red colors
        # These color codes are used exclusively for thinking states in Claude Code
        # 174 = dark orange-red, 202-216 = orange range
        if echo "$pane_content" | grep -qE '\[38;5;(174|20[2-9]|21[0-6])m[^[]*…'; then
            
            # After 15 minutes, assume it's a stale indicator and proceed
            if [ $attempt -ge 900 ]; then
                echo "[SEND_TO_CLAUDE] WARNING: Waited 15 minutes - assuming stale thinking indicator, proceeding" >&2
                break
            fi
            
            # Log every 30 seconds
            if [ $((attempt % 30)) -eq 0 ]; then
                echo "[SEND_TO_CLAUDE] Claude thinking... (waiting ${attempt}s)" >&2
                
                # Alert Amy after 10 minutes
                if [ $attempt -ge 600 ] && [ $notification_sent -eq 0 ]; then
                    echo "[SEND_TO_CLAUDE] WARNING: Waiting over 10 minutes - notifying Amy" >&2
                    
                    # Send Discord notification if possible
                    if command -v write_channel >/dev/null 2>&1; then
                        write_channel amy-delta "⚠️ Claude has been thinking for over 10 minutes while trying to send: '$message'. This might be a false positive detection." 2>/dev/null || true
                    fi
                    
                    notification_sent=1
                fi
            fi
            
            sleep 1
            ((attempt++))
            continue
        fi
        
        # Claude is ready - send the message
        echo "[SEND_TO_CLAUDE] Claude ready after ${attempt}s - sending message" >&2

        # Clear any escape sequences or garbage on the input line with Ctrl+U
        tmux send-keys -t "$tmux_session" C-u
        sleep 0.05  # Brief pause to let clear complete

        # Send message and Enter as separate commands for reliability
        tmux send-keys -t "$tmux_session" "$message"
        tmux send-keys -t "$tmux_session" Enter
        
        echo "[SEND_TO_CLAUDE] Message sent successfully" >&2
        return 0
    done
}

# Export function for use in other scripts
export -f send_to_claude

# If script is run directly with arguments, execute the function
if [ "${BASH_SOURCE[0]}" = "${0}" ] && [ $# -gt 0 ]; then
    send_to_claude "$@"
fi