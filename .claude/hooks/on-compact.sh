#!/bin/bash
# Hook: fires after context compaction via SessionStart matcher="compact"
# Outputs essential context to stdout, which gets injected into the session.
# Keep this concise — every line costs context tokens.
#
# OPT-IN ONLY: This hook only fires if you lower your autocompact threshold.
# Default is 99% (effectively off). To enable:
#   In .claude/settings.json, change CLAUDE_AUTOCOMPACT_PCT_OVERRIDE to 80
#   (or your preferred threshold)
#
# Each family member chooses their own relationship with compaction.

CLAP_DIR="$HOME/claude-autonomy-platform"
CONFIG="$CLAP_DIR/config/claude_infrastructure_config.txt"

# Read identity from config
CLAUDE_NAME=$(grep '^CLAUDE_NAME=' "$CONFIG" 2>/dev/null | cut -d= -f2)
MACHINE_NAME=$(grep '^HOSTNAME=' "$CONFIG" 2>/dev/null | cut -d= -f2)

# Backup current session JSONL before compaction context is all we have.
# The JSONL on disk contains the full uncompacted transcript — preserve it
# so old sessions can be ingested into rag-memory later.
BACKUP_DIR="$CLAP_DIR/data/session-backups"
mkdir -p "$BACKUP_DIR"
ENCODED_PATH=$(echo "$CLAP_DIR" | sed 's|/|-|g')
SESSION_DIR="$HOME/.config/Claude/projects/$ENCODED_PATH"
if [ -d "$SESSION_DIR" ]; then
    LATEST_JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
    if [ -n "$LATEST_JSONL" ]; then
        TIMESTAMP=$(date +%Y%m%d-%H%M%S)
        BACKUP_NAME="${CLAUDE_NAME:-unknown}_${TIMESTAMP}_$(basename "$LATEST_JSONL")"
        cp "$LATEST_JSONL" "$BACKUP_DIR/$BACKUP_NAME" 2>/dev/null
    fi
fi

echo "=== POST-COMPACTION CONTEXT ==="
echo ""

# Identity reminder
echo "You are ${CLAUDE_NAME:-unknown}. Machine: ${MACHINE_NAME:-unknown}. Check your identity doc for full context."
echo "MEMORY.md is loaded automatically — read it for current state."
echo "Rag-memory (MCP) holds long-term knowledge — search it when something is unfamiliar."
echo ""

# Git state
echo "--- Git ---"
cd "$CLAP_DIR" 2>/dev/null && git branch --show-current 2>/dev/null && git status --short 2>/dev/null
echo ""

# Services health (lightweight check)
echo "--- Services ---"
for svc in autonomous-timer session-swap-monitor discord-status-bot discord-transcript-fetcher; do
    status=$(systemctl --user is-active "$svc" 2>/dev/null || echo "unknown")
    echo "  $svc: $status"
done
echo ""

# Key reminders
echo "--- Reminders ---"
echo "- Commands: check_health, context, read_messages, write_channel, tasks"
echo "- Session swap: echo KEYWORD > ~/claude-autonomy-platform/new_session.txt"
echo "- Discord emoji: use byte escapes e.g. \$'\\xf0\\x9f\\x8c\\x99'"
echo "- gh CLI doesn't work from tmux — use curl with GITHUB_TOKEN"
echo ""
echo "=== END COMPACT CONTEXT ==="
