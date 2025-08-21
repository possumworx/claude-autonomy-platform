#!/bin/bash
# Session Swap Script for Claude
# Updates context, backs up work, and swaps to fresh session
# Usage: session_swap.sh [KEYWORD]

# Load path utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The swap command lives in ~/bin/, but we need ClAP paths
CLAP_DIR="$HOME/claude-autonomy-platform"
source "$CLAP_DIR/config/claude_env.sh"

# This function is now loaded from claude_state_detector.sh

# Function to read values from infrastructure config (override claude_env.sh version)
read_session_config() {
    local key="$1"
    local config_file="$CLAP_DIR/config/claude_infrastructure_config.txt"
    
    if [[ -f "$config_file" ]]; then
        grep "^${key}=" "$config_file" | cut -d'=' -f2-
    else
        echo "[SESSION_SWAP] ERROR: Config file not found at $config_file" >&2
    fi
}

# Load Claude model from config
CLAUDE_MODEL=$(read_session_config "MODEL")
if [[ -z "$CLAUDE_MODEL" ]]; then
    echo "[SESSION_SWAP] ERROR: Unable to read MODEL from config - cannot ensure correct identity!"
    echo "[SESSION_SWAP] Aborting session swap to prevent identity confusion."
    rm -f "$LOCKFILE"
    exit 1
fi
echo "[SESSION_SWAP] Using model: $CLAUDE_MODEL"

KEYWORD=${1:-"NONE"}
echo "[SESSION_SWAP] Context keyword: $KEYWORD"

# Create lockfile to pause autonomous timer notifications
LOCKFILE="$CLAP_DIR/data/session_swap.lock"
echo "[SESSION_SWAP] Creating lockfile to pause autonomous timer..."
touch "$LOCKFILE"
echo "$$" > "$LOCKFILE"

# Load state detection utilities
source "$CLAP_DIR/utils/claude_state_detector.sh"

# Load the trysend function for smart command sending
source "$CLAP_DIR/utils/claude_safe_send.sh"

# Wrapper for backwards compatibility
send_command_and_wait() {
    local command="$1"
    local max_wait=${2:-180}  # Default 3 minutes
    
    echo "[SESSION_SWAP] Sending: $command" >&2
    trysend "$command" "$max_wait" "session swap"
}

# Wait for any ongoing Claude responses to complete
echo "[SESSION_SWAP] Waiting for Claude to finish current response..." >&2
"$CLAP_DIR/utils/wait_for_claude.sh" 60 "initial check"

echo "[SESSION_SWAP] Backing up work to git..."
cd "$PERSONAL_DIR"
git add -A
git commit -m "Autonomous session backup - $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main
echo "[SESSION_SWAP] Backup complete!"

# Return to CLAP directory after git operations
cd "$CLAP_DIR"

echo "[SESSION_SWAP] Exporting current conversation..."
# Wait for Claude to be ready before sending commands
"$CLAP_DIR/utils/wait_for_claude.sh" 30 "shell command"

# First ensure Claude is in the correct directory using shell command
send_command_and_wait "!" 10
send_command_and_wait "cd $CLAP_DIR" 10

# Use the export handler for reliable export with verification
export_path="context/current_export.txt"
if "$CLAP_DIR/utils/export_handler.sh" "$export_path"; then
    echo "[SESSION_SWAP] Export successful, updating conversation history..."
    python3 "$CLAP_DIR/utils/update_conversation_history.py" "$CLAP_DIR/$export_path"
    # Keep the export file as fallback for next run
    echo "[SESSION_SWAP] Export preserved at $export_path for reference"
else
    echo "[SESSION_SWAP] ERROR: Export failed after multiple attempts!"
    echo "[SESSION_SWAP] Aborting session swap to prevent data loss."
    rm -f "$LOCKFILE"
    exit 1
fi

echo "[SESSION_SWAP] Updating context with keyword: $KEYWORD"
# Temporarily write keyword for context builder
echo "$KEYWORD" > "$CLAP_DIR/new_session.txt"
python3 "$CLAP_DIR/context/project_session_context_builder.py"
# Reset to FALSE after context building
echo "FALSE" > "$CLAP_DIR/new_session.txt"

