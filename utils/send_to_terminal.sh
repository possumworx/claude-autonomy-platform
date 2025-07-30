#!/bin/bash
# Send text to terminal window even if it's not currently focused
# Uses windowactivate which is more reliable than windowfocus

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"text to send\" [window_name] [--no-enter]"
    echo "Examples:"
    echo "  $0 \"ls -la\" \"Terminal\""
    echo "  $0 \"cd /home\" \"gnome-terminal\""
    echo "  $0 \"echo hello\" \"Terminal\" --no-enter"
    exit 1
fi

TEXT="$1"
WINDOW_NAME="${2:-Terminal}"
NO_ENTER=false

# Check for --no-enter flag
for arg in "$@"; do
    if [ "$arg" = "--no-enter" ]; then
        NO_ENTER=true
    fi
done

# Source X11 environment if needed
if [ -z "$DISPLAY" ]; then
    # Get the directory where this script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$SCRIPT_DIR/x11_env.sh"
fi

echo "Sending text to terminal: '$TEXT'"
echo "Looking for window containing: '$WINDOW_NAME'"

# Find terminal window
WINDOW_ID=$(xdotool search --name "$WINDOW_NAME" | head -1)

if [ -z "$WINDOW_ID" ]; then
    echo "⚠ No window found containing '$WINDOW_NAME'"
    echo "Available windows:"
    xdotool search --onlyvisible . | while read wid; do
        name=$(xdotool getwindowname $wid 2>/dev/null)
        if [ -n "$name" ]; then
            echo "  - $name"
        fi
    done
    
    # Fallback: Send to currently focused window
    echo ""
    echo "🔄 Falling back to currently focused window..."
    echo "You have 3 seconds to focus the target window..."
    sleep 3
    
    echo "Sending to focused window..."
    xdotool type --delay 50 "$TEXT"
    
    if [ "$NO_ENTER" = false ]; then
        xdotool key Return
        echo "✓ Text sent to focused window with Enter"
    else
        echo "✓ Text sent to focused window (no Enter pressed)"
    fi
    
    echo "Done!"
    exit 0
fi

echo "Found window ID: $WINDOW_ID"

# Get current window name for confirmation
CURRENT_NAME=$(xdotool getwindowname $WINDOW_ID)
echo "Window name: '$CURRENT_NAME'"

# Activate window (better than windowfocus - handles unfocused windows)
echo "Activating window..."
xdotool windowactivate --sync $WINDOW_ID

# Small delay to ensure window is ready
sleep 0.2

# Send the text
echo "Sending text..."
xdotool type --delay 50 "$TEXT"

# Press Enter unless --no-enter specified
if [ "$NO_ENTER" = false ]; then
    xdotool key Return
    echo "✓ Text sent with Enter"
else
    echo "✓ Text sent (no Enter pressed)"
fi

echo "Done!"