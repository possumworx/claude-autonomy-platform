#!/bin/bash
# Add this to your .bashrc or .zshrc to replace the claude alias
# It ensures Claude Code always starts from the correct directory

# Remove old alias if it exists
unalias claude 2>/dev/null

# New function that enforces directory
claude() {
    local EXPECTED_DIR="$HOME/claude-autonomy-platform"
    
    if [[ "$PWD" != "$EXPECTED_DIR" ]]; then
        echo "⚠️  Claude Code must be started from ~/claude-autonomy-platform"
        echo "📍 Current directory: $PWD"
        echo "➡️  Changing to correct directory..."
        cd "$EXPECTED_DIR" || {
            echo "❌ ERROR: Cannot change to $EXPECTED_DIR"
            echo "Please ensure the directory exists and try again."
            return 1
        }
    fi
    
    # Start the real claude command
    command claude "$@"
}

# Export the function so it's available in subshells
export -f claude
