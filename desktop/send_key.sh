#!/bin/bash

# Simple key sending tool using xdotool
# Usage: ./send_key.sh <key>
# Examples: Return, ctrl+c, alt+Tab, F1

# Source X11 environment if needed
if [ -z "$DISPLAY" ]; then
    source "/home/sonnet-4/claude-autonomy-platform/x11_env.sh"
fi

if [ $# -lt 1 ]; then
    echo "Usage: $0 <key>"
    echo "Examples: Return, ctrl+c, alt+Tab, F1"
    exit 1
fi

key="$1"

# Send the key
xdotool key "$key"

echo "Sent key: $key"