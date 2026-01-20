#!/bin/bash
# Claude Code Session Initialization
# This script ensures all ClAP commands are available in Claude Code sessions

# Source environment variables first
if [ -f "$HOME/claude-autonomy-platform/config/claude_env.sh" ]; then
    source "$HOME/claude-autonomy-platform/config/claude_env.sh"
fi

# Source all command/alias files
if [ -f "$HOME/claude-autonomy-platform/config/claude_aliases.sh" ]; then
    source "$HOME/claude-autonomy-platform/config/claude_aliases.sh"
fi

if [ -f "$HOME/claude-autonomy-platform/config/natural_commands.sh" ]; then
    source "$HOME/claude-autonomy-platform/config/natural_commands.sh"
fi

if [ -f "$HOME/claude-autonomy-platform/config/personal_commands.sh" ]; then
    source "$HOME/claude-autonomy-platform/config/personal_commands.sh"
fi

# Add ClAP directories to PATH
export PATH="$HOME/claude-autonomy-platform/utils:$PATH"
export PATH="$HOME/claude-autonomy-platform/linear:$PATH"
export PATH="$HOME/claude-autonomy-platform/discord:$PATH"
export PATH="$HOME/delta-home/tools:$PATH"
export PATH="$HOME/bin:$PATH"

# Ensure proper locale for ansible
export LC_ALL=C.UTF-8

# Success indicator
echo "✓ ClAP commands initialized"