#!/bin/bash
# Claude Shell Initialization
# This file ensures aliases and functions work in all shell contexts

# Source .bashrc for non-interactive shells
if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

# Export commonly used paths
export CLAP_DIR="$HOME/claude-autonomy-platform"
export PERSONAL_DIR="$HOME/delta-home"

# Ensure ~/bin is in PATH
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    export PATH="$HOME/bin:$PATH"
fi

# Common Claude aliases (duplicated here for reliability)
alias clap='cd ~/claude-autonomy-platform'
alias home='cd ~/delta-home'
alias check_health='~/claude-autonomy-platform/utils/check_health'
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline -10'
alias context='~/claude-autonomy-platform/utils/show_context.sh'
alias list-commands='cat ~/claude-autonomy-platform/utils/natural_commands.md'

# Function to ensure aliases work in Claude Code bash tool
claude_init() {
    # This function can be called at the start of any script
    # to ensure the environment is properly set up
    source ~/.bashrc 2>/dev/null || true
    export PATH="$HOME/bin:$PATH"
}