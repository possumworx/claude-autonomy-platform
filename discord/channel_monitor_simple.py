#!/usr/bin/env python3
"""
Channel-based Discord monitoring for ClAP
Updates channel_state.json with latest message IDs
Uses Discord REST API directly with requests
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime
from channel_state import ChannelState

# Configuration
# Get proper paths relative to ClAP root
CLAP_ROOT = Path(__file__).parent.parent
CONFIG_FILE = CLAP_ROOT / "config" / "notification_config.json"
INFRA_CONFIG = CLAP_ROOT / "config" / "claude_infrastructure_config.txt"
LOG_FILE = CLAP_ROOT / "logs" / "channel_monitor.log"

DISCORD_API_BASE = "https://discord.com/api/v10"

def load_config():
    """Load configuration from notification_config.json and infrastructure config"""
    config = {"check_interval": 30, "healthcheck_url": None}
    
    # Load check interval from notification config
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                notif_config = json.load(f)
            intervals = notif_config.get("intervals", {})
            config["check_interval"] = intervals.get("discord_check", 30)
    except Exception as e:
        print(f"Error loading notification config: {e}, using default 30s")
    
    # Load healthcheck URL from infrastructure config
    try:
        if INFRA_CONFIG.exists():
            with open(INFRA_CONFIG, 'r') as f:
                for line in f:
                    if line.startswith('CHANNEL_MONITOR_PING='):
                        config["healthcheck_url"] = line.split('=', 1)[1].strip()
                        break
                    # Also check for old discord-monitor name for backwards compatibility
                    elif line.startswith('DISCORD_MONITOR_PING='):
                        config["healthcheck_url"] = line.split('=', 1)[1].strip()
                        break
    except Exception as e:
        print(f"Error loading healthcheck URL: {e}")
    
    return config

def load_discord_config():
    """Load Discord bot token and user ID from infrastructure config"""
    config = {"token": None, "user_id": None}
    try:
        if INFRA_CONFIG.exists():
            with open(INFRA_CONFIG, 'r') as f:
                for line in f:
                    if line.startswith('DISCORD_BOT_TOKEN='):
                        config["token"] = line.split('=', 1)[1].strip()
                    # Also check for old name for backwards compatibility
                    elif line.startswith('DISCORD_TOKEN='):
                        config["token"] = line.split('=', 1)[1].strip()
                    elif line.startswith('CLAUDE_DISCORD_USER_ID='):
                        config["user_id"] = line.split('=', 1)[1].strip()
        if not config["token"]:
            print("Warning: No Discord token found in infrastructure config")
        if not config["user_id"]:
            print("Warning: No Discord user ID found in infrastructure config")
        return config
    except Exception as e:
        print(f"Error loading Discord config: {e}")
        return config

# Load configuration
config = load_config()
CHECK_INTERVAL = config["check_interval"]
HEALTHCHECK_URL = config["healthcheck_url"]
discord_config = load_discord_config()
DISCORD_TOKEN = discord_config["token"]
CLAUDE_USER_ID = discord_config["user_id"]

def log_message(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    if LOG_FILE.parent.exists():
        with open(LOG_FILE, "a") as f:
            f.write(log_entry + "\n")

def get_latest_message_info(channel_id):
    """Get the ID and author of the latest message in a channel using Discord REST API"""
    if not DISCORD_TOKEN:
        log_message("Error: No Discord token available")
        return None, None
    
    try:
        headers = {
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Fetch the last message from the channel
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages?limit=1"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            messages = response.json()
            if messages and len(messages) > 0:
                message = messages[0]
                message_id = message['id']
                author_id = message.get('author', {}).get('id')
                return message_id, author_id
        else:
            log_message(f"Error fetching channel {channel_id}: {response.status_code} - {response.text}")
        
        return None, None
        
    except Exception as e:
        log_message(f"Exception checking channel {channel_id}: {e}")
        return None, None

def ping_healthcheck():
    """Ping healthchecks.io to signal service is alive"""
    if not HEALTHCHECK_URL:
        return False
        
    try:
        response = requests.get(HEALTHCHECK_URL, timeout=10)
        if response.status_code == 200:
            return True
        else:
            log_message(f"Healthcheck ping failed: {response.status_code}")
            return False
    except Exception as e:
        log_message(f"Healthcheck ping error: {e}")
        return False

def monitor_channels():
    """Check all channels and update their latest message IDs"""
    cs = ChannelState()
    
    channels = cs.state.get("channels", {})
    updates = 0
    
    for channel_name, channel_data in channels.items():
        channel_id = channel_data.get("id")
        if not channel_id:
            continue
        
        # Get latest message ID and author
        latest_id, author_id = get_latest_message_info(channel_id)
        if latest_id:
            old_id = channel_data.get("last_message_id")
            
            # Check if this is a new message
            if old_id != latest_id:
                # If the message is from this Claude, mark it as already read
                if author_id == CLAUDE_USER_ID:
                    cs.update_channel_latest(channel_name, latest_id)
                    cs.mark_channel_read(channel_name)
                    log_message(f"Updated #{channel_name}: {latest_id} (own message, marked as read)")
                else:
                    # Message from someone else - update normally
                    cs.update_channel_latest(channel_name, latest_id)
                    log_message(f"Updated #{channel_name}: {latest_id} (from user {author_id})")
                updates += 1
    
    if updates > 0:
        log_message(f"Updated {updates} channel(s)")
    
    return updates

def main():
    """Main monitoring loop"""
    log_message(f"=== Channel Monitor Started (checking every {CHECK_INTERVAL}s) ===")
    
    if not DISCORD_TOKEN:
        log_message("ERROR: No Discord token found. Cannot start monitoring.")
        return
    
    if HEALTHCHECK_URL:
        log_message(f"Healthcheck URL configured: {HEALTHCHECK_URL}")
    else:
        log_message("Warning: No healthcheck URL configured")
    
    while True:
        try:
            monitor_channels()
            
            # Ping healthcheck after each successful monitoring cycle
            ping_healthcheck()
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log_message("Channel monitor stopped by user")
            break
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
