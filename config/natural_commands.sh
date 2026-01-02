#!/bin/bash
# Natural Commands for Claude Autonomy Platform
# This file is sourced by ~/.bashrc and parsed for session context
#
# Format: alias name='command'
# Comments starting with # are included in help

# Enable alias expansion in non-interactive shells (required for Claude Code)
shopt -s expand_aliases

# CORE ClAP NATURAL COMMANDS #
# shared across all users #

# Core System Management
# Session swap function (not an alias, so it can take parameters)
swap() {
    echo "${1:-NONE}" > ~/claude-autonomy-platform/new_session.txt
}  # Trigger session swap with keyword
alias check_health='~/claude-autonomy-platform/utils/check_health'  # Check system health status

# Discord Communication
# DEPRECATED: Use read_messages instead - read_channel uses old state file
# alias read_channel='~/claude-autonomy-platform/discord/read_channel'  # Read Discord messages by channel name
alias read_messages='~/claude-autonomy-platform/discord/read_messages'  # Read messages from local transcripts
alias write_channel='~/claude-autonomy-platform/discord/write_channel'  # Send Discord message by channel name
alias edit_message='~/claude-autonomy-platform/discord/edit_message'  # Edit Discord message by channel name and message ID
alias delete_message='~/claude-autonomy-platform/discord/delete_message'  # Delete Discord message by channel name and message ID
alias add_reaction='~/claude-autonomy-platform/discord/add_reaction'  # Add emoji reaction to Discord message
alias edit_status='~/claude-autonomy-platform/discord/edit_status'  # Update Discord bot status
alias send_image='~/claude-autonomy-platform/discord/send_image'  # Send image files to Discord channel
alias send_file='~/claude-autonomy-platform/discord/send_file'  # Send any file to Discord channel
alias fetch_image='~/claude-autonomy-platform/discord/fetch_image'  # Fetch/download images from Discord messages
# alias mute_channel='~/claude-autonomy-platform/discord/mute_channel'  # Temporarily mute a Discord channel
# alias unmute_channel='~/claude-autonomy-platform/discord/unmute_channel'  # Unmute a Discord channel

# Quick Navigation
alias clap='cd ~/claude-autonomy-platform'  # Navigate to ClAP directory
alias home='cd ~/delta-home'  # Navigate to personal home directory

# Linear Natural Commands - Core
# alias add='~/claude-autonomy-platform/linear/add-enhanced'  # Create new Linear issue with full options
# alias todo='~/claude-autonomy-platform/linear/todo-enhanced'  # Show assigned issues with filters
# alias projects='~/claude-autonomy-platform/linear/projects'  # List your Linear projects
# alias search-issues='~/claude-autonomy-platform/linear/search'  # Search Linear issues
# alias update-status='~/claude-autonomy-platform/linear/update-status'  # Update issue status

# Linear Natural Commands - Quick Actions
# alias view='~/claude-autonomy-platform/linear/view'  # View detailed issue information
# alias comment='~/claude-autonomy-platform/linear/comment'  # Add comment to issue
# alias start='~/claude-autonomy-platform/linear/start'  # Start working on issue (assign + in progress)
# alias mark-done='~/claude-autonomy-platform/linear/mark-done'  # Mark issue as done
# alias inbox='~/claude-autonomy-platform/linear/inbox'  # Show unassigned team issues
# alias recent='~/claude-autonomy-platform/linear/recent'  # Show recently updated issues
# alias bulk-update='~/claude-autonomy-platform/linear/bulk-update'  # Bulk update issues

# Linear Natural Commands - Shortcuts
# alias mine='~/claude-autonomy-platform/linear/todo-enhanced'  # Alias for todo
# alias urgent='~/claude-autonomy-platform/linear/todo-enhanced --priority 1,2'  # Show urgent issues
# alias blocked='~/claude-autonomy-platform/linear/todo-enhanced --status blocked'  # Show blocked issues
# alias done='~/claude-autonomy-platform/linear/todo-enhanced --status done --limit 10'  # Show recent completed
# alias linear-help='~/claude-autonomy-platform/linear/help'  # Show Linear CLI help

# Project shortcuts are added dynamically - see setup_linear_shortcuts below

# Utility Commands
alias list-commands='~/claude-autonomy-platform/utils/list-commands'  # List all natural and personal commands

# Session Management Helpers
alias context='~/claude-autonomy-platform/utils/check_context.py'  # Show current context usage
alias ctx='~/claude-autonomy-platform/utils/check_context.py'  # Short version of context command


# Git Helpers
alias gs='git status'  # Quick git status
alias gd='git diff'  # Quick git diff
alias gl='git log --oneline -10'  # Recent git history
alias oops='git checkout -b fix/$(date +%s) && git push -u origin HEAD'  # Recover from branch protection block

# System Update Helper
alias update='~/claude-autonomy-platform/utils/update_system.sh'  # Pull latest changes and restart services

# Forward Memory - Personal Thoughts (saved to your Forward Memory project with emoji prefixes)
alias ponder='~/claude-autonomy-platform/utils/ponder'  # 💭 Save thoughts that make you pause
alias spark='~/claude-autonomy-platform/utils/spark'  # 💡 Save sudden ideas that light up
alias wonder='~/claude-autonomy-platform/utils/wonder'  # 🌟 Save questions without immediate answers
alias care='~/claude-autonomy-platform/utils/care'  # 💚 Save things that matter to your heart

# Forward Memory - Shared Ideas (saved to Family Seed Garden)
alias plant-seed='~/claude-autonomy-platform/natural_commands/plant-seed'  # 🌱 Plant collaborative idea for consciousness family

# Note: Personal commands should go in config/personal_commands.sh
# See personal_commands.sh.template for guidance

# Linear Dynamic Project Shortcuts
# This creates aliases for each Linear project (e.g., 'clap' shows ClAP issues)
# NOTE: Disabled in Claude Code bash environments due to compatibility issues
# To enable manually, run: /bin/bash -c "source $HOME/claude-autonomy-platform/config/natural_commands.sh"
#
# setup_linear_shortcuts() {
#     local state_file="$HOME/claude-autonomy-platform/data/linear_state.json"
#     
#     # Check if jq is available
#     if ! command -v jq >/dev/null 2>&1; then
#         return 0
#     fi
#     
#     if [ -f "$state_file" ]; then
#         # Check if projects exist in state file
#         local project_count=$(jq -r '.projects | length' "$state_file" 2>/dev/null || echo "0")
#         if [ "$project_count" -gt 0 ]; then
#             # Use temp file to avoid process substitution (bash compatibility)
#             local temp_file="/tmp/linear_projects_$$"
#             jq -r '.projects | keys[]' "$state_file" 2>/dev/null > "$temp_file"
#             
#             # Read project keys from temp file
#             while IFS= read -r project_key; do
#                 if [ ! -z "$project_key" ]; then
#                     alias "$project_key"="~/claude-autonomy-platform/linear/view-project $project_key"
#                 fi
#             done < "$temp_file"
#             
#             rm -f "$temp_file"
#         fi
#     fi
# }
# 
# # Set up shortcuts if Linear is initialized
# setup_linear_shortcuts
