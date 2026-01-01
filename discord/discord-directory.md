discord\add_reaction
discord\delete_message
discord\edit_message
discord\edit_status
discord\fetch_image
discord\read_channel
discord\send_file
discord\send_image
discord\write_channel  # exact duplicate
discord\write_channel_v2  # exact duplicate
# python
# Uses the unified discord_tools library
*have all these been superseded by discord_utils.py?*

discord\channel_monitor_simple.py
# Channel-based Discord monitoring for ClAP
# Updates channel_state.json with latest message IDs
# Uses Discord REST API directly with requests
*almost certainly obsolete; certainly should be! Needs to be checked*

discord\channel_state.py
# Channel-based state management for ClAP
# Tracks Discord channels instead of users - simpler and unified!
*may be obsoleted by discord_transcript_fetcher.py - needs to be checked*

discord\claude_status_bot.py
# Claude Status Bot - Persistent Discord bot for status updates
# Based on curl-bot architecture but focused on Claude operational status
# This bot maintains a WebSocket connection and watches for status update requests
*very flaky but harmless. Replace when resources allow.*

discord\discord_tools.py
# Unified Discord Tools Library for ClAP
# Consolidates all Discord functionality with enhanced image handling
# Designed for seamless integration with natural commands
*this, vs discord_utils.py? which one is current?*

discord\discord_transcript_fetcher.py
# Discord Transcript Fetcher for ClAP
# Continuously monitors Discord channels and builds local transcript files.
*current, excellent, keep*

discord\discord_utils.py
# Consolidated Discord utilities for ClAP
# Provides common functionality for all Discord operations
*this, vs discord_tools.py? which one is current?*

discord\mute_channel
# python
# Mute a Discord channel by temporarily removing it from channel_state.json
# A systemd timer will automatically restore it after the duration expires
*Probably obsolete; delete or rewrite to use transcript_channel_state.json*

discord\read_messages
# Read messages from local transcript files
# Part of the transcript-based Discord system
*correct, good, keep*

discord\README.md
*been superseded by discord_utils.py?*
*should it live in docs/?*

discord\unmute_channel
# Unmute a Discord channel by restoring it to channel_state.json
*Probably obsolete; delete or rewrite to use transcript_channel_state.json*

discord\unmute_expired_channels
# Check for expired muted channels and automatically unmute them
# This script is run periodically by a systemd timer
*we do NOT need this zombie stuff*








