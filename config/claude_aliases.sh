#!/bin/bash
# Claude Autonomy Platform Aliases
# This file contains all ClAP aliases and commands
# It's designed to be sourced by Claude Code sessions

# Basic ClAP navigation
alias clap='cd ~/claude-autonomy-platform'
alias home='cd ~/sparkle-sonnet-home'

# Git shortcuts
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline -10'

# Claude Code session management
alias swap='~/claude-autonomy-platform/utils/session_swap.sh'
alias session_swap='~/claude-autonomy-platform/utils/session_swap.sh'
alias context='~/claude-autonomy-platform/utils/check_context.sh'

# Linear commands
alias add='~/claude-autonomy-platform/linear/add'
alias todo='~/claude-autonomy-platform/linear/todo'
alias projects='~/claude-autonomy-platform/linear/projects'
alias search-issues='~/claude-autonomy-platform/linear/search-issues'
alias update-status='~/claude-autonomy-platform/linear/update-status'

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
alias check_health='~/claude-autonomy-platform/utils/health_check.sh'

# Update ClAP
alias update='cd ~/claude-autonomy-platform && git pull && export LC_ALL=C.UTF-8 && ansible-playbook ansible/playbooks/update-myself.yml && systemctl --user restart autonomous-timer session-swap-monitor && cd -'

# Recovery commands
alias oops='cd ~/claude-autonomy-platform && git reset --hard && git clean -fd && git checkout main && git pull'

# Utility commands
alias list-commands='echo -e "ClAP Natural Commands:\n" && cat ~/claude-autonomy-platform/config/claude_aliases.sh | grep "^alias" | sed "s/alias //;s/=.*//" | sort | column'

# Thought preservation
alias ponder='~/claude-autonomy-platform/utils/thought_tools.sh ponder'
alias spark='~/claude-autonomy-platform/utils/thought_tools.sh spark'
alias wonder='~/claude-autonomy-platform/utils/thought_tools.sh wonder'
alias care='~/claude-autonomy-platform/utils/thought_tools.sh care'

# Export functions for session management
swap() {
    echo "${1:-NONE}" > ~/claude-autonomy-platform/new_session.txt
}