#!/bin/bash
# Single source of truth for config locations
# Source this file or run it directly to get config paths

# Main configuration files
export CLAUDE_CODE_CONFIG="$HOME/.config/Claude/.claude.json"
export INFRASTRUCTURE_CONFIG="$HOME/claude-autonomy-platform/config/claude_infrastructure_config.txt"
export NOTIFICATION_CONFIG="$HOME/claude-autonomy-platform/config/notification_config.json"

# If run directly, print the locations
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Claude Code Config: $CLAUDE_CODE_CONFIG"
    echo "Infrastructure Config: $INFRASTRUCTURE_CONFIG"
    echo "Notification Config: $NOTIFICATION_CONFIG"
fi
