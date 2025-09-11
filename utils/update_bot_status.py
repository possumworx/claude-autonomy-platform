#!/usr/bin/env python3
"""
Update bot status file for Discord status bot
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def update_bot_status(status_text, status_type="playing"):
    """Update the bot status file"""
    home = Path.home()
    status_file = home / "claude-autonomy-platform" / "data" / "bot_status.json"
    
    # Create data directory if it doesn't exist
    status_file.parent.mkdir(exist_ok=True)
    
    # Write simple format that simple_status_bot.py expects
    data = {
        "status": status_text,
        "type": status_type,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(status_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Updated bot_status.json: {status_type} {status_text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: update_bot_status.py <status_text> [status_type]")
        print("Types: playing, streaming, listening, watching")
        sys.exit(1)
    
    status_text = sys.argv[1]
    status_type = sys.argv[2] if len(sys.argv) > 2 else "playing"
    
    update_bot_status(status_text, status_type)