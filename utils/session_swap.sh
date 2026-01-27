#!/bin/bash
# Session Swap Script for Claude
# Updates context, backs up work, and swaps to fresh session
# Usage: session_swap.sh [KEYWORD]

# Load path utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Note: The 'swap' command is a bash function in natural_commands.sh that writes to new_session.txt
CLAP_DIR="$HOME/claude-autonomy-platform"
source "$CLAP_DIR/config/claude_env.sh"

# Load logging utilities
source "$CLAP_DIR/utils/log_utils.sh"
source "$CLAP_DIR/utils/session_swap_logger.sh"

# Track swap start time
SWAP_START_TIME=$(date +%s)

KEYWORD=${1:-"NONE"}
echo "[SESSION_SWAP] Context keyword: $KEYWORD"
log_info "SESSION_SWAP" "Starting session swap with keyword: $KEYWORD"
log_swap_event "SWAP_START" "$KEYWORD" "initiated" "Session swap initiated by monitor"

# Load the unified send_to_claude function FIRST so we can use it
source "$CLAP_DIR/utils/send_to_claude.sh"

# Create lockfile to pause autonomous timer notifications
LOCKFILE="$CLAP_DIR/data/session_swap.lock"
echo "[SESSION_SWAP] Creating lockfile to pause autonomous timer..."
touch "$LOCKFILE"
echo "$$" > "$LOCKFILE"
log_info "SESSION_SWAP" "Created lockfile with PID $$"

# Alert Claude that swap is starting
echo "[SESSION_SWAP] Notifying Claude that swap is starting..."
send_to_claude "🔄 Session swap to $KEYWORD triggered. Please stay quiet while swap completes..."
sleep 2  # Give Claude time to see the message

# Load Claude model from config using the standard read_config function
CLAUDE_MODEL=$(read_config "MODEL")
if [[ -z "$CLAUDE_MODEL" ]]; then
    echo "[SESSION_SWAP] ERROR: Unable to read MODEL from config - cannot ensure correct identity!"
    echo "[SESSION_SWAP] Aborting session swap to prevent identity confusion."
    log_error "SESSION_SWAP" "Failed to read MODEL from config - aborting"
    log_swap_event "SWAP_FAILED" "$KEYWORD" "failed" "Unable to read MODEL from config"
    track_swap_metrics "$SWAP_START_TIME" "$(date +%s)" "$KEYWORD" "failed" "0" "unknown"

    # Alert Claude that swap failed
    send_to_claude "❌ Session swap abandoned: Unable to read MODEL from config. Still in current session."
    sleep 2

    rm -f "$LOCKFILE"
    exit 1
fi
echo "[SESSION_SWAP] Using model: $CLAUDE_MODEL"
log_info "SESSION_SWAP" "Using model: $CLAUDE_MODEL"

# Note: send_to_claude will automatically wait for Claude to be ready

# Git backup removed - handled by separate service for reliability
# Return to CLAP directory for session operations
cd "$CLAP_DIR" || exit

echo "[SESSION_SWAP] Exporting current conversation..."

# First ensure Claude is in the correct directory using shell command
send_to_claude "! cd $CLAP_DIR"

# Wait for shell command to complete
sleep 2

# Export conversation using our new unified approach
export_path="context/current_export.txt"
full_path="$CLAP_DIR/$export_path"

echo "[SESSION_SWAP] Starting export..."
send_to_claude "/export $export_path"

# Wait for export to complete (no confirmation dialog anymore)
sleep 5

# Give more time for file to be written after confirmation
sleep 5

