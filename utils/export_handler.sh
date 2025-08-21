#!/bin/bash
# Export Handler for Claude Session Swap
# Handles the export process and verifies file creation
# Returns 0 on success, 1 on failure

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../config/claude_env.sh"
source "$SCRIPT_DIR/claude_state_detector.sh"

# Read session name from config
CLAUDE_SESSION=$(jq -r '.claude_session // "autonomous-claude"' "$SCRIPT_DIR/../config/autonomous_timer_config.json")

# Function to wait for Claude to be ready (no thinking indicator)
wait_for_claude_ready() {
    local max_wait=${1:-30}
    local count=0
    echo "Waiting for Claude to finish thinking..."
    
    # Get the Claude pane in the claude session
    local claude_pane=$(tmux list-panes -t "$CLAUDE_SESSION" -F '#{pane_id}' 2>/dev/null | head -1)
    
    if [ -z "$claude_pane" ]; then
        echo "Warning: Could not find Claude pane"
        return 1
    fi
    
    while [ $count -lt $max_wait ]; do
        # Capture the last few lines of the pane WITH ANSI escape codes
        # The -e flag preserves color information
        local pane_content=$(tmux capture-pane -t "$claude_pane" -p -e -S -10)
        
        # Check for the specific orange-red color (38;5;174) used by Claude's thinking animation
        # This is the most reliable indicator since user output won't have this exact color
        if echo "$pane_content" | grep -q '\[38;5;174m.*…'; then
            echo "Claude is still thinking..."
            sleep 1
            ((count++))
            continue
        fi
        
        # Check for orange-red colored thinking animation symbols
        # These appear during thinking: . + * ❄ ✿ ✶
        if echo "$pane_content" | grep -E '\[38;5;174m[[:space:]]*[.+*❄✿✶]' | grep -v 'tokens'; then
            echo "Claude is still thinking..."
            sleep 1
            ((count++))
            continue
        fi
        
        # Check for the specific "ing…" pattern with orange-red color
        if echo "$pane_content" | grep -q '\[38;5;174m.*ing…'; then
            echo "Claude is still thinking..."
            sleep 1
            ((count++))
            continue
        fi
        
        # If no colored thinking indicators found, Claude is ready
        echo "Claude is ready (no thinking indicator found)"
        sleep 1  # Extra safety pause
        return 0
    done
    
    echo "Warning: Claude may still be thinking after ${max_wait}s"
    return 1
}

EXPORT_PATH="${1:-context/current_export.txt}"
FULL_PATH="$CLAP_DIR/$EXPORT_PATH"
MAX_ATTEMPTS=3
ATTEMPT=1

echo "[EXPORT_HANDLER] Starting export process to $EXPORT_PATH"

# Remove old export if it exists
if [[ -f "$FULL_PATH" ]]; then
    echo "[EXPORT_HANDLER] Removing old export file..."
    rm -f "$FULL_PATH"
fi

while [[ $ATTEMPT -le $MAX_ATTEMPTS ]]; do
    echo "[EXPORT_HANDLER] Attempt $ATTEMPT of $MAX_ATTEMPTS"
    
    # Wait for Claude to be ready before starting
    echo "[EXPORT_HANDLER] Waiting for Claude to be ready before export..."
    if wait_for_claude_ready 600; then  # 10 minutes for critical export operation
        echo "[EXPORT_HANDLER] Claude is ready, proceeding with export"
    else
        echo "[EXPORT_HANDLER] Timeout waiting for Claude to be ready, proceeding anyway"
    fi
    
    # Get initial file timestamp (or 0 if doesn't exist)
    INITIAL_TIMESTAMP=0
    if [[ -f "$FULL_PATH" ]]; then
        INITIAL_TIMESTAMP=$(stat -c %Y "$FULL_PATH" 2>/dev/null || echo 0)
    fi
    
    # Send export command
    echo "[EXPORT_HANDLER] Sending /export command..."
    tmux send-keys -t "$CLAUDE_SESSION" "/export $EXPORT_PATH"
    tmux send-keys -t "$CLAUDE_SESSION" Enter
    
    # Wait for dialog to appear
    sleep 2
    
    # Select "Save to file" option directly by pressing 2
    echo "[EXPORT_HANDLER] Selecting option 2 (Save to file)..."
    # The export dialog has numbered options:
    # 1. Copy to clipboard
    # 2. Save to file
    # 3. Cancel
    tmux send-keys -t "$CLAUDE_SESSION" 2
    sleep 0.5
    tmux send-keys -t "$CLAUDE_SESSION" Enter
    
    # Wait a moment for file dialog
    sleep 1
    
    # Confirm the save
    echo "[EXPORT_HANDLER] Confirming save..."
    tmux send-keys -t "$CLAUDE_SESSION" Enter
    
    # Wait for export to complete (Claude might be "thinking")
    echo "[EXPORT_HANDLER] Waiting for export to complete..."
    wait_for_claude_ready 120
    
    # Verify file was created/updated
    sleep 2
    if [[ -f "$FULL_PATH" ]]; then
        NEW_TIMESTAMP=$(stat -c %Y "$FULL_PATH" 2>/dev/null || echo 0)
        if [[ $NEW_TIMESTAMP -gt $INITIAL_TIMESTAMP ]]; then
            FILE_SIZE=$(stat -c %s "$FULL_PATH" 2>/dev/null || echo 0)
            if [[ $FILE_SIZE -gt 100 ]]; then
                echo "[EXPORT_HANDLER] Export successful! File size: $FILE_SIZE bytes"
                exit 0
            else
                echo "[EXPORT_HANDLER] Export file too small ($FILE_SIZE bytes), retrying..."
            fi
        else
            echo "[EXPORT_HANDLER] Export file not updated, retrying..."
        fi
    else
        echo "[EXPORT_HANDLER] Export file not created, retrying..."
    fi
    
    # If we're here, export failed
    ATTEMPT=$((ATTEMPT + 1))
    if [[ $ATTEMPT -le $MAX_ATTEMPTS ]]; then
        echo "[EXPORT_HANDLER] Waiting before retry..."
        sleep 5
    fi
done

echo "[EXPORT_HANDLER] ERROR: Export failed after $MAX_ATTEMPTS attempts!"
exit 1