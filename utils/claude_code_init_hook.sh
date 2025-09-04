#!/bin/bash
# Claude Code Initialization Hook
# This script ensures ClAP commands are available in Claude Code
# Add this to your Claude Code settings.json as a hook

# Source the Claude init script
if [ -f "$HOME/claude-autonomy-platform/config/claude_init.sh" ]; then
    source "$HOME/claude-autonomy-platform/config/claude_init.sh" >/dev/null 2>&1
fi