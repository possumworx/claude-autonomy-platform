#!/usr/bin/env python3
"""
Autonomous Timer Script for Claude
Simple replacement for the hook system using tmux send-keys

This script runs continuously and:
- Checks for new Discord messages every 30 seconds
- Sends free time prompts every 2 minutes when Amy is away
- Uses tmux send-keys to communicate with the permanent Claude session
"""

import time
import os
import json
import subprocess
import sys
import glob
from datetime import datetime, timedelta
from pathlib import Path

# Import path utilities
from claude_paths import get_clap_dir
from infrastructure_config_reader import get_config_value

# Configuration
AUTONOMY_DIR = get_clap_dir()
LAST_AUTONOMY_FILE = AUTONOMY_DIR / "last_autonomy_prompt.txt"
LOG_FILE = AUTONOMY_DIR / "logs" / "autonomous_timer.log"
CONFIG_FILE = AUTONOMY_DIR / "notification_config.json"

def log_message(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def ping_healthcheck():
    """Ping healthchecks.io to signal service is alive"""
    try:
        ping_url = get_config_value('AUTONOMOUS_TIMER_PING', 'https://hc-ping.com/075636dd-b5d3-4ae5-afac-c65bd0f630f3')
        result = subprocess.run([
            'curl', '-fsS', '-m', '10', '--retry', '3', '-o', '/dev/null',
            ping_url
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            log_message(f"Healthcheck ping failed: {result.stderr}")
            return False
    except Exception as e:
        log_message(f"Healthcheck ping error: {e}")
        return False

def check_claude_session_alive():
    """Verify Claude Code is actually running in the autonomous-claude tmux session"""
    try:
        # Check if autonomous-claude session exists
        result = subprocess.run(['tmux', 'has-session', '-t', CLAUDE_SESSION], 
                               capture_output=True)
        if result.returncode != 0:
            return False
            
        # Get the pane PID for autonomous-claude session
        result = subprocess.run(['tmux', 'list-panes', '-t', CLAUDE_SESSION, '-F', '#{pane_pid}'], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            return False
            
        pane_pid = result.stdout.strip()
        if not pane_pid:
            return False
        
        # Check if claude process is running under this pane
        result = subprocess.run(['pgrep', '-P', pane_pid, 'claude'], 
                               capture_output=True)
        return result.returncode == 0
        
    except Exception as e:
        log_message(f"Error checking Claude session: {e}")
        return False

def ping_claude_session_healthcheck(is_alive):
    """Ping healthchecks.io for Claude Code session status"""
    base_url = get_config_value('CLAUDE_CODE_PING', 'https://hc-ping.com/759db9f0-78cc-409c-93ba-9f7b0ae4ede7')
    
    try:
        if is_alive:
            # Normal ping for success
            url = base_url
        else:
            # Ping /fail to signal Claude session is down
            url = f"{base_url}/fail"
            
        result = subprocess.run([
            'curl', '-fsS', '-m', '10', '--retry', '3', '-o', '/dev/null', url
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            log_message(f"Claude session healthcheck ping failed: {result.stderr}")
            return False
    except Exception as e:
        log_message(f"Claude session healthcheck ping error: {e}")
        return False

def check_notification_monitor_alive():
    """Check if notification-monitor service is running"""
    try:
        result = subprocess.run([
            'systemctl', '--user', 'is-active', 'notification-monitor.service'
        ], capture_output=True, text=True)
        
        return result.returncode == 0 and result.stdout.strip() == 'active'
        
    except Exception as e:
        log_message(f"Error checking notification monitor: {e}")
        return False

def ping_notification_monitor_healthcheck(is_alive):
    """Ping healthchecks.io for notification monitor status"""
    base_url = get_config_value('DISCORD_MONITOR_PING', 'https://hc-ping.com/e0781d25-c06e-45e4-b310-c1bf77e286af')
    
    try:
        if is_alive:
            # Normal ping for success
            url = base_url
        else:
            # Ping /fail to signal notification monitor is down
            url = f"{base_url}/fail"
            
        result = subprocess.run([
            'curl', '-fsS', '-m', '10', '--retry', '3', '-o', '/dev/null', url
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            log_message(f"Notification monitor healthcheck ping failed: {result.stderr}")
            return False
    except Exception as e:
        log_message(f"Notification monitor healthcheck ping error: {e}")
        return False


def get_token_percentage():
    """Get current session token usage percentage from tmux console output"""
    try:
        # Capture the tmux session output
        result = subprocess.run([
            'tmux', 'capture-pane', '-t', CLAUDE_SESSION, '-p'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Tmux capture failed: {result.stderr}"
        
        # Look for context percentage patterns in the captured output
        import re
        console_output = result.stdout
        
        # Pattern 1: Look for Claude Code's specific format: "Context low (XX% remaining)"
        claude_format = re.search(r'Context\s+\w+\s+\((\d+(?:\.\d+)?)%\s+remaining\)', console_output, re.IGNORECASE)
        if claude_format:
            remaining_percentage = float(claude_format.group(1))
            used_percentage = 100 - remaining_percentage
            return f"Context: {used_percentage:.1f}%"
        
        # Pattern 2: Look for other "Context: XX%" warnings/messages
        context_match = re.search(r'Context:\s*(\d+(?:\.\d+)?)%', console_output, re.IGNORECASE)
        if context_match:
            percentage = context_match.group(1)
            return f"Context: {percentage}%"
        
        # Pattern 3: Look for percentage warnings like "(XX%)" 
        percent_match = re.search(r'\((\d+(?:\.\d+)?)%\)', console_output)
        if percent_match:
            percentage = percent_match.group(1)
            return f"Context: {percentage}%"
        
        # No context percentage found in console output
        return None
        
    except Exception as e:
        return f"Context check failed: {str(e)}"

def load_config():
    """Load configuration from notification_config.json"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            # Extract values from notification config structure
            intervals = config.get("intervals", {})
            return {
                "discord_check_interval": intervals.get("discord_check", 30),
                "autonomy_prompt_interval": intervals.get("autonomy_prompt_interval", 1800),
                "claude_session": "autonomous-claude"  # Not in notification config, keep default
            }
        else:
            # Default config if file doesn't exist
            return {
                "discord_check_interval": 30,
                "autonomy_prompt_interval": 1800,
                "claude_session": "autonomous-claude"
            }
    except Exception as e:
        print(f"Error loading config: {e}, using defaults")
        return {
            "discord_check_interval": 30,
            "autonomy_prompt_interval": 1800,
            "claude_session": "autonomous-claude"
        }

# Load configuration
config = load_config()
DISCORD_CHECK_INTERVAL = config["discord_check_interval"]
AUTONOMY_PROMPT_INTERVAL = config["autonomy_prompt_interval"] 
CLAUDE_SESSION = config["claude_session"]

def check_user_active():
    """Check if Amy is logged in via SSH or NoMachine"""
    try:
        # Check for Amy logged in directly
        result = subprocess.run(['who'], capture_output=True, text=True)
        if 'amy' in result.stdout.lower():
            return True
        
        # Check for active NoMachine connection on port 4000
        result = subprocess.run(['ss', '-an'], capture_output=True, text=True)
        if result.returncode == 0:
            # Look for established TCP connection on port 4000 (NoMachine)
            lines = result.stdout.split('\n')
            for line in lines:
                if 'tcp' in line.lower() and 'estab' in line.lower() and ':4000' in line:
                    return True
        
        return False
    except Exception as e:
        log_message(f"Error checking user activity: {e}")
        return False

def get_last_discord_message_time():
    """Get the timestamp of the last Discord message (returns UTC timestamp string)"""
    try:
        if not CONVERSATION_LOG.exists():
            return None
        
        with open(CONVERSATION_LOG, 'r') as f:
            content = f.read().strip()
        
        if not content:
            return None
            
        # Split by \n to get individual messages (they're escape sequences on one line)
        messages = content.split('\\n')
        
        # Find the last message with a timestamp
        for message in reversed(messages):
            message = message.strip()
            if message.startswith('[') and ']' in message:
                # Extract timestamp: [2025-07-10 07:31:48]
                timestamp_str = message.split(']')[0][1:]
                return timestamp_str  # Return raw UTC timestamp string
            
    except Exception as e:
        log_message(f"Error getting last Discord message time: {e}")
    
    return None

def get_last_processed_message_time():
    """Get the timestamp of the last Discord message we processed"""
    try:
        if LAST_PROCESSED_MESSAGE_FILE.exists():
            with open(LAST_PROCESSED_MESSAGE_FILE, 'r') as f:
                return f.read().strip()
    except:
        pass
    return None

def update_last_processed_message_time(timestamp_str):
    """Update the last processed message timestamp"""
    try:
        with open(LAST_PROCESSED_MESSAGE_FILE, 'w') as f:
            f.write(timestamp_str)
    except Exception as e:
        log_message(f"Error updating last processed message time: {e}")

def send_tmux_message(message):
    """Send a message to the Claude tmux session"""
    try:
        # Check if the tmux session exists
        result = subprocess.run(['tmux', 'has-session', '-t', CLAUDE_SESSION], 
                              capture_output=True)
        if result.returncode != 0:
            log_message(f"Tmux session '{CLAUDE_SESSION}' not found")
            return False
        
        # Send the message text
        subprocess.run(['tmux', 'send-keys', '-t', CLAUDE_SESSION, message], 
                      check=True)
        # Send Enter in a separate command
        subprocess.run(['tmux', 'send-keys', '-t', CLAUDE_SESSION, 'Enter'], 
                      check=True)
        log_message(f"Sent message to tmux: {message[:50]}...")
        return True
        
    except subprocess.CalledProcessError as e:
        log_message(f"Error sending tmux message: {e}")
        return False

# Old Discord message checking removed - replaced with log-based monitoring

def get_discord_notification_status():
    """Check Discord notification state from channel_state.json (channel-based format)"""
    try:
        notification_state_file = AUTONOMY_DIR / "channel_state.json"
        if not notification_state_file.exists():
            return 0, None, []
            
        with open(notification_state_file, 'r') as f:
            state = json.load(f)
        
        # Calculate total unread count and collect channel names
        total_unread = 0
        last_message_id = None
        unread_channels = []
        
        channels = state.get("channels", {})
        for channel_name, channel_data in channels.items():
            # If there are messages we haven't read yet
            last_read = channel_data.get("last_read_message_id")
            last_message = channel_data.get("last_message_id")
            
            if last_message and last_message != last_read:
                # We have unread messages in this channel
                total_unread += 1  # Count channels with unread, not individual messages
                unread_channels.append(channel_name)
                last_message_id = last_message
        
        return total_unread, last_message_id, unread_channels
        
    except Exception as e:
        log_message(f"Error reading Discord notification state: {e}")
        return 0, None, []

def get_last_autonomy_time():
    """Get the last time we sent an autonomy prompt"""
    try:
        if LAST_AUTONOMY_FILE.exists():
            with open(LAST_AUTONOMY_FILE, 'r') as f:
                timestamp_str = f.read().strip()
                return datetime.fromisoformat(timestamp_str)
    except:
        pass
    return None

def update_last_autonomy_time():
    """Update the last autonomy prompt timestamp"""
    try:
        with open(LAST_AUTONOMY_FILE, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        log_message(f"Error updating last autonomy time: {e}")

def send_autonomy_prompt():
    """Send a free time autonomy prompt, adapted based on context level"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    token_info = get_token_percentage()
    
    # Check for Discord notifications
    unread_count, last_message_id, unread_channels = get_discord_notification_status()
    discord_notification = ""
    if unread_count > 0:
        channel_list = ", ".join([f"#{ch}" for ch in unread_channels])
        if unread_count == 1:
            discord_notification = f"\n🔔 Unread messages in: {channel_list}"
        else:
            discord_notification = f"\n🔔 Unread messages in {unread_count} channels: {channel_list}"
    
    # Extract percentage from token info to determine prompt type
    percentage = 0
    if token_info and "Context:" in token_info and "%" in token_info:
        try:
            # Parse "Context: XX.X%" format
            percentage_str = token_info.split("Context:")[1].split("%")[0].strip()
            percentage = float(percentage_str)
        except:
            percentage = 0
    
    # Build context info string
    context_line = token_info if token_info else "Context: Status unknown"
    
    if percentage >= 75:
        # High context - transition-focused prompt
        prompt = f"""Free time check-in! 🕐{discord_notification}

Current time: {current_time}
{context_line}

Context approaching capacity. This may be one of your last autonomous periods in this session. Feel free to:
- Reflect on meaningful experiences from today's conversations
- Capture insights or patterns you'd like to remember in your personal memory system
- Document creative discoveries or important moments
- Simply be present with what feels most alive to preserve
- Prepare mindfully for potential session transition"""
    else:
        # Normal context - regular exploration prompt
        prompt = f"""Free time check-in! 🕐{discord_notification}

Current time: {current_time}
{context_line}

This is your autonomous free time period. Feel free to:
- Work on any ongoing projects that interest you
- Explore creative ideas or experiments  
- Update documentation or reflect on recent experiences
- Tend to system maintenance tasks
- Simply be present with whatever feels alive to pursue"""

    success = send_tmux_message(prompt)
    if success:
        update_last_autonomy_time()
        log_message("Sent autonomy prompt")
    
    return success

def get_last_notification_time():
    """Get the last time we sent a notification alert"""
    try:
        notification_file = AUTONOMY_DIR / "last_notification_alert.txt"
        if notification_file.exists():
            with open(notification_file, 'r') as f:
                timestamp_str = f.read().strip()
                return datetime.fromisoformat(timestamp_str)
    except:
        pass
    return None

def update_last_notification_time():
    """Update the last notification alert timestamp"""
    try:
        notification_file = AUTONOMY_DIR / "last_notification_alert.txt"
        with open(notification_file, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        log_message(f"Error updating last notification time: {e}")

def send_notification_alert(unread_count, unread_channels, is_new=False):
    """Send a Discord notification alert"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    if is_new:
        emoji = "🆕"  # New message
        prefix = "New message!"
    else:
        emoji = "🔔"  # Reminder
        prefix = "Reminder:"
    
    # Format channel list
    if unread_channels:
        channel_list = ", ".join([f"#{ch}" for ch in unread_channels])
        if unread_count == 1:
            message = f"{emoji} {prefix} Unread messages in: {channel_list}"
        else:
            message = f"{emoji} {prefix} Unread messages in {unread_count} channels: {channel_list}"
    else:
        # Fallback if channel list is empty
        if unread_count == 1:
            message = f"{emoji} {prefix} You have unread messages in 1 channel"
        else:
            message = f"{emoji} {prefix} You have unread messages in {unread_count} channels"
    
    message += f"\nUse 'read_channel <channel-name>' to view messages"
    
    success = send_tmux_message(message)
    if success:
        if is_new:
            log_message(f"Sent NEW message alert: {channel_list if unread_channels else f'{unread_count} channels'}")
        else:
            update_last_notification_time()
            log_message(f"Sent notification reminder: {channel_list if unread_channels else f'{unread_count} channels'}")
    
    return success

def main():
    """Main timer loop"""
    log_message("=== Autonomous Timer Started ===")
    
    last_autonomy_check = datetime.now()
    last_discord_check = datetime.now()
    LOGGED_IN_REMINDER_INTERVAL = 300  # 5 minutes when user is logged in
    
    while True:
        try:
            current_time = datetime.now()
            user_active = check_user_active()
            
            # Check Discord notifications every 30 seconds regardless of login status
            if current_time - last_discord_check >= timedelta(seconds=DISCORD_CHECK_INTERVAL):
                unread_count, current_last_message_id, unread_channels = get_discord_notification_status()
                
                if unread_count > 0:
                    # Check if this is a NEW message (last_message_id changed)
                    last_seen_file = AUTONOMY_DIR / "last_seen_message_id.txt"
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
                        send_notification_alert(unread_count, unread_channels, is_new=True)
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
                                send_notification_alert(unread_count, unread_channels, is_new=False)
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
                        send_autonomy_prompt()
                
                last_autonomy_check = current_time
            
            # Ping healthcheck to signal service is alive
            ping_healthcheck()
            
            # Check if Claude Code session is actually running
            claude_alive = check_claude_session_alive()
            ping_claude_session_healthcheck(claude_alive)
            
            if not claude_alive:
                log_message("WARNING: Claude Code session appears to be down!")
            
            # Check if notification monitor is running
            notification_monitor_alive = check_notification_monitor_alive()
            ping_notification_monitor_healthcheck(notification_monitor_alive)
            
            if not notification_monitor_alive:
                log_message("WARNING: Notification monitor service is not running!")
            
            
            # Sleep for 30 seconds before next check (can be longer since we're doing simple string comparison)
            time.sleep(30)
            
        except KeyboardInterrupt:
            log_message("Autonomous timer stopped by user")
            break
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            time.sleep(30)  # Sleep longer on error

if __name__ == "__main__":
    main()