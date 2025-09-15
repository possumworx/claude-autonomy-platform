#!/bin/bash
# Parse both natural and personal commands for inclusion in session context

echo "## Available Natural Commands"
echo ""

# Parse natural commands
if [ -f ~/claude-autonomy-platform/config/natural_commands.sh ]; then
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
fi

# Check for swap function
if grep -q "^swap()" ~/claude-autonomy-platform/config/natural_commands.sh 2>/dev/null; then
    comment=$(grep -A1 "^swap()" ~/claude-autonomy-platform/config/natural_commands.sh | tail -1 | grep -o '#.*' | sed 's/^# *//')
    echo "- **swap**: $comment"
fi

echo ""
echo "## Personal Natural Commands"
echo ""

# Parse personal commands if they exist
if [ -f ~/claude-autonomy-platform/config/personal_commands.sh ]; then
    grep "^alias" ~/claude-autonomy-platform/config/personal_commands.sh | while IFS= read -r line; do
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
fi