#!/bin/bash
# Session Swap Script for Claude
# Updates context, backs up work, and swaps to fresh session
# Usage: session_swap.sh [KEYWORD]

# Load path utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../config/claude_env.sh"

# Function to read values from infrastructure config
read_config() {
    local key="$1"
    local config_file="$SCRIPT_DIR/../config/claude_infrastructure_config.txt"
    
    if [[ -f "$config_file" ]]; then
        grep "^${key}=" "$config_file" | cut -d'=' -f2-
    fi
}

# Load Claude model from config
CLAUDE_MODEL=$(read_config "MODEL")
CLAUDE_MODEL=${CLAUDE_MODEL:-claude-sonnet-4-20250514}

KEYWORD=${1:-"NONE"}
echo "[SESSION_SWAP] Context keyword: $KEYWORD"

echo "[SESSION_SWAP] Backing up work to git..."
cd "$PERSONAL_DIR"
git add -A
git commit -m "Autonomous session backup - $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main
echo "[SESSION_SWAP] Backup complete!"

# Return to CLAP directory after git operations
cd "$CLAP_DIR"

echo "[SESSION_SWAP] Finding most recent conversation export..."
# Find the most recent export file
export_dir="$CLAP_DIR/context"
most_recent_export=$(ls -t "$export_dir"/session_*.txt 2>/dev/null | head -1)

if [[ -n "$most_recent_export" ]]; then
    echo "[SESSION_SWAP] Using export: $(basename "$most_recent_export")"
    # Parse and update swap_CLAUDE.md
    python3 "$CLAP_DIR/utils/update_conversation_history.py" "$most_recent_export"
else
    echo "[SESSION_SWAP] No recent exports found, creating new export..."
    # Fallback: create a fresh export if none exist
    export_path="$export_dir/temp-export.txt"
    tmux send-keys -t autonomous-claude "/export $export_path" 
    sleep 1
    tmux send-keys -t autonomous-claude "Enter"
    # Wait for export to complete
    sleep 5
    if [[ -f "$export_path" ]]; then
        echo "[SESSION_SWAP] Fresh export created"
        python3 "$CLAP_DIR/utils/update_conversation_history.py" "$export_path"
    else
        echo "[SESSION_SWAP] Warning: Export failed, continuing with existing context"
    fi
fi

echo "[SESSION_SWAP] Updating context with keyword: $KEYWORD"
# Temporarily write keyword for context builder
echo "$KEYWORD" > "$CLAP_DIR/new_session.txt"
python3 "$CLAP_DIR/context/project_session_context_builder.py"
# Reset to FALSE after context building
echo "FALSE" > "$CLAP_DIR/new_session.txt"

echo "[SESSION_SWAP] Swapping to new session..."
tmux send-keys -t autonomous-claude "Enter"
sleep 3
tmux send-keys -t autonomous-claude "/exit"
sleep 3
tmux send-keys -t autonomous-claude "Enter"
sleep 10
tmux send-keys -t autonomous-claude "cd $CLAP_DIR && claude --dangerously-skip-permissions --add-dir ~ --model $CLAUDE_MODEL"
tmux send-keys -t autonomous-claude "Enter"

echo "[SESSION_SWAP] Session swap complete!"
