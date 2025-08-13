#!/usr/bin/env python3
"""
Send a message to Discord channel using the API directly
Based on the read_channel_api.py pattern
"""

import sys
import requests
import json
import os

# Add the utils directory to Python path for infrastructure_config_reader
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from infrastructure_config_reader import get_config_value

DISCORD_API_BASE = "https://discord.com/api/v10"

def load_discord_token():
    """Load Discord bot token from infrastructure config"""
    return get_config_value('DISCORD_BOT_TOKEN')

def send_message(channel_id, message):
    """Send a message to a channel using Discord API"""
    token = load_discord_token()
    if not token:
        print("❌ Error: No Discord token found")
        return False
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "content": message
    }
    
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("✅ Message sent successfully!")
        return True
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: send_discord_message.py <channel_id> <message>")
        sys.exit(1)
    
    channel_id = sys.argv[1]
    message = sys.argv[2]
    
    print(f"📤 Sending message to channel {channel_id}...")
    success = send_message(channel_id, message)
    
    if success:
        print("✅ Done!")
    else:
        print("❌ Failed to send message")
        sys.exit(1)

if __name__ == "__main__":
    main()