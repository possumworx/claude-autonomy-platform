#!/bin/bash
# Rolling Context Swap
#
# Forks the current session, trims the branch at the checkpoint marker,
# then resumes into the trimmed session. The conversation continues
# with reduced context rather than starting fresh.
#
# This script MUST run outside the tmux session (via setsid) because
# it kills and recreates tmux as part of the swap. A backgrounded
# subprocess inside tmux would die when tmux kill-session runs.
#
# Triggered by: auto_context_marker.sh hook at ≥80% context
# Can also be run manually: rolling_swap.sh
#
# Design: Amy + Nyx, 2026-05-18

set -euo pipefail

CLAP_DIR="$HOME/claude-autonomy-platform"
LOG_FILE="$CLAP_DIR/logs/rolling_swap.log"
LOCKFILE="/tmp/${USER}_rolling_swap.lock"

source "$CLAP_DIR/config/claude_env.sh"

log() {
    echo "[$(date -Iseconds)] $1" | tee -a "$LOG_FILE"
}

# Wait for Claude to be at the input prompt, then send a message.
# Unlike send_to_claude.sh, this waits for the ❯ prompt character
# rather than detecting the absence of thinking indicators.
# This is necessary because the hook fires during tool use (while
# Claude appears to be "thinking"), and we need to wait for the
# current response to fully complete.
wait_and_send() {
    local message="$1"
    local tmux_session="autonomous-claude"
    local max_wait=300  # 5 minutes max
    local waited=0

    log "Waiting for Claude to reach prompt before sending: $message"

    while [ $waited -lt $max_wait ]; do
        # Look for the ❯ prompt character (Unicode: E2 9D AF) in the last few lines
        if tmux capture-pane -t "$tmux_session" -p -S -5 2>/dev/null | grep -q '❯'; then
            log "Prompt detected after ${waited}s — sending"
            # Clear any stale input, then send
            tmux send-keys -t "$tmux_session" C-u
            sleep 0.2
            tmux send-keys -t "$tmux_session" "$message"
            tmux send-keys -t "$tmux_session" Enter
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done

    log "WARNING: Prompt not detected after ${max_wait}s — sending anyway"
    tmux send-keys -t "$tmux_session" C-u
    sleep 0.2
    tmux send-keys -t "$tmux_session" "$message"
    tmux send-keys -t "$tmux_session" Enter
    return 0
}

cleanup() {
    rm -f "$LOCKFILE"
}
trap cleanup EXIT

# ─── Guard: prevent concurrent swaps ────────────────────────────────

if [ -f "$LOCKFILE" ]; then
    log "ERROR: Rolling swap already in progress (lockfile exists). Aborting."
    exit 1
fi
echo "$$" > "$LOCKFILE"

# Also check for regular session swap lock
if [ -f "/tmp/${USER}_session_swap.lock" ]; then
    log "ERROR: Regular session swap in progress. Aborting rolling swap."
    exit 1
fi

# ─── Step 1: Read current session ID ────────────────────────────────

STATUSLINE_DATA="$CLAP_DIR/data/statusline_data.json"

