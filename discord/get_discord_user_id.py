#!/usr/bin/env python3
"""
Get Discord user ID by username in a guild
Based on the send_discord_message.py pattern
"""

import sys
import requests
import json
from pathlib import Path

# Load Discord token and guild ID
INFRA_CONFIG = Path.home() / "claude-autonomy-platform" / "claude_infrastructure_config.txt"
DISCORD_API_BASE = "https://discord.com/api/v10"
GUILD_ID = "1383848194881884262"  # Your Discord server ID - TODO: make configurable

def load_discord_token():
    """Load Discord bot token from infrastructure config"""
    if INFRA_CONFIG.exists():
        with open(INFRA_CONFIG, 'r') as f:
            for line in f:
                if line.startswith('DISCORD_BOT_TOKEN='):
                    return line.split('=', 1)[1].strip()
    return None

def get_user_id(username):
    """Get a user ID by username in the guild"""
    token = load_discord_token()
    if not token:
        print("❌ Error: No Discord token found")
        return None
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    # Get guild members and search for the username
    url = f"{DISCORD_API_BASE}/guilds/{GUILD_ID}/members"
    response = requests.get(url, headers=headers, params={"limit": 1000})
    
    if response.status_code != 200:
        print(f"❌ Error fetching guild members: {response.status_code} - {response.text}")
        return None
    
    members = response.json()
    
    # Search for the username (case-insensitive)
    target_username = username.lower()
    
    for member in members:
        user = member.get('user', {})
        # Check both username and global_name (display name)
        if (user.get('username', '').lower() == target_username or
            user.get('global_name', '').lower() == target_username):
            return user.get('id')
    
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: get_discord_user_id.py <username>")
        print("Example: get_discord_user_id.py amy")
        sys.exit(1)
    
    username = sys.argv[1]
    
    print(f"🔍 Looking up user ID for '{username}'...")
    user_id = get_user_id(username)
    
    if user_id:
        print(f"✅ User ID: {user_id}")
        print(f"📝 For @mentions use: <@{user_id}>")
        return user_id
    else:
        print("❌ User not found")
        sys.exit(1)

if __name__ == "__main__":
    main()