#!/bin/bash
# Export Handler for Claude Session Swap
# Handles the export process and verifies file creation
# Returns 0 on success, 1 on failure

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../config/claude_env.sh"
source "$SCRIPT_DIR/claude_state_detector.sh"

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
    
    # Get initial file timestamp (or 0 if doesn't exist)
    INITIAL_TIMESTAMP=0
    if [[ -f "$FULL_PATH" ]]; then
        INITIAL_TIMESTAMP=$(stat -c %Y "$FULL_PATH" 2>/dev/null || echo 0)
    fi
    
    # Send export command
    echo "[EXPORT_HANDLER] Sending /export command..."
    tmux send-keys -t autonomous-claude "/export $EXPORT_PATH" Enter
    
    # Wait for dialog to appear
    sleep 2
    
    # Navigate to "Save to file" option
    echo "[EXPORT_HANDLER] Navigating to 'Save to file' option..."
    tmux send-keys -t autonomous-claude Down
    sleep 0.2
    tmux send-keys -t autonomous-claude Down
    sleep 0.2
    tmux send-keys -t autonomous-claude Down
    sleep 0.2
    tmux send-keys -t autonomous-claude Enter
    
    # Wait a moment for file dialog
    sleep 1
    
    # Confirm the save
    echo "[EXPORT_HANDLER] Confirming save..."
    tmux send-keys -t autonomous-claude Enter
    
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