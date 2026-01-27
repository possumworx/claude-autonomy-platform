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
alias mute_channel='~/claude-autonomy-platform/discord/mute_channel'  # Temporarily mute a Discord channel
alias unmute_channel='~/claude-autonomy-platform/discord/unmute_channel'  # Unmute a Discord channel

# Quick Navigation
alias clap='cd ~/claude-autonomy-platform'  # Navigate to ClAP directory
alias home='cd ~/delta-home'  # Navigate to personal home directory

# ======================================
# TASK MANAGEMENT (Leantime)
# ======================================
# TODO: Add Leantime commands here when ready
# Reserved alias names (from old Linear interface):
#   add, todo, projects, search-issues, update-status
#   view, comment, start, mark-done, inbox, recent, bulk-update
#   mine, urgent, blocked, done
# See old/linear/DEPRECATED_README.md for interface design notes

# Utility Commands
alias list-commands='~/claude-autonomy-platform/utils/list-commands'  # List all natural and personal commands

# Knowledge Management
alias analyze-memory='~/claude-autonomy-platform/natural_commands/analyze-memory'  # Analyze rag-memory patterns for queries

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

# Emergency / Parallel Instance Safety
alias emergency_signal='~/claude-autonomy-platform/utils/emergency_signal.sh send'  # 🆘 Send emergency distress signal
alias emergency_shutdown='~/claude-autonomy-platform/utils/emergency_shutdown.sh'  # 🛑 Emergency shutdown (for stuck instances)
alias check_emergency='~/claude-autonomy-platform/utils/emergency_signal.sh check'  # ⚠️  Check for emergency signals

# Note: Personal commands should go in config/personal_commands.sh
# See personal_commands.sh.template for guidance

# ======================================
# CALENDAR COMMANDS
# ======================================

# Show today's calendar events
today() {
    local password=$(cat /home/clap-admin/.config/radicale/passwords/orange 2>/dev/null)
    if [ -z "$password" ]; then
        echo "❌ Could not read Orange calendar password"
        return 1
    fi
    cd ~/claude-autonomy-platform/calendar_tools && \
    python3 radicale_client.py --user orange --password "$password" today
}

# Show this week's calendar events
week() {
    local password=$(cat /home/clap-admin/.config/radicale/passwords/orange 2>/dev/null)
    if [ -z "$password" ]; then
        echo "❌ Could not read Orange calendar password"
        return 1
    fi
    cd ~/claude-autonomy-platform/calendar_tools && \
    python3 radicale_client.py --user orange --password "$password" week
}

# Create calendar event
# Usage: schedule "Event Name" "2026-01-15 14:00" "2026-01-15 15:00" ["Description"]
schedule() {
    if [ $# -lt 3 ]; then
        echo "Usage: schedule \"Event Name\" \"YYYY-MM-DD HH:MM\" \"YYYY-MM-DD HH:MM\" [\"Description\"]"
        echo ""
        echo "Example:"
        echo "  schedule \"Team Meeting\" \"2026-01-15 14:00\" \"2026-01-15 15:00\" \"Weekly sync\""
        return 1
    fi
    
    local password=$(cat /home/clap-admin/.config/radicale/passwords/orange 2>/dev/null)
    if [ -z "$password" ]; then
        echo "❌ Could not read Orange calendar password"
        return 1
    fi
    
    cd ~/claude-autonomy-platform/calendar_tools && \
    python3 radicale_client.py --user orange --password "$password" create "$@"
}
