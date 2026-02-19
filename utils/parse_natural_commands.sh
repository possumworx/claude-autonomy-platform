#!/bin/bash
# Parse available commands from wrappers directory for session context
# Reads the comment on line 2 of each wrapper script as the description

WRAPPERS_DIR="$HOME/claude-autonomy-platform/wrappers"

echo "## Available Natural Commands"
echo ""

for wrapper in "$WRAPPERS_DIR"/*; do
    [ -f "$wrapper" ] || continue
    name=$(basename "$wrapper")
    # Extract description from line 2 comment (# Description text)
    description=$(sed -n '2s/^# *//p' "$wrapper" 2>/dev/null)
    if [ -n "$description" ]; then
        echo "- **$name**: $description"
    else
        echo "- **$name**"
    fi
done
