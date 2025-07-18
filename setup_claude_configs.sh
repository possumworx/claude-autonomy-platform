#!/bin/bash
# Claude Infrastructure Configuration Setup
# Simple wrapper around the Python setup script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/setup_claude_configs.py"

echo "🔧 Claude Infrastructure Configuration Setup"
echo "============================================="

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Setup script not found: $PYTHON_SCRIPT"
    exit 1
fi

# Run the Python setup script
python3 "$PYTHON_SCRIPT" "$@"

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Restart Claude Code session to pick up new MCP configurations"
    echo "2. Restart Claude Desktop if running"
    echo "3. Test MCP servers with /mcp command"
else
    echo ""
    echo "❌ Setup failed. Check error messages above."
    exit 1
fi