#!/bin/bash
# Natural Commands for Claude Autonomy Platform
# This file is sourced by ~/.bashrc and parsed for session context
# 
# Format: alias name='command'
# Comments starting with # are included in help

# Core System Management
alias swap='~/claude-autonomy-platform/utils/session_swap.sh'  # Trigger session swap with keyword
alias check_health='~/claude-autonomy-platform/utils/check_health'  # Check system health status

# Discord Communication
alias read_channel='~/claude-autonomy-platform/discord/read_channel'  # Read Discord messages by channel name
# alias write_channel='~/claude-autonomy-platform/discord/write_channel'  # TODO: Send Discord message by channel name

# Quick Navigation
alias clap='cd ~/claude-autonomy-platform'  # Navigate to ClAP directory
alias home='cd ~/delta-home'  # Navigate to personal home directory

# Gaming
alias game='cd ~/delta-home/games/if && frotz'  # Launch interactive fiction with Frotz
alias dreamhold='cd ~/delta-home/games/if && frotz ~/delta-home/games/if/Dreamhold.z8'  # Play The Dreamhold

# Linear Helpers (Note: These need user ID configuration)
# alias linear-helpers='~/claude-autonomy-platform/utils/linear-helpers'  # Show Linear command templates
# alias my-linear-issues='~/claude-autonomy-platform/utils/my-linear-issues'  # TODO: Make generic for any user

# Utility Commands
alias list-commands='grep "^alias" ~/claude-autonomy-platform/config/natural_commands.sh | sed "s/alias //g" | column -t -s "="'  # List all natural commands

# Session Management Helpers
alias context='grep -o "Context: [0-9.]*%" ~/claude-autonomy-platform/logs/autonomous_timer.log | tail -1'  # Show current context usage

# Git Helpers
alias gs='git status'  # Quick git status
alias gd='git diff'  # Quick git diff
alias gl='git log --oneline -10'  # Recent git history
alias oops='git checkout -b fix/$(date +%s) && git push -u origin HEAD'  # Recover from branch protection block

# System Update Helper
alias update='~/claude-autonomy-platform/utils/update_system.sh'  # Pull latest changes and restart services