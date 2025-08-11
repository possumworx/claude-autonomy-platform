#!/usr/bin/env python3
"""
Edit a Discord message using the API directly
Based on the send_discord_message.py pattern
"""

import sys
import requests
import json
from pathlib import Path

# Load Discord token
INFRA_CONFIG = Path.home() / "claude-autonomy-platform" / "claude_infrastructure_config.txt"
DISCORD_API_BASE = "https://discord.com/api/v10"

def load_discord_token():
    """Load Discord bot token from infrastructure config"""
    if INFRA_CONFIG.exists():
        with open(INFRA_CONFIG, 'r') as f:
            for line in f:
                if line.startswith('DISCORD_TOKEN='):
                    return line.split('=', 1)[1].strip()
    return None

def edit_message(channel_id, message_id, new_content):
    """Edit a message using Discord API"""
    token = load_discord_token()
    if not token:
        print("❌ Error: No Discord token found")
        return False
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "content": new_content
    }
    
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}"
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("✅ Message edited successfully!")
        return True
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

def main():
    if len(sys.argv) < 4:
        print("Usage: edit_discord_message.py <channel_id> <message_id> <new_content>")
        sys.exit(1)
    
    channel_id = sys.argv[1]
    message_id = sys.argv[2]
    new_content = sys.argv[3]
    
    print(f"📝 Editing message {message_id} in channel {channel_id}...")
    success = edit_message(channel_id, message_id, new_content)
    
    if success:
        print("✅ Done!")
    else:
        print("❌ Failed to edit message")
        sys.exit(1)

if __name__ == "__main__":
    main()