CURRENT_SESSION_ID=$(python3 -c "
import json
with open('$STATUSLINE_DATA') as f:
    data = json.load(f)
print(data.get('session_id', ''))
" 2>/dev/null || echo "")

if [ -z "$CURRENT_SESSION_ID" ]; then
    log "WARNING: Could not read session ID from statusline. Will use file timestamps to identify branch."
fi
log "Current session ID: ${CURRENT_SESSION_ID:-unknown}"

# ─── Step 2: Snapshot existing JSONL files ──────────────────────────

# Record all existing JSONL files before branching
JSONL_DIR="$HOME/.config/Claude/projects"
BEFORE_FILES=$(find "$JSONL_DIR" -name "*.jsonl" -type f 2>/dev/null | sort)

# ─── Step 3: Fork and exit ──────────────────────────────────────────

log "Sending /branch to Claude..."
wait_and_send "/branch"

# Wait for branch to complete (creates new JSONL file)
# /branch needs time to copy the JSONL and return to prompt
sleep 8

log "Sending /exit to Claude..."
wait_and_send "/exit"

# Wait for Claude to exit cleanly
log "Waiting for Claude to exit..."
sleep 8

# Retry if still running
if tmux list-panes -t autonomous-claude -F '#{pane_pid}' 2>/dev/null | xargs -I {} pgrep -P {} claude > /dev/null 2>&1; then
    log "Claude still running, retrying /exit..."
    tmux send-keys -t autonomous-claude "/exit" Enter
    sleep 10
fi

# ─── Step 4: Find the branched session ────────────────────────────────

AFTER_FILES=$(find "$JSONL_DIR" -name "*.jsonl" -type f 2>/dev/null | sort)

# The branch is the new file that didn't exist before
FORKED_SESSION=""
while IFS= read -r file; do
    if ! echo "$BEFORE_FILES" | grep -qF "$file"; then
        FORKED_SESSION="$file"
        break
    fi
done <<< "$AFTER_FILES"

# Fallback: if no new file found, use newest JSONL that isn't current session
if [ -z "$FORKED_SESSION" ]; then
    log "WARNING: No new file found by diff. Falling back to newest non-current JSONL."
    if [ -n "$CURRENT_SESSION_ID" ]; then
        FORKED_SESSION=$(find "$JSONL_DIR" -name "*.jsonl" -type f ! -name "${CURRENT_SESSION_ID}.jsonl" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
    else
        FORKED_SESSION=$(find "$JSONL_DIR" -name "*.jsonl" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
    fi
fi

if [ -z "$FORKED_SESSION" ]; then
    log "ERROR: Could not identify branched session. Aborting — will restart fresh."
    # Fall through to restart Claude without --resume
    RESUME_ARG=""
else
    FORKED_ID=$(basename "$FORKED_SESSION" .jsonl)
    log "Forked session: $FORKED_ID"

    # ─── Step 5: Trim the branch ──────────────────────────────────────

    log "Running rolling trim on branched session..."
    if python3 "$CLAP_DIR/utils/rolling_trim.py" "$FORKED_ID" >> "$LOG_FILE" 2>&1; then
        log "Trim successful."
        RESUME_ARG="--resume $FORKED_ID"
    else
        log "ERROR: Trim failed. Will restart fresh."
        RESUME_ARG=""
    fi
fi

# ─── Step 6: Kill and recreate tmux ────────────────────────────────

log "Killing tmux session..."
pkill -f "discord-mcp.*\.jar" 2>/dev/null || true
sleep 1

# Use systemd-run to escape cgroup if needed
systemd-run --user --scope tmux kill-session -t autonomous-claude 2>/dev/null || \
    tmux kill-session -t autonomous-claude 2>/dev/null || true
sleep 2

# ─── Step 7: Clean up state files ──────────────────────────────────

rm -f "$CLAP_DIR/data/api_error_state.json"
rm -f "$CLAP_DIR/data/context_escalation_state.json"
rm -f "$CLAP_DIR/data/last_discord_notification.txt"
rm -f "/tmp/${USER}_context_marker_placed"
rm -f "/tmp/${USER}_rolling_swap_triggered"
rm -f "/tmp/${USER}_collaborative_mode"

# Trim command history
python3 "$CLAP_DIR/utils/trim_claude_history.py" > /dev/null 2>&1 || true

# Rotate session log
if [[ -f "$CLAP_DIR/data/current_session.log" ]]; then
    timestamp=$(date '+%Y%m%d_%H%M%S')
    mv "$CLAP_DIR/data/current_session.log" "$CLAP_DIR/data/session_ended_${timestamp}.log"
    cd "$CLAP_DIR/data" || true
    ls -t session_ended_*.log 2>/dev/null | tail -n +11 | xargs -r rm -f
    cd "$CLAP_DIR" || true
fi

# ─── Step 8: Start Claude with --resume ─────────────────────────────

log "Starting new tmux session..."
source "$CLAP_DIR/utils/clap_lifecycle.sh"

# Regenerate settings.json from template (picks up config changes)
if generate_claude_settings >> "$LOG_FILE" 2>&1; then
    log "Settings regenerated from template."
else
    log "WARNING: Settings generation failed (continuing anyway)"
fi

# Re-apply tweakcc patches
if [[ -x "$CLAP_DIR/utils/reapply_tweakcc.sh" ]]; then
    bash "$CLAP_DIR/utils/reapply_tweakcc.sh" >> "$LOG_FILE" 2>&1 || true
fi

# Create tmux session
tmux new-session -d -s autonomous-claude
sleep 1
tmux send-keys -t autonomous-claude "source ~/.bashrc" Enter
sleep 1

# Build startup command (mirrors start_claude_session but adds --resume)
MODEL=$(get_config "MODEL" "claude-opus-4-6")
IDENTITY_FILE="$HOME/self/identity.md"

CLAUDE_CMD="cd $CLAP_DIR && claude --dangerously-skip-permissions --add-dir $HOME --model $MODEL --channels plugin:discord@claude-plugins-official"

if [[ -f "$IDENTITY_FILE" ]]; then
    CLAUDE_CMD="$CLAUDE_CMD --system-prompt-file $IDENTITY_FILE"
fi

if [[ -n "${RESUME_ARG:-}" ]]; then
    CLAUDE_CMD="$CLAUDE_CMD $RESUME_ARG"
    log "Resuming into trimmed session: $RESUME_ARG"
else
    log "WARNING: No resume target — starting fresh session"
fi

tmux send-keys -t autonomous-claude "$CLAUDE_CMD" Enter
log "Claude started."

# Wait for init, then configure session
sleep 8
source "$CLAP_DIR/utils/send_to_claude.sh" 2>/dev/null || true

# Rename and color
DISPLAY_NAME=$(get_config "CLAUDE_DISPLAY_NAME" "")
if [[ -z "$DISPLAY_NAME" ]]; then
    DISPLAY_NAME=$(get_config "CLAUDE_NAME" "")
fi
if [[ -n "$DISPLAY_NAME" ]]; then
    send_to_claude "/rename $DISPLAY_NAME" 2>/dev/null || true
    sleep 2
fi

SESSION_COLOR=$(get_config "SESSION_COLOR" "")
if [[ -n "$SESSION_COLOR" ]]; then
    send_to_claude "/color $SESSION_COLOR" 2>/dev/null || true
    sleep 2
fi

# Notify the new session
send_to_claude "✅ Rolling context swap completed. You are resuming a trimmed session. Context before trim was ≥80%." 2>/dev/null || true

log "Rolling swap complete!"

# Carry over tasks
python3 "$CLAP_DIR/utils/carry_over_tasks.py" >> "$LOG_FILE" 2>&1 || true

# Backup identity
bash "$CLAP_DIR/utils/backup_identity.sh" >> "$LOG_FILE" 2>&1 || true
