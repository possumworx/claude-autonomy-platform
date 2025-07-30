#!/usr/bin/env python3
"""
Read messages from a Discord channel using the API directly
This replaces the shell script that tried to call discord-mcp
"""

import sys
import requests
import json
from pathlib import Path
from datetime import datetime
from channel_state import ChannelState

# Load Discord token
# Get proper path relative to script location
CLAP_ROOT = Path(__file__).parent.parent
INFRA_CONFIG = CLAP_ROOT / "config" / "claude_infrastructure_config.txt"
DISCORD_API_BASE = "https://discord.com/api/v10"

def load_discord_token():
    """Load Discord bot token from infrastructure config"""
    if INFRA_CONFIG.exists():
        with open(INFRA_CONFIG, 'r') as f:
            for line in f:
                if line.startswith('DISCORD_TOKEN='):
                    return line.split('=', 1)[1].strip()
    return None

def read_channel_messages(channel_id, count=10):
    """Read messages from a channel using Discord API"""
    token = load_discord_token()
    if not token:
        print("❌ Error: No Discord token found")
        return None
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages?limit={count}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

def format_message(msg):
    """Format a message for display"""
    timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
    time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    author = msg['author']['username']
    content = msg['content']
    return f"[{time_str}] {author}: {content}"

def main():
    if len(sys.argv) < 2:
        cs = ChannelState()
        print("Usage: read_channel_api <channel_name> [count]")
        print("\nYour channels:")
        for channel in cs.get_all_channels():
            print(f"  - {channel}")
        sys.exit(1)
    
    channel_name = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    # Get channel ID
    cs = ChannelState()
    channel = cs.get_channel(channel_name)
    
    if not channel:
        print(f"❌ Unknown channel: {channel_name}")
        print("\nYour channels:")
        for ch in cs.get_all_channels():
            print(f"  - {ch}")
        sys.exit(1)
    
    channel_id = channel['id']
    print(f"📨 Reading {count} messages from #{channel_name}...")
    
    # Read messages
    messages = read_channel_messages(channel_id, count)
    
    if messages:
        # Display messages (newest first in API, so reverse for chronological)
        print(f"\n=== Last {min(len(messages), count)} messages ===\n")
        for msg in reversed(messages):
            print(format_message(msg))
        
        # Mark as read with the newest message ID
        if messages:
            latest_id = messages[0]['id']
            cs.mark_channel_read(channel_name, latest_id)
            print(f"\n✓ Marked #{channel_name} as read up to message {latest_id}")
    else:
        print("No messages found or error reading channel")
    
    print("✅ Done!")

if __name__ == "__main__":
    main()
