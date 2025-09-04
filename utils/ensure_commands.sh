#!/bin/bash
# Ensure ClAP Commands are Available
# This script checks if ClAP commands are available and sources them if not

# Check if a key command is available
if ! command -v todo &> /dev/null; then
    # Source the init script
    if [ -f "$HOME/claude-autonomy-platform/config/claude_init.sh" ]; then
        source "$HOME/claude-autonomy-platform/config/claude_init.sh"
    fi
fi

# Execute the requested command
"$@"