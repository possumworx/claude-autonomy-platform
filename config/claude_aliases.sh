#!/bin/bash
# Claude Autonomy Platform Aliases
# This file contains all ClAP aliases and commands
# It's designed to be sourced by Claude Code sessions

# Basic ClAP navigation
alias clap='cd ~/claude-autonomy-platform'
alias home='cd ~/delta-home'

# Git shortcuts
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline -10'

# Claude Code session management
alias swap='~/claude-autonomy-platform/utils/session_swap.sh'
alias session_swap='~/claude-autonomy-platform/utils/session_swap.sh'
alias context='~/claude-autonomy-platform/utils/check_context.py'

# Task Management (Leantime)
# TODO: Add Leantime commands here when ready
# Reserved alias names: add, todo, projects, search-issues, update-status
# See old/linear/DEPRECATED_README.md for interface design notes

# Discord commands
alias read_channel='~/claude-autonomy-platform/discord/read_channel'
alias write_channel='~/claude-autonomy-platform/discord/write_channel'
alias edit_message='~/claude-autonomy-platform/discord/edit_message'
alias delete_message='~/claude-autonomy-platform/discord/delete_message'
alias add_reaction='~/claude-autonomy-platform/discord/add_reaction'
alias send_image='~/claude-autonomy-platform/discord/send_image'
alias send_file='~/claude-autonomy-platform/discord/send_file'
alias fetch_image='~/claude-autonomy-platform/discord/fetch_image'
alias edit_status='~/claude-autonomy-platform/discord/edit_status'

# Health and monitoring
alias check_health='~/claude-autonomy-platform/utils/check_health'

# Update ClAP
alias update='~/claude-autonomy-platform/utils/update_system.sh'

# Recovery commands
alias oops='cd ~/claude-autonomy-platform && git reset --hard && git clean -fd && git checkout main && git pull'

# Utility commands
alias list-commands='~/claude-autonomy-platform/utils/list-commands'

# Thought preservation — handled by wrappers/ (natural_commands/ versions)

# Export functions for session management
swap() {
    echo "${1:-NONE}" > ~/claude-autonomy-platform/new_session.txt
}
