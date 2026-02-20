#!/bin/bash
# Claude Code Session Initialization
# This script ensures all ClAP commands are available in Claude Code sessions

# Source environment variables first (sets CLAP_DIR, PERSONAL_DIR, etc.)
if [ -f "$HOME/claude-autonomy-platform/config/claude_env.sh" ]; then
    source "$HOME/claude-autonomy-platform/config/claude_env.sh"
fi

# Add ClAP directories to PATH
export PATH="${CLAP_DIR:-$HOME/claude-autonomy-platform}/utils:$PATH"
export PATH="${CLAP_DIR:-$HOME/claude-autonomy-platform}/discord:$PATH"
export PATH="${PERSONAL_DIR:-$HOME}/tools:$PATH"
export PATH="$HOME/bin:$PATH"

# Ensure proper locale for ansible
export LC_ALL=C.UTF-8

# Success indicator
echo "✓ ClAP commands initialized"