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

def edit_status(status_text, activity_type="playing"):
    """Update Discord bot status using Discord Gateway (status updates require WebSocket)
    
    Note: This is a simplified implementation. Full status updates typically require
    a persistent WebSocket connection to Discord Gateway. For now, this serves as
    a foundation that could be extended with WebSocket support.
    """
    token = load_discord_token()
    if not token:
        print("❌ Error: No Discord token found")
        return False
    
    # Discord status updates typically require WebSocket connection
    # This is a placeholder that shows the intended functionality
    print("⚠️ Note: Discord status updates require WebSocket Gateway connection")
    print(f"📝 Status update requested: '{status_text}' (type: {activity_type})")
    print("💡 This functionality would need WebSocket implementation for full support")
    
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