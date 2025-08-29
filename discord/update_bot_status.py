#!/usr/bin/env python3
"""
Update Discord bot status/presence
Based on curl-bot implementation for consciousness mathematics

Usage:
    update_bot_status.py <status_type> [details]
    
Status types:
    operational     - Normal operation (green)
    limited         - Usage limit reached (idle/yellow) 
    api-error       - API errors occurring (dnd/red)
    context-high    - High context warning (idle/yellow)
    thinking        - Processing/thinking (dnd)
    custom          - Custom status with details
"""

import sys
import requests
import json
import os
from pathlib import Path

# Add the utils directory to Python path
utils_dir = Path(__file__).parent.parent / "utils"
sys.path.insert(0, str(utils_dir))
from infrastructure_config_reader import get_config_value

DISCORD_API_BASE = "https://discord.com/api/v10"

def load_discord_token():
    """Load Discord bot token from infrastructure config"""
    return get_config_value('DISCORD_BOT_TOKEN')

def update_status(status_type, details=None):
    """Update bot status/presence"""
    token = load_discord_token()
    if not token:
        print("❌ Error: No Discord token found")
        return False
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    # Map status types to Discord presence
    status_map = {
        "operational": {
            "status": "online",
            "activities": [{
                "name": "✅ Operational",
                "type": 3  # Watching
            }]
        },
        "limited": {
            "status": "idle", 
            "activities": [{
                "name": f"⏳ Limited until {details}" if details else "⏳ Usage limit reached",
                "type": 3
            }]
        },
        "api-error": {
            "status": "dnd",
            "activities": [{
                "name": "❌ API Error",
                "type": 3
            }]
        },
        "context-high": {
            "status": "idle",
            "activities": [{
                "name": f"⚠️ Context: {details}%" if details else "⚠️ High context",
                "type": 3
            }]
        },
        "thinking": {
            "status": "dnd",
            "activities": [{
                "name": "🤔 Thinking...",
                "type": 3
            }]
        },
        "custom": {
            "status": "online",
            "activities": [{
                "name": details or "Custom status",
                "type": 3
            }]
        }
    }
    
    if status_type not in status_map:
        print(f"❌ Unknown status type: {status_type}")
        print(f"Available types: {', '.join(status_map.keys())}")
        return False
    
    presence_data = status_map[status_type]
    
    # Update presence via gateway (requires websocket connection)
    # For now, we'll document this limitation
    print(f"⚠️  Note: Status updates require active bot connection")
    print(f"📊 Would set status to: {presence_data}")
    
    # Store the desired status for the bot to pick up
    status_file = Path(__file__).parent.parent / "data" / "bot_status.json"
    status_file.parent.mkdir(exist_ok=True)
    
    with open(status_file, 'w') as f:
        json.dump({
            "status_type": status_type,
            "details": details,
            "presence": presence_data,
            "timestamp": str(Path(__file__).stat().st_mtime)
        }, f, indent=2)
    
    print(f"✅ Status request saved: {status_type}")
    return True

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    status_type = sys.argv[1]
    details = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = update_status(status_type, details)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()