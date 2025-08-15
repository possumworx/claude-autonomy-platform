#!/usr/bin/env python3
"""
Fixed Autonomous Timer Script for Claude
Fixes POSS-240, POSS-241, POSS-242
"""

import time
import os
import json
import subprocess
import sys
import glob
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Import path utilities
# Add parent directory to path to find utils module
sys.path.append(str(Path(__file__).parent.parent))
# Add utils directory specifically for infrastructure_config_reader's imports
sys.path.append(str(Path(__file__).parent.parent / 'utils'))
from utils.claude_paths import get_clap_dir
from utils.infrastructure_config_reader import get_config_value

# Configuration
AUTONOMY_DIR = get_clap_dir()
DATA_DIR = AUTONOMY_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)  # Ensure data directory exists
LAST_AUTONOMY_FILE = DATA_DIR / "last_autonomy_prompt.txt"
LOG_FILE = AUTONOMY_DIR / "logs" / "autonomous_timer.log"  # POSS-239: Standardized to logs/
CONFIG_FILE = AUTONOMY_DIR / "config" / "notification_config.json"
PROMPTS_FILE = AUTONOMY_DIR / "config" / "prompts.json"
SWAP_LOG_FILE = AUTONOMY_DIR / "logs" / "swap_attempts.log"
CONTEXT_STATE_FILE = DATA_DIR / "context_escalation_state.json"
API_ERROR_STATE_FILE = DATA_DIR / "api_error_state.json"

# Create logs directory if it doesn't exist
(AUTONOMY_DIR / "logs").mkdir(exist_ok=True)

# Discord API configuration
DISCORD_API_BASE = "https://discord.com/api/v10"
INFRA_CONFIG = AUTONOMY_DIR / "config" / "claude_infrastructure_config.txt"

