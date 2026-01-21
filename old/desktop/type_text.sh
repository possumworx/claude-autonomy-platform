#!/bin/bash

# Simple text typing tool using xdotool
# Usage: ./type_text.sh "text to type"

# Source X11 environment if needed
if [ -z "$DISPLAY" ]; then
    source "/home/sonnet-4/claude-autonomy-platform/x11_env.sh"
fi

if [ $# -lt 1 ]; then
    echo "Usage: $0 \"text to type\""
    exit 1
fi

text="$1"

# Type the text
xdotool type "$text"

echo "Typed: $text"