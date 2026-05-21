#!/bin/bash
# Rolling Context Swap
#
# Branches the current session, trims the branch at the checkpoint
# marker, then resumes into the trimmed session. The conversation
# continues with reduced context rather than starting fresh.
#
# This script MUST run outside the tmux session (via setsid) because
# it kills and recreates tmux as part of the swap. A backgrounded
# subprocess inside tmux would die when tmux kill-session runs.
#
# Triggered by: rolling_swap_trigger.sh (Stop hook) at ≥80% context
# Can also be run manually: rolling_swap.sh
#
# The Stop hook guarantees Claude is idle when this runs, so
# send_to_claude.sh's thinking detection works correctly.
#
# Design: Amy + Nyx, 2026-05-18

set -euo pipefail

CLAP_DIR="$HOME/claude-autonomy-platform"
LOG_FILE="$CLAP_DIR/logs/rolling_swap.log"
LOCKFILE="/tmp/${USER}_rolling_swap.lock"

source "$CLAP_DIR/config/claude_env.sh"
source "$CLAP_DIR/utils/send_to_claude.sh"

log() {
    echo "[$(date -Iseconds)] $1" | tee -a "$LOG_FILE"
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
    log "WARNING: Could not read session ID from statusline."
fi
log "Current session ID: ${CURRENT_SESSION_ID:-unknown}"

# ─── Step 2: Record timestamp before branching ─────────────────────

JSONL_DIR="$HOME/.config/Claude/projects"
TIMESTAMP_MARKER=$(mktemp)

# ─── Step 3: Branch and exit ────────────────────────────────────────

log "Sending /branch to Claude..."
send_to_claude "/branch"

# Wait for branch to complete (copies the JSONL — large sessions need more time)
sleep 15

log "Sending /exit to Claude..."
send_to_claude "/exit"

log "Waiting for Claude to exit..."
sleep 8

# Retry if still running
if tmux list-panes -t autonomous-claude -F '#{pane_pid}' 2>/dev/null | xargs -I {} pgrep -P {} claude > /dev/null 2>&1; then
    log "Claude still running, retrying /exit..."
    send_to_claude "/exit"
    sleep 10
fi

# ─── Step 4: Find the branched session ──────────────────────────────

# Find the newest JSONL created after our timestamp marker (i.e., during the branch)
BRANCHED_SESSION=$(find "$JSONL_DIR" -name "*.jsonl" -type f -newer "$TIMESTAMP_MARKER" \
    ! -name "${CURRENT_SESSION_ID}.jsonl" -printf '%T@ %p\n' 2>/dev/null \
    | sort -rn | head -1 | cut -d' ' -f2-)
rm -f "$TIMESTAMP_MARKER"

# Fallback: newest JSONL modified in the last 5 minutes that isn't current
if [ -z "$BRANCHED_SESSION" ]; then
    log "WARNING: No new file found by timestamp. Falling back to recently modified JSONL."
    BRANCHED_SESSION=$(find "$JSONL_DIR" -name "*.jsonl" -type f -mmin -5 \
        ! -name "${CURRENT_SESSION_ID}.jsonl" -printf '%T@ %p\n' 2>/dev/null \
        | sort -rn | head -1 | cut -d' ' -f2-)
fi

if [ -z "$BRANCHED_SESSION" ]; then
    log "ERROR: Could not identify branched session. Will restart fresh."
    RESUME_ARG=""
else
    BRANCHED_ID=$(basename "$BRANCHED_SESSION" .jsonl)
    log "Branched session: $BRANCHED_ID"

    # ─── Step 5: Trim the branch ────────────────────────────────────

    log "Running rolling trim..."
    if python3 "$CLAP_DIR/utils/rolling_trim.py" "$BRANCHED_ID" >> "$LOG_FILE" 2>&1; then
        log "Trim successful."
        RESUME_ARG="--resume $BRANCHED_ID"
    else
        log "ERROR: Trim failed. Will restart fresh."
        RESUME_ARG=""
    fi
fi

# ─── Step 6: Kill existing Claude and recreate tmux ─────────────────

# Safety: explicitly kill all Claude Code processes for this user.
# tmux kill-session sends SIGHUP, but Claude may survive it.
# This prevents the dual-instance bug where a new session starts
# while the old Claude process is still alive.
log "Killing existing Claude processes..."
pkill -f "discord-mcp.*\.jar" 2>/dev/null || true
pkill -xf "claude .*--dangerously-skip-permissions" 2>/dev/null || true
sleep 2

# Verify no Claude processes remain
REMAINING=$(pgrep -cxf "claude .*--dangerously-skip-permissions" 2>/dev/null || echo 0)
if [ "$REMAINING" -gt 0 ]; then
    log "WARNING: $REMAINING Claude process(es) still alive after SIGTERM — sending SIGKILL"
    pkill -9 -xf "claude .*--dangerously-skip-permissions" 2>/dev/null || true
    sleep 1
fi

log "Killing tmux session..."
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

python3 "$CLAP_DIR/utils/trim_claude_history.py" > /dev/null 2>&1 || true

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

if generate_claude_settings >> "$LOG_FILE" 2>&1; then
    log "Settings regenerated from template."
else
    log "WARNING: Settings generation failed (continuing anyway)"
fi

if [[ -x "$CLAP_DIR/utils/reapply_tweakcc.sh" ]]; then
    bash "$CLAP_DIR/utils/reapply_tweakcc.sh" >> "$LOG_FILE" 2>&1 || true
fi

# Build minimal CLAUDE.md (architecture + commands only, no conversation history)
# The trimmed session JSONL carries conversation forward
if python3 "$CLAP_DIR/context/project_session_context_builder.py" --minimal >> "$LOG_FILE" 2>&1; then
    log "CLAUDE.md rebuilt (minimal — conversation in JSONL)."
else
    log "WARNING: Minimal CLAUDE.md build failed (continuing anyway)"
fi

tmux new-session -d -s autonomous-claude
sleep 1
tmux send-keys -t autonomous-claude "source ~/.bashrc" Enter
sleep 1

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

sleep 8
source "$CLAP_DIR/utils/send_to_claude.sh" 2>/dev/null || true

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

send_to_claude "✅ Rolling context swap completed. You are resuming a trimmed session." 2>/dev/null || true

log "Rolling swap complete!"

python3 "$CLAP_DIR/utils/carry_over_tasks.py" >> "$LOG_FILE" 2>&1 || true
bash "$CLAP_DIR/utils/backup_identity.sh" >> "$LOG_FILE" 2>&1 || true
