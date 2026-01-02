#!/bin/bash
# X11 environment variables for desktop automation
# Source this file to access the logged-in desktop session

# Get the directory where this script is located (config directory)
CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to read values from infrastructure config
read_config() {
    local key="$1"
    local config_file="$CONFIG_DIR/claude_infrastructure_config.txt"
    
    if [[ -f "$config_file" ]]; then
        grep "^${key}=" "$config_file" | cut -d'=' -f2-
    fi
}

# Load X11 settings from infrastructure config
DISPLAY_VALUE=$(read_config "DISPLAY")
XAUTH_PATTERN=$(read_config "XAUTH_PATTERN")

# Set environment variables
export DISPLAY=${DISPLAY_VALUE:-:0}

# Handle XAUTHORITY with pattern matching
if [[ -n "$XAUTH_PATTERN" ]]; then
    # Find the actual XAUTHORITY file using the pattern
    XAUTH_FILE=$(ls $XAUTH_PATTERN 2>/dev/null | head -1)
    export XAUTHORITY=${XAUTH_FILE:-/run/user/$(id -u)/gdm/Xauthority}
else
    export XAUTHORITY=/run/user/$(id -u)/gdm/Xauthority
fi

# Verify the environment is working
echo "X11 environment loaded:"
echo "DISPLAY: $DISPLAY"
echo "XAUTHORITY: $XAUTHORITY"