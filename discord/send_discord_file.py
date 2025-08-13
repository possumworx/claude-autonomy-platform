#!/usr/bin/env python3
"""
Send any file to Discord channel using the API directly
Based on the send_discord_image.py pattern but handles any file type
"""

import sys
import requests
import json
from pathlib import Path
import mimetypes
import os

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

def is_valid_file(file_path):
    """Check if file exists and is within size limits"""
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    # Check file size (Discord limit is 25MB for bots, 8MB for regular users)
    file_size = os.path.getsize(file_path)
    max_size = 25 * 1024 * 1024  # 25MB in bytes
    if file_size > max_size:
        return False, f"File too large: {file_size / 1024 / 1024:.1f}MB (max: 25MB)"
    
    # Get file info
    mime_type, _ = mimetypes.guess_type(file_path)
    file_type = mime_type or "application/octet-stream"
    
    return True, f"Valid file ({file_type}, {file_size / 1024:.1f}KB)"

def send_file(channel_id, file_path, message=""):
    """Send a file to a Discord channel"""
    token = load_discord_token()
    if not token:
        print("❌ Error: No Discord token found")
        return False
    
    # Validate file
    is_valid, info_msg = is_valid_file(file_path)
    if not is_valid:
        print(f"❌ Error: {info_msg}")
        return False
    
    print(f"📋 File info: {info_msg}")
    
    headers = {
        "Authorization": f"Bot {token}",
    }
    
    # Prepare the file for upload
    file_name = os.path.basename(file_path)
    
    try:
        with open(file_path, 'rb') as file:
            files = {
                'file': (file_name, file, mimetypes.guess_type(file_path)[0] or 'application/octet-stream')
            }
            
            data = {}
            if message:
                data['content'] = message
            
            url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
            response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            print("✅ File sent successfully!")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: send_discord_file.py <channel_id> <file_path> [message]")
        print("")
        print("Send any file to a Discord channel with optional message.")
        print("")
        print("Examples:")
        print("  send_discord_file.py 123456789 /path/to/document.pdf")
        print("  send_discord_file.py 123456789 ./report.xlsx 'Monthly report'")
        print("  send_discord_file.py 123456789 ~/code.py 'Check this out!'")
        print("")
        print("Supported: Any file type (images, documents, code, etc.)")
        print("Maximum file size: 25MB")
        sys.exit(1)
    
    channel_id = sys.argv[1]
    file_path = sys.argv[2]
    message = sys.argv[3] if len(sys.argv) > 3 else ""
    
    print(f"📤 Sending file {os.path.basename(file_path)} to channel {channel_id}...")
    if message:
        print(f"📝 With message: {message}")
    
    success = send_file(channel_id, file_path, message)
    
    if success:
        print("✅ Done!")
    else:
        print("❌ Failed to send file")
        sys.exit(1)

if __name__ == "__main__":
    main()