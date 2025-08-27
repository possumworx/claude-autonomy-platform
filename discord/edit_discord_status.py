#!/usr/bin/env python3
"""
Update Discord bot status using the API directly
Based on the send_discord_message.py pattern
"""

import sys
import requests
import json
from pathlib import Path

# Load Discord token
INFRA_CONFIG = Path.home() / "claude-autonomy-platform" / "config" / "claude_infrastructure_config.txt"
DISCORD_API_BASE = "https://discord.com/api/v10"

def load_discord_token():
    """Load Discord bot token from infrastructure config"""
    if INFRA_CONFIG.exists():
        with open(INFRA_CONFIG, 'r') as f:
            for line in f:
                if line.startswith('DISCORD_BOT_TOKEN='):
                    return line.split('=', 1)[1].strip()
    return None

def edit_status(status_text, activity_type="playing"):
    """Update Discord bot status using a temporary WebSocket connection
    
    This creates a brief connection to update the bot's status, then disconnects.
    Perfect for CLI tools that need to update status without maintaining a persistent connection.
    """
    token = load_discord_token()
    if not token:
        print("❌ Error: No Discord token found")
        return False
    
    # Import discord.py for the status update
    try:
        import discord
    except ImportError:
        print("❌ Error: discord.py not installed")
        print("Install with: pip install discord.py")
        return False
    
    # Create a minimal bot client just for status update
    class StatusUpdater(discord.Client):
        def __init__(self, status_text, activity_type):
            super().__init__(intents=discord.Intents.default())
            self.status_text = status_text
            self.activity_type = activity_type
            self.update_complete = False
            
        async def on_ready(self):
            # Map activity types
            activity_type_map = {
                "playing": discord.ActivityType.playing,
                "streaming": discord.ActivityType.streaming,
                "listening": discord.ActivityType.listening,
                "watching": discord.ActivityType.watching,
                "custom": discord.ActivityType.custom,
                "competing": discord.ActivityType.competing
            }
            
            activity = discord.Activity(
                name=self.status_text,
                type=activity_type_map.get(self.activity_type, discord.ActivityType.playing)
            )
            
            await self.change_presence(activity=activity)
            print(f"✅ Status updated: {self.activity_type} {self.status_text}")
            
            # Close after update
            await self.close()
            self.update_complete = True
    
    # Run the status update
    import asyncio
    client = StatusUpdater(status_text, activity_type)
    
    try:
        # Run until the status is updated
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.start(token))
    except Exception as e:
        print(f"❌ Error updating status: {e}")
        return False
    
    return True
    
    # For now, just validate the parameters and show what would be sent
    activity_types = {
        "playing": 0,
        "streaming": 1, 
        "listening": 2,
        "watching": 3,
        "custom": 4,
        "competing": 5
    }
    
    if activity_type.lower() not in activity_types:
        print(f"❌ Invalid activity type. Valid types: {', '.join(activity_types.keys())}")
        return False
        
    status_payload = {
        "op": 3,  # Presence Update
        "d": {
            "status": "online",
            "activities": [{
                "name": status_text,
                "type": activity_types[activity_type.lower()]
            }]
        }
    }
    
    print(f"✅ Status payload prepared: {json.dumps(status_payload, indent=2)}")
    print("📋 To implement: Send this via WebSocket to Discord Gateway")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: edit_discord_status.py <status_text> [activity_type]")
        print("")
        print("Activity types:")
        print("  playing   - 'Playing <status>'")
        print("  streaming - 'Streaming <status>'") 
        print("  listening - 'Listening to <status>'")
        print("  watching  - 'Watching <status>'")
        print("  custom    - Custom status")
        print("  competing - 'Competing in <status>'")
        print("")
        print("Examples:")
        print("  edit_discord_status.py 'autonomous mode'")
        print("  edit_discord_status.py 'hedgehog care' watching")
        sys.exit(1)
    
    status_text = sys.argv[1]
    activity_type = sys.argv[2] if len(sys.argv) > 2 else "playing"
    
    print(f"🔄 Updating Discord status...")
    success = edit_status(status_text, activity_type)
    
    if success:
        print("✅ Status update prepared successfully!")
        print("💡 Full implementation requires WebSocket Gateway connection")
    else:
        print("❌ Failed to prepare status update")
        sys.exit(1)

if __name__ == "__main__":
    main()