# Verify export was created
if [[ -f "$full_path" ]]; then
    # Check if file was modified in the last 10 seconds
    current_time=$(date +%s)
    file_mtime=$(stat -c %Y "$full_path" 2>/dev/null || echo 0)
    time_diff=$((current_time - file_mtime))

    if [[ $time_diff -le 30 ]]; then
        file_size=$(stat -c %s "$full_path" 2>/dev/null || echo 0)
        file_size=$(stat -c %s "$full_path" 2>/dev/null || echo 0)
        echo "[SESSION_SWAP] Export successful! File size: $file_size bytes (modified ${time_diff}s ago)"
        log_info "SESSION_SWAP" "Export successful - file size: $file_size bytes, modified ${time_diff}s ago"
        log_swap_event "EXPORT_SUCCESS" "$KEYWORD" "success" "Export size: $file_size bytes"
        python3 "$CLAP_DIR/utils/update_conversation_history.py" "$full_path"
        echo "[SESSION_SWAP] Export preserved at $export_path for reference"
        log_info "SESSION_SWAP" "Conversation history updated from export"
        EXPORT_SIZE=$file_size
    else
        echo "[SESSION_SWAP] ERROR: Export file exists but wasn't recently modified (${time_diff}s ago)"
        echo "[SESSION_SWAP] This suggests the export didn't actually update the file (expecting <30s)"
        log_error "SESSION_SWAP" "Export file not recently modified - ${time_diff}s ago (expecting <30s)"
        log_swap_event "EXPORT_FAILED" "$KEYWORD" "failed" "Export file not recently modified"
        track_swap_metrics "$SWAP_START_TIME" "$(date +%s)" "$KEYWORD" "failed" "0" "$CLAUDE_MODEL"

        # Alert Claude that swap failed
        send_to_claude "❌ Session swap abandoned: Export file not recently modified. Still in current session."
        sleep 2

        rm -f "$LOCKFILE"
        exit 1
    fi
else
    echo "[SESSION_SWAP] ERROR: Export failed - file not created!"
    log_error "SESSION_SWAP" "Export failed - file not created at $full_path"
    log_swap_event "EXPORT_FAILED" "$KEYWORD" "failed" "Export file not created"
    track_swap_metrics "$SWAP_START_TIME" "$(date +%s)" "$KEYWORD" "failed" "0" "$CLAUDE_MODEL"

    # Alert Claude that swap failed
    send_to_claude "❌ Session swap abandoned: Export file not created. Still in current session."
    sleep 2

    rm -f "$LOCKFILE"
    exit 1
fi

echo "[SESSION_SWAP] Capturing final usage reading from old session..."
python3 "$CLAP_DIR/utils/check_usage.py" > /dev/null 2>&1 || echo "[SESSION_SWAP] Warning: Final usage capture failed"

echo "[SESSION_SWAP] Updating context with keyword: $KEYWORD"
# Keyword is already in new_session.txt from trigger - context builder will use it
python3 "$CLAP_DIR/context/project_session_context_builder.py"
# Note: Monitor will reset to FALSE after completion

# Fetch Leantime seeds for autonomous time skill
echo "[SESSION_SWAP] Fetching Leantime seeds for autonomous time..."
python3 "$CLAP_DIR/utils/fetch_leantime_seeds.py" > /dev/null 2>&1 || echo "[SESSION_SWAP] Warning: Leantime seeds fetch failed (continuing anyway)"

echo "[SESSION_SWAP] Swapping to new session..."
send_to_claude "/exit"

# Wait for Claude to fully exit before killing tmux
echo "[SESSION_SWAP] Waiting for Claude to exit cleanly..."
sleep 5

# Check if Claude process is still running and retry /exit if needed
if tmux list-panes -t autonomous-claude -F '#{pane_pid}' 2>/dev/null | xargs -I {} pgrep -P {} claude > /dev/null 2>&1; then
    echo "[SESSION_SWAP] WARNING: Claude still running, retrying /exit..."
    send_to_claude "/exit"
    sleep 10

    # Final check - Claude might have been busy with something
    if tmux list-panes -t autonomous-claude -F '#{pane_pid}' 2>/dev/null | xargs -I {} pgrep -P {} claude > /dev/null 2>&1; then
        echo "[SESSION_SWAP] WARNING: Claude still running after retry - will force kill"
    else
        echo "[SESSION_SWAP] Claude exited cleanly after retry"
    fi
fi

# Kill and recreate tmux session for stability
echo "[SESSION_SWAP] Recreating tmux session for stability..."

# Clean up any discord-mcp zombie processes (POSS-286)
echo "[SESSION_SWAP] Cleaning up discord-mcp processes..."
pkill -f "discord-mcp.*\.jar" 2>/dev/null || true
sleep 1

# Use systemd-run to escape service cgroup restrictions (KillMode=process)
# This allows session-swap-monitor.service to kill tmux despite isolation
echo "[SESSION_SWAP] Killing tmux session (using systemd-run to escape cgroup)..."
systemd-run --user --scope tmux kill-session -t autonomous-claude 2>/dev/null || true
sleep 2

echo "[SESSION_SWAP] Creating new tmux session..."
tmux new-session -d -s autonomous-claude

