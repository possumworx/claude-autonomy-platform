#!/bin/bash

# Simple click tool using xdotool
# Usage: ./click.sh <x> <y> [button]
# Button: 1=left (default), 2=middle, 3=right

# Source X11 environment if needed
if [ -z "$DISPLAY" ]; then
    source "/home/sonnet-4/claude-autonomy-platform/x11_env.sh"
fi

if [ $# -lt 2 ]; then
    echo "Usage: $0 <x> <y> [button]"
    echo "Button: 1=left (default), 2=middle, 3=right"
    exit 1
fi

x="$1"
y="$2"
button="${3:-1}"

# Move to position and click
xdotool mousemove "$x" "$y"
xdotool click "$button"

echo "Clicked at ($x, $y) with button $button"