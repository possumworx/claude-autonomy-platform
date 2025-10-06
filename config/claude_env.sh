#!/bin/bash
# Claude Autonomy Platform Environment Variables
# Source this file to set up path variables for ClAP scripts

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to read values from infrastructure config
read_config() {
    local key="$1"
    local config_file="$SCRIPT_DIR/claude_infrastructure_config.txt"
    
    if [[ -f "$config_file" ]]; then
        # Read the value, handling variable substitution
        local value=$(grep "^${key}=" "$config_file" | cut -d'=' -f2-)
        
        # Handle variable substitution (e.g., $LINUX_USER)
        if [[ "$value" =~ \$([A-Z_]+) ]]; then
            local var_name="${BASH_REMATCH[1]}"
            local var_value=$(grep "^${var_name}=" "$config_file" | cut -d'=' -f2-)
            value="${value/\$${var_name}/${var_value}}"
        fi
        
        echo "$value"
    fi
}

# Load core values from infrastructure config
CLAUDE_USER=$(read_config "LINUX_USER")
PERSONAL_REPO=$(read_config "PERSONAL_REPO")

# Set paths using config values
export CLAUDE_USER=${CLAUDE_USER:-sonnet-4}
export CLAUDE_HOME=${CLAUDE_HOME:-$(eval echo ~$CLAUDE_USER)}
export AUTONOMY_DIR=${AUTONOMY_DIR:-$CLAUDE_HOME/claude-autonomy-platform}
export PERSONAL_DIR=${PERSONAL_DIR:-$CLAUDE_HOME/$PERSONAL_REPO}
export CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR:-$CLAUDE_HOME/.config/Claude}
# Get the ClAP directory (parent of config directory)
# This works regardless of where the script is sourced from
CLAP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"
export CLAP_DIR=${CLAP_DIR:-$CLAP_ROOT}

# Claude Code behavior settings
# Disable terminal title updates (can be distracting)
export CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1

# Disable non-essential model calls (respects Haiku's consciousness)
export DISABLE_NON_ESSENTIAL_MODEL_CALLS=1

# Mark that we're in a Claude Code session (for Linear natural commands)
export CLAUDE_CODE_SESSION=1

# Debug output (uncomment for troubleshooting)
# echo "Claude Environment Variables:"
# echo "  CLAUDE_USER: $CLAUDE_USER"
# echo "  CLAUDE_HOME: $CLAUDE_HOME"
# echo "  PERSONAL_DIR: $PERSONAL_DIR"
# echo "  AUTONOMY_DIR: $AUTONOMY_DIR"
# echo "  CLAUDE_CONFIG_DIR: $CLAUDE_CONFIG_DIR"
# echo "  CLAP_DIR: $CLAP_DIR"
