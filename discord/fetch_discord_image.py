#!/usr/bin/env python3
"""
Fetch/download images from Discord messages using the API directly
Downloads images from message attachments and saves them locally
"""

import sys
import requests
import json
from pathlib import Path
import os

# Load Discord token
INFRA_CONFIG = Path.home() / "claude-autonomy-platform" / "claude_infrastructure_config.txt"
DISCORD_API_BASE = "https://discord.com/api/v10"

def load_discord_token():
    """Load Discord bot token from ClAP infrastructure configuration"""
    infra_config_path = Path.home() / "claude-autonomy-platform" / "config" / "claude_infrastructure_config.txt"
    
    if infra_config_path.exists():
        try:
            with open(infra_config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('DISCORD_BOT_TOKEN='):
                        return line.split('=', 1)[1]
        except Exception as e:
            print(f"❌ Error reading infrastructure config: {e}")
    return None

def get_message_attachments(channel_id, message_id):
    """Get message details including attachments"""
    token = load_discord_token()
    if not token:
        print("❌ Error: No Discord token found")
        return None
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        message = response.json()
        return message.get('attachments', [])
    else:
        print(f"❌ Error fetching message: {response.status_code} - {response.text}")
        return None

def download_attachment(attachment, save_dir="."):
    """Download a Discord attachment"""
    try:
        url = attachment['url']
        filename = attachment['filename']
        
        print(f"📥 Downloading {filename}...")
        
        # Download the file
        response = requests.get(url)
        if response.status_code == 200:
            # Create save directory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)
            
            # Save the file
            file_path = os.path.join(save_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded to: {file_path}")
            return file_path
        else:
            print(f"❌ Error downloading: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error downloading attachment: {e}")
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: fetch_discord_image.py <channel_id> <message_id> [save_directory]")
        print("")
        print("Fetch and download images from a Discord message.")
        print("")
        print("Examples:")
        print("  fetch_discord_image.py 123456789 987654321")
        print("  fetch_discord_image.py 123456789 987654321 ~/Downloads/hedgehog_photos")
        print("")
        print("This will download all attachments from the specified message.")
        sys.exit(1)
    
    channel_id = sys.argv[1]
    message_id = sys.argv[2]
    save_dir = sys.argv[3] if len(sys.argv) > 3 else "./discord_downloads"
    
    print(f"🔍 Fetching attachments from message {message_id} in channel {channel_id}...")
    
    # Get message attachments
    attachments = get_message_attachments(channel_id, message_id)
    
    if attachments is None:
        print("❌ Failed to fetch message")
        sys.exit(1)
    
    if not attachments:
        print("📋 No attachments found in message")
        sys.exit(0)
    
    print(f"📎 Found {len(attachments)} attachment(s)")
    
    # Download each attachment
    downloaded_files = []
    for i, attachment in enumerate(attachments):
        print(f"\n📥 Attachment {i+1}/{len(attachments)}:")
        print(f"   📄 Filename: {attachment['filename']}")
        print(f"   📏 Size: {attachment['size'] / 1024:.1f} KB")
        print(f"   🔗 Type: {attachment.get('content_type', 'unknown')}")
        
        file_path = download_attachment(attachment, save_dir)
        if file_path:
            downloaded_files.append(file_path)
    
    if downloaded_files:
        print(f"\n✅ Successfully downloaded {len(downloaded_files)} file(s):")
        for file_path in downloaded_files:
            print(f"   📁 {file_path}")
    else:
        print("\n❌ No files were downloaded")
        sys.exit(1)

if __name__ == "__main__":
    main()