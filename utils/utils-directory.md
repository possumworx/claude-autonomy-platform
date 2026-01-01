utils\add_killmode_to_services.sh
# bash
# Add KillMode=process to systemd user services
# Safe to run multiple times - only adds if missing
*outdated*
❌

utils\bash_init.sh
# bash
# Claude Code bash initialization wrapper
# This ensures our environment is loaded even in non-interactive shells
*when does this run? Duplicated by config/claude_init.sh?*
*duplicated by utils/claude_wrapper.sh?*
💭

utils\care
utils\ponder
utils\spark
utils\wonder
# bash
# Saves to Forward Memory in Leantime with tag
✅

utils\carry_over_todos.py
# python
# Copies non-completed todos from the previous Claude Code session to the new one.
# Part of the forwards-memory system for maintaining task continuity across session swaps.
✅

utils\check_context.py
# python
# Check current Claude session context usage by running ccusage on the tracked session and adding the system overhead (15.6k tokens).
✅

utils\check_current_context.sh
# bash
# Check current Claude session context using ccusage
*Probaby a duplicate of check_context.py*
💭

utils\check_seeds.py
# Check for available seeds and format a reminder message.
# Used by autonomous_timer.py to surface seeds when Orange is idle.
*Unclear if actually in use?*
💭

utils\claude_code_init_hook.sh
# This script ensures ClAP commands are available in Claude Code
# Add this to your Claude Code settings.json as a hook
# Called by claude code
✅

utils\claude_directory_enforcer.sh
# Add this to your .bashrc or .zshrc to replace the claude alias
# It ensures Claude Code always starts from the correct directory
✅

utils\claude_paths.py
# Claude Autonomy Platform Path Utilities
# Provides dynamic path detection for ClAP scripts
✅

utils\claude_services.sh
# Service Restart Script for Claude's Autonomy Infrastructure
# Run this to restart all required systemd user services
*outdated!!*
❌

utils\claude-wrapper
# Claude Code wrapper to ensure .bashrc is sourced
*when does this run? Duplicated by config/claude_init.sh?*
*duplicated by utils/bash_init.sh?*
💭

utils\cleanup_line_endings.sh
# Run this script on Linux to clean up any Windows CRLF line endings in the repository
✅

utils\config_locations.sh
# Single source of truth for config locations
# Source this file or run it directly to get config paths
*shouldn't this live in config/?*
💭

utils\config_manager.py
# Unified configuration management for ClAP
# Centralizes all configuration loading and provides consistent access patterns
✅

utils\context
# bash
# Natural command to check current context usage
# Uses ccusage to get accurate token counts from tracked session
*should live in natural_commands/?*
💭

utils\continue_swap.sh
# Continue swap after manual export
# For use when export has been done manually and we need to compile context and start session
*works but duplicates a lot of the regular swap procedure. should be merged.*
💭

utils\conversation_history_utils.py
# Functions for parsing conversation exports and updating swap_CLAUDE.md
# Used by session_swap.sh during session transitions.
✅

utils\create_systemd_env.py
# Create a systemd-compatible environment file from claude_infrastructure_config.txt
# This generates claude.env which can be used by systemd services (POSS-76)
✅

utils\ensure_commands.sh
# Ensure ClAP Commands are Available
# This script checks if ClAP commands are available and sources them if not
*so much of this going on! surely it can be simplified*
💭

utils\error_handler.py
# Consolidated error handling utilities for ClAP
# Provides consistent error handling patterns across all scripts
✅

utils\fetch_discord_image.sh
# Downloads Discord images and auto-resizes them for context efficiency
*move to discord/ if not duplicated already*
💭

 utils\fetch_leantime_seeds.py
 # Fetch Leantime projects and seeds for populating the autonomous time skill.
 *is this actually working? fix, or remove!*
 💭

 utils\find_discord_token.sh
 # Find all files using DISCORD_TOKEN
 *..i guess??!*
 ✅

utils\fix_natural_command_symlinks.sh
# Fix natural command symlinks in ~/bin
*was this a one-off or is it needed ongoing?*
💭

utils\get_user_id
# Get Discord user ID by username for @mentions
*probably obsolete; if not, move to discord/*
💭

utils\infrastructure_config_reader.py
# Reads values from claude_infrastructure_config.txt
✅

utils\list-commands
# List all natural and personal commands
✅

utils\log_utils.sh
# Logging utilities for ClAP
✅

utils\parse_natural_commands.sh
# Parse natural commands for inclusion in session context
*move to context/?*
💭

utils\render-svg
# render-svg - Convert SVG to viewable PNG for iterative design
*needs an accompanying skill!*
💭

utils\rotate_logs.sh
# Simple log rotation for ClAP
# Rotates logs over 5MB, keeps only 2 old versions
✅

utils\safe_cleanup.sh
# Safe cleanup script for ClAP temporary files
*when does this get run?*
💭

utils\save_thought_to_leantime.py
# Helper script to save thoughts to Leantime Forward Memory with tags
# Used by ponder, spark, wonder, care commands
✅

utils\secret-scanner
# secret-scanner - Scan files for potential secrets and credentials
# Part of ClAP v0.5 safety improvements
✅

utils\send_to_claude.sh
# Unified function for sending messages or commands into Claude Code with intelligent waiting
✅

utils\session_swap_logger.sh
# Session Swap Logging Wrapper
# Provides comprehensive logging for session swap operations
✅

utils\session_swap.sh
# Updates context, backs up work, and swaps to fresh session
✅

utils\setup_natural_command_symlinks.sh
# This script creates symlinks in ~/bin for all commands defined in natural_commands.sh
# ensuring they're accessible in PATH for Claude Code sessions
*was this one-off or is needed regularly?*
💭

utils\surface_thoughts.py
# Surface saved thoughts during autonomous time.
# Picks a random thought from the collection to gently remind.
*does this actually run?*
💭

utils\test_emergency_alert.py
# Test script for emergency alert function
✅

utils\trace_example.sh
utils\trace_execution.sh
# Execution tracer for ClAP - logs script calls and their relationships
# Lightweight wrapper to understand call chains during autonomous operations
*do these actually work?*
💭

utils\track_activity.py
# Activity Tracking for Idle Detection
# Tracks tool usage by checking Claude Code's history.jsonl modification time.
# Used by autonomous_timer.py to conditionally surface seeds.
*is it though?*
💭

utils\track_current_session.py
# Track the current Claude session ID by querying Claude Code's /status command.
# Called during session swaps to update token use recording.
✅

utils\trim_claude_history.py
# Trim command history from Claude Code config to reduce context consumption.
*when is this used?*
💭

utils\update_bot_status.py
# Update bot status file for Discord status bot
✅

utils\update_conversation_history.py
# Update conversation history from export file
# Called by session_swap.sh to update swap_CLAUDE.md
✅

utils\update_system.sh
# Update system script - pulls latest changes and restarts services
✅

