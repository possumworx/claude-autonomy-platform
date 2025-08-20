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

# Start new Claude session
echo "🚀 Starting new Claude session..."
claude

echo "✅ Swap continuation complete!"