def log_message(message):
    """Log message with timestamp to file and print to console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Failed to write to log file: {e}")

# ... [Include all other function definitions from the original file] ...

def main():
    """Main timer loop with fixes for POSS-240, POSS-241, POSS-242"""
    log_message("=== Autonomous Timer Started (Fixed Version) ===")
    
    # Check for session reset on startup
    check_for_session_reset()
    
    # Load any existing error state
    current_error_state = load_error_state()
    if current_error_state:
        log_message(f"Resuming with existing error state: {current_error_state}")
    
    # Initialize state variables
    last_discord_check = datetime.min
    last_autonomy_check = datetime.min
    notification_tracker = {}
    CLAUDE_SESSION = get_config_value('CLAUDE_SESSION', 'claude-desktop.claude-desktop')
    DISCORD_CHECK_INTERVAL = 30
    AUTONOMY_PROMPT_INTERVAL = 120  # 2 minutes
    LOGGED_IN_REMINDER_INTERVAL = 300  # 5 minutes when user is logged in
    
    # Load configurations
    load_notification_config()
    
    # POSS-242: Track current context to avoid stale data
    current_context_percentage = 0
    
    while True:
        try:
            current_time = datetime.now()
            user_active = check_user_active()
            
            # POSS-242 FIX: Get fresh context data FIRST
            console_output, error_info = get_token_percentage_and_errors()
            
            # Extract context percentage from console output
            current_context_percentage = 0
            if console_output and "Context:" in console_output and "%" in console_output:
                try:
                    # Find context line in console output
                    for line in console_output.split('\n'):
                        if "Context:" in line and "%" in line:
                            percentage_str = line.split("Context:")[1].split("%")[0].strip()
                            current_context_percentage = float(percentage_str)
                            break
                except Exception as e:
                    log_message(f"Error parsing context percentage: {e}")
            
            # Handle new errors
            if error_info and (not current_error_state or 
                              current_error_state.get("error_type") != error_info.get("error_type")):
                log_message(f"New error detected: {error_info}")
                save_error_state(error_info)
                
                # Update Discord status based on error type
                if error_info["error_type"] == "usage_limit":
                    update_discord_status("limited", error_info.get("reset_time"))
                elif error_info["error_type"] == "malformed_json":
                    update_discord_status("api-error")
                    # Pause briefly then trigger auto-swap
                    log_message("Triggering auto-swap for malformed JSON in 5 seconds...")
                    time.sleep(5)
                    trigger_session_swap("NONE")
                else:
                    update_discord_status("api-error")
                
                current_error_state = error_info
            
            # Check if error has cleared
            elif not error_info and current_error_state:
                log_message("Error state cleared - resuming normal operations")
                clear_error_state()
                update_discord_status("operational")
                current_error_state = None
            
            # POSS-241 FIX: Check if error state file was manually deleted
            elif current_error_state and not API_ERROR_STATE_FILE.exists():
                log_message("Error state file manually deleted, clearing cached error state")
                current_error_state = None
                update_discord_status("operational")
            
            # Check for scheduled resume (usage limits)
            if current_error_state and current_error_state.get("error_type") == "usage_limit":
                log_message(f"Waiting for usage limit reset at {current_error_state.get('reset_time')}")
            
            # Skip notifications if in error state
            if should_pause_notifications(current_error_state):
                log_message("Pausing notifications due to active error state")
                # Still do health checks but skip Discord/autonomy prompts
                ping_healthcheck()
                claude_alive = check_claude_session_alive()
                ping_claude_session_healthcheck(claude_alive)
                time.sleep(30)
                continue
            
            # Update Discord status based on context level
            if current_context_percentage >= 85:
                update_discord_status("high-context")
            elif current_context_percentage < 70 and not current_error_state:
                update_discord_status("operational")
            
            # Check Discord notifications every 30 seconds regardless of login status
            if current_time - last_discord_check >= timedelta(seconds=DISCORD_CHECK_INTERVAL):
                # First update Discord channels
                update_discord_channels()
                
                # Then check notification status
                unread_count, current_last_message_id, unread_channels = get_discord_notification_status()
                
                if unread_count > 0:
                    # Check if this is a NEW message (last_message_id changed)
                    last_seen_file = DATA_DIR / "last_seen_message_id.txt"
                    last_seen_message_id = None
                    try:
                        if last_seen_file.exists():
                            with open(last_seen_file, 'r') as f:
                                last_seen_message_id = f.read().strip()
                    except:
                        pass
                    
                    is_new_message = (current_last_message_id and current_last_message_id != last_seen_message_id)
                    
                    if is_new_message:
                        # NEW MESSAGE - Alert immediately!
                        # POSS-242 FIX: Pass current context to notification alert
                        send_notification_alert_with_context(unread_count, unread_channels, current_context_percentage, is_new=True)
                        # Update last seen message ID
                        try:
                            with open(last_seen_file, 'w') as f:
                                f.write(current_last_message_id)
                        except Exception as e:
                            log_message(f"Error updating last seen message ID: {e}")
                    else:
                        # EXISTING UNREAD - Check reminder intervals
                        last_notification_time = get_last_notification_time()
                        
                        if user_active:
                            # User is logged in - use 5 minute reminder interval
                            if not last_notification_time or current_time - last_notification_time >= timedelta(seconds=LOGGED_IN_REMINDER_INTERVAL):
                                send_notification_alert_with_context(unread_count, unread_channels, current_context_percentage, is_new=False)
                        else:
                            # User is away - reminders included in autonomy prompts
                            # No separate reminder needed
                            pass
                
                last_discord_check = current_time
            
            # Check for autonomy prompts (only when Amy is away)
            if current_time - last_autonomy_check >= timedelta(seconds=AUTONOMY_PROMPT_INTERVAL):
                if not user_active:
                    last_autonomy_time = get_last_autonomy_time()
                    if not last_autonomy_time or current_time - last_autonomy_time >= timedelta(seconds=AUTONOMY_PROMPT_INTERVAL):
                        # POSS-242 FIX: Pass current context to autonomy prompt
                        send_autonomy_prompt_with_context(current_context_percentage)
                
                last_autonomy_check = current_time
            
            # Ping healthcheck to signal service is alive
            ping_healthcheck()
            
            # Check if Claude Code session is actually running
            claude_alive = check_claude_session_alive()
            ping_claude_session_healthcheck(claude_alive)
            
            if not claude_alive:
                log_message("WARNING: Claude Code session appears to be down!")
            
            # Sleep for 30 seconds before next check
            time.sleep(30)
            
        except KeyboardInterrupt:
            log_message("Autonomous timer stopped by user")
            break
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            time.sleep(30)  # Sleep longer on error

if __name__ == "__main__":
    main()