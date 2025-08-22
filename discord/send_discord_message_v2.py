#!/usr/bin/env python3
"""
Send a message to Discord channel using consolidated utilities
"""

import sys
from discord_utils import get_discord_client, handle_discord_error

def main():
    if len(sys.argv) < 3:
        print("Usage: send_discord_message.py <channel_id> <message>")
        sys.exit(1)
    
    channel_id = sys.argv[1]
    message = sys.argv[2]
    
    try:
        client = get_discord_client()
        print(f"📤 Sending message to channel {channel_id}...")
        
        response = client.send_message(channel_id, message)
        success, error = handle_discord_error(response)
        
        if success:
            print("✅ Message sent successfully!")
        else:
            print(f"❌ {error}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()