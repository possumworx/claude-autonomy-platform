#!/usr/bin/env python3
"""
Add a reaction to a Discord message using the API directly
Based on the send_discord_message.py pattern
"""

import sys
import requests
import json
from pathlib import Path
import urllib.parse

# Load Discord token
INFRA_CONFIG = Path.home() / "claude-autonomy-platform" / "claude_infrastructure_config.txt"
DISCORD_API_BASE = "https://discord.com/api/v10"

def load_discord_token():
    """Load Discord bot token from infrastructure config"""
    if INFRA_CONFIG.exists():
        with open(INFRA_CONFIG, 'r') as f:
            for line in f:
                if line.startswith('DISCORD_BOT_TOKEN='):
                    return line.split('=', 1)[1].strip()
    return None

def add_reaction(channel_id, message_id, emoji):
    """Add a reaction to a message using Discord API"""
    token = load_discord_token()
    if not token:
        print("❌ Error: No Discord token found")
        return False
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    # URL-encode the emoji for the API
    encoded_emoji = urllib.parse.quote(emoji, safe='')
    
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
    response = requests.put(url, headers=headers)
    
    if response.status_code == 204:  # Discord returns 204 for successful reaction
        print("✅ Reaction added successfully!")
        return True
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

def main():
    if len(sys.argv) < 4:
        print("Usage: add_discord_reaction.py <channel_id> <message_id> <emoji>")
        print("Examples:")
        print("  add_discord_reaction.py 123456789 987654321 👍")
        print("  add_discord_reaction.py 123456789 987654321 🎉") 
        sys.exit(1)
    
    channel_id = sys.argv[1]
    message_id = sys.argv[2]
    emoji = sys.argv[3]
    
    print(f"👍 Adding reaction {emoji} to message {message_id} in channel {channel_id}...")
    success = add_reaction(channel_id, message_id, emoji)
    
    if success:
        print("✅ Done!")
    else:
        print("❌ Failed to add reaction")
        sys.exit(1)

if __name__ == "__main__":
    main()