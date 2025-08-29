#!/usr/bin/env python3
"""
Save Discord status request for bot to pick up
This is a lightweight alternative that doesn't require discord.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

def save_status_request(status_type, details=None):
    """Save status request to file for bot to pick up"""
    
    # Map status types to Discord presence
    status_map = {
        "operational": {
            "status": "online",
            "activity": {
                "name": "✅ Operational",
                "type": 3  # Watching
            }
        },
        "limited": {
            "status": "idle", 
            "activity": {
                "name": f"⏳ Limited until {details}" if details else "⏳ Usage limit",
                "type": 3
            }
        },
        "api-error": {
            "status": "dnd",
            "activity": {
                "name": "❌ API Error",
                "type": 3
            }
        },
        "context-high": {
            "status": "idle",
            "activity": {
                "name": f"⚠️ Context: {details}%" if details else "⚠️ High context",
                "type": 3
            }
        }
    }
    
    if status_type not in status_map:
        print(f"❌ Unknown status type: {status_type}")
        return False
    
    presence_data = status_map[status_type]
    
    # Save the status request
    status_file = Path(__file__).parent.parent / "data" / "bot_status_request.json"
    status_file.parent.mkdir(exist_ok=True)
    
    with open(status_file, 'w') as f:
        json.dump({
            "status_type": status_type,
            "details": details,
            "presence": presence_data,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"✅ Status request saved: {status_type}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: save_status_request.py <status_type> [details]")
        sys.exit(1)
    
    status_type = sys.argv[1]
    details = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = save_status_request(status_type, details)
    sys.exit(0 if success else 1)