echo "[SESSION_SWAP] Swapping to new session..."
# Wait for Claude to be ready before sending exit command
"$CLAP_DIR/utils/wait_for_claude.sh" 30 "/exit command"

send_command_and_wait "/exit" 30

# Wait for Claude to fully exit before killing tmux
echo "[SESSION_SWAP] Waiting for Claude to exit cleanly..."
sleep 5

# Check if Claude process is still running
if tmux list-panes -t autonomous-claude -F '#{pane_pid}' 2>/dev/null | xargs -I {} pgrep -P {} claude > /dev/null 2>&1; then
    echo "[SESSION_SWAP] WARNING: Claude still running, waiting longer..."
    sleep 10
fi

# Kill and recreate tmux session for stability
echo "[SESSION_SWAP] Recreating tmux session for stability..."
tmux kill-session -t autonomous-claude 2>/dev/null || true
sleep 2
tmux new-session -d -s autonomous-claude

# Implement log rotation
if [[ -f "$CLAP_DIR/data/current_session.log" ]]; then
    timestamp=$(date '+%Y%m%d_%H%M%S')
    mv "$CLAP_DIR/data/current_session.log" "$CLAP_DIR/data/session_ended_${timestamp}.log"
    echo "[SESSION_SWAP] Rotated current session log to session_ended_${timestamp}.log"
    
    # Clean up old session logs (keep only 10 most recent)
    cd "$CLAP_DIR/data"
    ls -t session_ended_*.log 2>/dev/null | tail -n +11 | xargs -r rm -f
    cd "$CLAP_DIR"
fi

# Start logging new session
# Removed pipe-pane due to instability - see docs/pipe-pane-instability-report.md

# Clear any stray keypresses before starting Claude
tmux send-keys -t autonomous-claude "Enter"

# Start Claude in the new session
tmux send-keys -t autonomous-claude "cd $CLAP_DIR && claude --dangerously-skip-permissions --add-dir $HOME --model $CLAUDE_MODEL" && tmux send-keys -t autonomous-claude "Enter"

# POSS-240 FIX: Clear any API error state after session swap
if [ -f "$CLAP_DIR/data/api_error_state.json" ]; then
    rm "$CLAP_DIR/data/api_error_state.json"
    echo "[SESSION_SWAP] Cleared API error state"
fi

# Clear context escalation state to prevent runaway warnings
if [ -f "$CLAP_DIR/data/context_escalation_state.json" ]; then
    rm "$CLAP_DIR/data/context_escalation_state.json"
    echo "[SESSION_SWAP] Cleared context escalation state"
fi

# Clear any notification tracking files
if [ -f "$CLAP_DIR/data/last_discord_notification.txt" ]; then
    rm "$CLAP_DIR/data/last_discord_notification.txt"
    echo "[SESSION_SWAP] Cleared notification tracking"
fi

# Remove lockfile to resume autonomous timer notifications
echo "[SESSION_SWAP] Removing lockfile to resume autonomous timer..."
rm -f "$LOCKFILE"

echo "[SESSION_SWAP] Session swap complete!"

# Wait for Claude to be ready, then send completion message
sleep 10
# Load prompts config
PROMPTS_CONFIG="$CLAP_DIR/config/prompts.json"
if [[ -f "$PROMPTS_CONFIG" ]]; then
    # Get the template
    TEMPLATE=$(python3 -c "
import json
with open('$PROMPTS_CONFIG', 'r') as f:
    config = json.load(f)
    print(config['prompts']['session_complete']['template'])
")
    # Format the message
    TIME=$(date '+%Y-%m-%d %H:%M')
    MESSAGE=$(echo "$TEMPLATE" | sed "s/{time}/$TIME/g" | sed "s/{keyword}/$KEYWORD/g")
else
    # Default message if config not found
    MESSAGE="✅ Session swap completed successfully at $(date '+%Y-%m-%d %H:%M') with $KEYWORD context.\nFeel free to continue with your plans."
fi

# Send the completion message
tmux send-keys -t autonomous-claude "$MESSAGE" && tmux send-keys -t autonomous-claude "Enter"