# Implement log rotation
if [[ -f "$CLAP_DIR/data/current_session.log" ]]; then
    timestamp=$(date '+%Y%m%d_%H%M%S')
    mv "$CLAP_DIR/data/current_session.log" "$CLAP_DIR/data/session_ended_${timestamp}.log"
    echo "[SESSION_SWAP] Rotated current session log to session_ended_${timestamp}.log"

    # Clean up old session logs (keep only 10 most recent)
    cd "$CLAP_DIR/data" || exit
    ls -t session_ended_*.log 2>/dev/null | tail -n +11 | xargs -r rm -f
    cd "$CLAP_DIR" || exit
fi

# Start logging new session
# Removed pipe-pane due to instability - see docs/pipe-pane-instability-report.md

# POSS-240 FIX: Clear any API error state BEFORE session swap
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

# Trim Claude Code command history to prevent context bloat
echo "[SESSION_SWAP] Trimming command history..."
python3 "$CLAP_DIR/utils/trim_claude_history.py" > /dev/null 2>&1 || echo "[SESSION_SWAP] Warning: History trim failed"

# Wait for state files to be fully cleared
echo "[SESSION_SWAP] Waiting for state files to clear..."
sleep 2

# Clear any stray keypresses before starting Claude
tmux send-keys -t autonomous-claude Enter

# Source bashrc to ensure environment variables like LINUX_USER are exported
tmux send-keys -t autonomous-claude "source ~/.bashrc" Enter
sleep 1

# Start Claude in the new session
tmux send-keys -t autonomous-claude "cd $CLAP_DIR && claude --dangerously-skip-permissions --add-dir $HOME --model $CLAUDE_MODEL" Enter

# Wait for Claude to initialize and create its todo file
echo "[SESSION_SWAP] Waiting for Claude to initialize..."
sleep 5

# Carry over non-completed todos from previous session
echo "[SESSION_SWAP] Carrying over non-completed todos from previous session..."
python3 "$CLAP_DIR/utils/carry_over_todos.py"

# Remove lockfile to resume autonomous timer notifications
echo "[SESSION_SWAP] Removing lockfile to resume autonomous timer..."
rm -f "$LOCKFILE"

echo "[SESSION_SWAP] Session swap complete!"

# Track successful completion
SWAP_END_TIME=$(date +%s)
track_swap_metrics "$SWAP_START_TIME" "$SWAP_END_TIME" "$KEYWORD" "success" "${EXPORT_SIZE:-0}" "$CLAUDE_MODEL"
log_swap_event "SWAP_COMPLETE" "$KEYWORD" "success" "Session swap completed successfully"
log_info "SESSION_SWAP" "Session swap completed successfully"

# Ping healthchecks.io for successful swap
SESSION_SWAP_PING=$(read_config "SESSION_SWAP_PING")
if [[ -n "$SESSION_SWAP_PING" ]]; then
    curl -m 10 --retry 2 "$SESSION_SWAP_PING" > /dev/null 2>&1
    echo "[SESSION_SWAP] Sent healthcheck ping"
fi

# Wait for new session to be ready
sleep 10

# Update tracked session ID to the new session BEFORE sending completion message
# This prevents interference between /status command and Claude's response
log_info "SESSION_SWAP" "Updating tracked session ID to new session"
if ! python3 "$SCRIPT_DIR/track_current_session.py" 2>&1 | tee -a "$CLAP_DIR/logs/session_swap.log"; then
    log_error "SESSION_SWAP" "Failed to update session tracking"
    # Don't send warning yet - wait until after completion message
fi

# Reset usage tracking for new session (CoOP)
echo "[SESSION_SWAP] Resetting usage tracking for new session..."
python3 -c "
import json
from pathlib import Path
storage_file = Path('$CLAP_DIR/data/last_usage_cost.json')
data = {'total_cost': 0.0, 'session_id': 'reset', 'timestamp': '$(date -Iseconds)'}
storage_file.write_text(json.dumps(data, indent=2))
print('✓ Usage cost tracking reset to 0 for new session')
" 2>&1 | tee -a "$CLAP_DIR/logs/session_swap.log"
log_info "SESSION_SWAP" "Usage cost tracking reset to 0 for new session"

# Now send completion message (no interference with session tracking)
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

# Use send_to_claude for consistency and proper handling
send_to_claude "$MESSAGE"
