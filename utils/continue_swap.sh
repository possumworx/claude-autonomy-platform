#!/bin/bash
# Continue swap after manual export
# For use when export has been done manually and we need to compile context and start session

# Load environment and functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../config/claude_env.sh"
source "$SCRIPT_DIR/../utils/claude_state_detector.sh"

# Check if keyword provided
KEYWORD="${1:-NONE}"

echo "📋 Continuing swap with keyword: $KEYWORD"

# Check if export exists
EXPORT_PATH="$CLAP_DIR/context/current_export.txt"
if [[ ! -f "$EXPORT_PATH" ]]; then
    echo "❌ No export found at $EXPORT_PATH"
    echo "Please perform manual export first!"
    exit 1
fi

echo "✅ Found export at $EXPORT_PATH"

# Process the export into swap_CLAUDE.md
echo "📝 Processing conversation history..."
python3 "$CLAP_DIR/utils/update_conversation_history.py" "$EXPORT_PATH"

if [[ $? -ne 0 ]]; then
    echo "❌ Conversation history update failed!"
    exit 1
fi

# Run context builder with keyword
echo "🔨 Building new context with keyword: $KEYWORD"
cd "$CLAP_DIR"
python3 context/project_session_context_builder.py "$KEYWORD"

if [[ $? -ne 0 ]]; then
    echo "❌ Context builder failed!"
    exit 1
fi

echo "✅ Context built successfully"

# Kill and recreate tmux session for stability
echo "🔄 Recreating tmux session for clean start..."
tmux kill-session -t autonomous-claude 2>/dev/null || true
sleep 2
tmux new-session -d -s autonomous-claude

# Load Claude model from infrastructure config
CLAUDE_MODEL=$(grep "^MODEL=" "$CLAP_DIR/config/claude_infrastructure_config.txt" | cut -d'=' -f2-)
CLAUDE_NAME=$(grep "^CLAUDENAME=" "$CLAP_DIR/config/claude_infrastructure_config.txt" | cut -d'=' -f2-)

if [[ -z "$CLAUDE_MODEL" ]]; then
    echo "❌ Unable to read MODEL from config!"
    exit 1
fi

echo "🚀 Starting Claude in fresh tmux session..."
echo "📊 Model: $CLAUDE_MODEL"

# Clear any stray keypresses before starting Claude
tmux send-keys -t autonomous-claude "Enter"

# Send the full Claude command
tmux send-keys -t autonomous-claude "cd $CLAP_DIR && claude --dangerously-skip-permissions --add-dir /home/$CLAUDE_NAME --model $CLAUDE_MODEL"

# Send Enter separately to execute
tmux send-keys -t autonomous-claude "Enter"

echo "✅ Claude started in tmux session"

echo "✅ Swap continuation complete!"