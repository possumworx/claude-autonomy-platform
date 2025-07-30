#!/bin/bash

# Simple screenshot tool using scrot
# Usage: ./screenshot.sh [filename]

# Source X11 environment if needed
if [ -z "$DISPLAY" ]; then
    source "/home/sonnet-4/claude-autonomy-platform/x11_env.sh"
fi

# Default filename with timestamp
if [ -z "$1" ]; then
    filename="/tmp/screenshot_$(date +%Y%m%d_%H%M%S).png"
else
    filename="$1"
fi

# Take screenshot
scrot "$filename"

echo "Screenshot saved to: $filename"