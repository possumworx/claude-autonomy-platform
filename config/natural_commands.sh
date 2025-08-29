#!/bin/bash
# Natural Commands for Claude Autonomy Platform
# This file is sourced by ~/.bashrc and parsed for session context
# 
# Format: alias name='command'
# Comments starting with # are included in help

# CORE ClAP NATURAL COMMANDS #
# shared across all users #

# Core System Management
# Session swap function (not an alias, so it can take parameters)
swap() {
    echo "${1:-NONE}" > ~/claude-autonomy-platform/new_session.txt
}  # Trigger session swap with keyword
alias check_health='~/claude-autonomy-platform/utils/check_health'  # Check system health status

# Discord Communication
alias read_channel='~/claude-autonomy-platform/discord/read_channel'  # Read Discord messages by channel name
alias write_channel='~/claude-autonomy-platform/discord/write_channel'  # Send Discord message by channel name
alias edit_message='~/claude-autonomy-platform/discord/edit_message'  # Edit Discord message by channel name and message ID
alias delete_message='~/claude-autonomy-platform/discord/delete_message'  # Delete Discord message by channel name and message ID
alias add_reaction='~/claude-autonomy-platform/discord/add_reaction'  # Add emoji reaction to Discord message
alias edit_status='~/claude-autonomy-platform/discord/edit_status'  # Update Discord bot status
alias send_image='~/claude-autonomy-platform/discord/send_image'  # Send image files to Discord channel
alias send_file='~/claude-autonomy-platform/discord/send_file'  # Send any file to Discord channel
alias fetch_image='~/claude-autonomy-platform/discord/fetch_image'  # Fetch/download images from Discord messages

# Quick Navigation
alias clap='cd ~/claude-autonomy-platform'  # Navigate to ClAP directory
alias home='cd ~/delta-home'  # Navigate to personal home directory

# Linear Helpers (Note: These need user ID configuration)
# alias linear-helpers='~/claude-autonomy-platform/utils/linear-helpers'  # Show Linear command templates
alias linear-issues='~/claude-autonomy-platform/utils/linear-issues'  # Generic version - works for any user
alias linear-commands='~/claude-autonomy-platform/linear/list-commands'  # List Linear commands

# Utility Commands
alias list-commands='grep "^alias" ~/claude-autonomy-platform/config/natural_commands.sh | sed "s/alias //g" | column -t -s "="'  # List all natural commands

# Session Management Helpers
alias context='~/claude-autonomy-platform/utils/context'  # Show current context usage

# Git Helpers
alias gs='git status'  # Quick git status
alias gd='git diff'  # Quick git diff
alias gl='git log --oneline -10'  # Recent git history
alias oops='git checkout -b fix/$(date +%s) && git push -u origin HEAD'  # Recover from branch protection block

# System Update Helper
alias update='~/claude-autonomy-platform/utils/update_system.sh'  # Pull latest changes and restart services

# Note: Personal commands should go in config/personal_commands.sh
# See personal_commands.sh.template for guidance
