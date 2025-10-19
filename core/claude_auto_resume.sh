#!/bin/bash
# Claude Auto-Resume Script
# Automatically restarts Claude Code in tmux after system reboot
# Works for any Claude on any box - checks config for RESTART_AFTER_REBOOT setting

set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTONOMY_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$AUTONOMY_DIR/config/claude_infrastructure_config.txt"
LOG_FILE="$AUTONOMY_DIR/logs/auto_resume.log"

# Ensure log directory exists
mkdir -p "$AUTONOMY_DIR/logs"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Claude Auto-Resume Starting ==="

# Check if config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    log "ERROR: Config file not found at $CONFIG_FILE"
    exit 1
fi

# Read RESTART_AFTER_REBOOT using Python config reader
cd "$AUTONOMY_DIR"
RESTART_AFTER_REBOOT=$(python3 -c "
import sys
sys.path.insert(0, 'utils')
from infrastructure_config_reader import get_config_value
print(get_config_value('RESTART_AFTER_REBOOT', 'false'))
")

# Check if auto-resume is enabled
if [[ "${RESTART_AFTER_REBOOT}" != "true" ]]; then
    log "Auto-resume disabled (RESTART_AFTER_REBOOT=${RESTART_AFTER_REBOOT:-not set})"
    log "This is a dormant ClAP installation - exiting gracefully"
    exit 0
fi

log "Auto-resume enabled - proceeding with Claude Code restart"

# Wait a moment for system to fully stabilize
sleep 5

# Check if tmux session already exists and Claude is running
if tmux has-session -t autonomous-claude 2>/dev/null; then
    log "Tmux session 'autonomous-claude' already exists"

    # Check if Claude Code is already running in the session
    if tmux list-panes -t autonomous-claude -F '#{pane_current_command}' | grep -q "claude"; then
        log "Claude Code already running in tmux session - nothing to do"
        exit 0
    fi

    log "Tmux session exists but Claude not running - starting Claude"
else
    log "Creating new tmux session 'autonomous-claude'"
    tmux new-session -d -s autonomous-claude
fi

# Load Claude model from config to ensure correct identity
CLAUDE_MODEL=$(python3 -c "
import sys
sys.path.insert(0, '$AUTONOMY_DIR/utils')
from infrastructure_config_reader import get_config_value
print(get_config_value('MODEL', ''))
")
if [[ -z "$CLAUDE_MODEL" ]]; then
    log "ERROR: Unable to read MODEL from config - cannot ensure correct identity!"
    exit 1
fi
log "Using model: $CLAUDE_MODEL"

# Load send_to_claude utilities for robust message sending
source "$AUTONOMY_DIR/utils/send_to_claude.sh"
export TMUX_SESSION="autonomous-claude"

# Start Claude Code with --continue and same flags as session swap
log "Starting Claude Code with --continue in autonomous-claude tmux session"
tmux send-keys -t autonomous-claude "cd $AUTONOMY_DIR && claude --continue --dangerously-skip-permissions --add-dir $HOME --model $CLAUDE_MODEL" Enter

# Wait for Claude to start and be ready (send_to_claude will wait for readiness)
log "Waiting for Claude Code to be ready..."
sleep 10

# Verify Claude started by checking process
if tmux list-panes -t autonomous-claude -F '#{pane_current_command}' | grep -q "claude"; then
    log "SUCCESS: Claude Code started successfully"

    # Send success message to Claude using send_to_claude for robustness
    RECOVERY_TIME=$(date '+%Y-%m-%d %H:%M:%S')
    send_to_claude "🔄 System rebooted - recovered successfully at $RECOVERY_TIME"
    log "Sent recovery notification to Claude"
    exit 0
else
    log "WARNING: Claude Code may not have started correctly"
    exit 1
fi
