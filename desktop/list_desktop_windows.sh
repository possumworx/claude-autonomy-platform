#!/bin/bash
# List all windows on the desktop to help find terminals

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source X11 environment if needed
if [ -z "$DISPLAY" ]; then
    if [ -f "$SCRIPT_DIR/x11_env.sh" ]; then
        source "$SCRIPT_DIR/x11_env.sh"
    else
        echo "Warning: x11_env.sh not found - X11 environment may not be set"
    fi
fi

echo "=== Desktop Windows ==="
xdotool search --onlyvisible . | while read window_id; do
    window_name=$(xdotool getwindowname $window_id 2>/dev/null)
    if [ -n "$window_name" ]; then
        echo "ID: $window_id - Name: $window_name"
    fi
done

echo ""
echo "=== Terminal-like Windows ==="
xdotool search --onlyvisible . | while read window_id; do
    window_name=$(xdotool getwindowname $window_id 2>/dev/null)
    if echo "$window_name" | grep -i -E "(terminal|konsole|xterm|gnome-terminal)" >/dev/null; then
        echo "Terminal found - ID: $window_id - Name: $window_name"
    fi
done