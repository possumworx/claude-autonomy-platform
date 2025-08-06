#!/bin/bash
# Parse natural commands for inclusion in session context

echo "## Available Natural Commands"
echo ""
grep "^alias" ~/claude-autonomy-platform/config/natural_commands.sh | while IFS= read -r line; do
    # Extract alias name and command
    alias_name=$(echo "$line" | sed 's/alias \([^=]*\)=.*/\1/')
    command=$(echo "$line" | sed 's/alias [^=]*=\(.*\)/\1/' | sed 's/  *#.*//')
    comment=$(echo "$line" | grep -o '#.*' | sed 's/^# *//')
    
    if [ -n "$comment" ]; then
        echo "- **$alias_name**: $comment"
    else
        echo "- **$alias_name**: $command"
    fi
done