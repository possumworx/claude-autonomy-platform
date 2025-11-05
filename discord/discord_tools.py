#!/usr/bin/env python3
"""
Unified Discord Tools Library for ClAP
Consolidates all Discord functionality with enhanced image handling
Designed for seamless integration with natural commands
"""

import os
import sys
import json
import requests
import time
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from PIL import Image

# Add the utils directory to Python path
utils_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
sys.path.insert(0, utils_dir)
from infrastructure_config_reader import get_config_value

DISCORD_API_BASE = "https://discord.com/api/v10"

class DiscordTools:
    """Unified Discord tools with enhanced image handling"""
    
    def __init__(self):
        self.token = get_config_value('DISCORD_BOT_TOKEN')
        if not self.token:
            raise ValueError("No Discord token found in infrastructure config")
        
        # Set up image storage directory
        self.home_dir = Path.home()
        self.username = os.getlogin()
        self.image_dir = self.home_dir / f"{self.username}-home" / "discord-images"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        # Load channel state for easy name lookup
        self.channel_state_file = Path.home() / "claude-autonomy-platform" / "data" / "channel_state.json"
        self.load_channel_state()
    
    @property
    def headers(self):
        """Get headers for Discord API requests"""
        return {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }
    
    def load_channel_state(self):
        """Load channel mappings from state file"""
        self.channel_map = {}
        try:
            if self.channel_state_file.exists():
                with open(self.channel_state_file, 'r') as f:
                    state = json.load(f)
                    # Create bidirectional mapping
                    channels = state.get('channels', {})
                    for name, channel_info in channels.items():
                        if isinstance(channel_info, dict) and 'id' in channel_info:
                            channel_id = channel_info['id']
                            self.channel_map[name] = channel_id
                            self.channel_map[channel_id] = name
        except Exception as e:
            print(f"Warning: Could not load channel state: {e}")
    
    def resolve_channel(self, channel_identifier: str) -> str:
        """Resolve channel name to ID or return ID if already an ID"""
        # If it's already a channel ID (all digits), return it
        if channel_identifier.isdigit():
            return channel_identifier
        
        # Look up channel name in mapping
        return self.channel_map.get(channel_identifier, channel_identifier)
    
    def send_message(self, channel: str, content: str) -> Dict:
        """Send a message to a Discord channel"""
        channel_id = self.resolve_channel(channel)
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
        data = {"content": content}
        
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": self._format_error(response)}
    
    def edit_message(self, channel: str, message_id: str, content: str) -> Dict:
        """Edit an existing Discord message"""
        channel_id = self.resolve_channel(channel)
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}"
        data = {"content": content}
        
        response = requests.patch(url, headers=self.headers, json=data)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": self._format_error(response)}
    
    def delete_message(self, channel: str, message_id: str) -> Dict:
        """Delete a Discord message"""
        channel_id = self.resolve_channel(channel)
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}"
        
        response = requests.delete(url, headers=self.headers)
        
        if response.status_code == 204:
            return {"success": True}
        else:
            return {"success": False, "error": self._format_error(response)}
    
    def add_reaction(self, channel: str, message_id: str, emoji: str) -> Dict:
        """Add a reaction to a Discord message"""
        channel_id = self.resolve_channel(channel)
        encoded_emoji = requests.utils.quote(emoji)
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
        
        response = requests.put(url, headers={"Authorization": f"Bot {self.token}"})
        
        if response.status_code == 204:
            return {"success": True}
        else:
            return {"success": False, "error": self._format_error(response)}
    
    def read_messages(self, channel: str, limit: int = 25) -> Dict:
        """
        Read messages from a channel with automatic image handling
        Downloads images and adds placeholders to message content
        """
        channel_id = self.resolve_channel(channel)
        channel_name = self.channel_map.get(channel_id, channel)
        
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
        params = {"limit": limit}
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            return {"success": False, "error": self._format_error(response)}
        
        messages = response.json()
        processed_messages = []
        
        for msg in reversed(messages):  # Process in chronological order
            processed_msg = {
                "id": msg["id"],
                "author": msg["author"]["username"],
                "timestamp": msg["timestamp"],
                "content": msg["content"]
            }
            
            # Handle attachments
            if msg.get("attachments"):
                image_placeholders = []
                for i, attachment in enumerate(msg["attachments"]):
                    if self._is_image(attachment.get("content_type", "")):
                        # Download image
                        image_path = self._download_image(
                            attachment["url"],
                            attachment["filename"],
                            channel_name,
                            msg["timestamp"],
                            i
                        )
                        if image_path:
                            placeholder = f"<image: {image_path.name}>"
                            image_placeholders.append(placeholder)
                
                # Add placeholders to content
                if image_placeholders:
                    if processed_msg["content"]:
                        processed_msg["content"] += " " + " ".join(image_placeholders)
                    else:
                        processed_msg["content"] = " ".join(image_placeholders)
            
            processed_messages.append(processed_msg)
        
        return {"success": True, "messages": processed_messages}
    
    def send_image(self, channel: str, image_path: str, message: str = "") -> Dict:
        """Send an image to a Discord channel with optional message"""
        channel_id = self.resolve_channel(channel)
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
        
        # Prepare the file
        image_path = Path(image_path).expanduser()
        if not image_path.exists():
            return {"success": False, "error": f"Image file not found: {image_path}"}
        
        # Detect MIME type
        mime_type = mimetypes.guess_type(str(image_path))[0] or 'application/octet-stream'
        
        # Prepare multipart form data
        files = {
            'file': (image_path.name, open(image_path, 'rb'), mime_type)
        }
        
        data = {}
        if message:
            data['content'] = message
        
        # Send with file (no JSON content-type header for multipart)
        headers = {"Authorization": f"Bot {self.token}"}
        
        try:
            response = requests.post(url, headers=headers, data=data, files=files)
            files['file'][1].close()  # Close the file
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": self._format_error(response)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_file(self, channel: str, file_path: str, message: str = "") -> Dict:
        """Send any file to a Discord channel with optional message"""
        # Reuse send_image logic as it handles any file type
        return self.send_image(channel, file_path, message)
    
    def _is_image(self, content_type: str) -> bool:
        """Check if content type is an image"""
        return content_type.startswith('image/')
    
    def _download_image(self, url: str, filename: str, channel_name: str, 
                       timestamp: str, index: int) -> Optional[Path]:
        """Download an image and save with organized naming, plus create thumbnail"""
        try:
            # Parse timestamp to create readable format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
            time_str = dt.strftime('%H%M%S')
            
            # Create filename: channel-date-time-index-originalname
            ext = Path(filename).suffix or '.jpg'
            new_filename = f"{channel_name}-{date_str}-{time_str}-{index:03d}{ext}"
            
            # Create date-based subdirectory
            date_dir = self.image_dir / date_str
            date_dir.mkdir(exist_ok=True)
            
            save_path = date_dir / new_filename
            thumb_filename = f"{channel_name}-{date_str}-{time_str}-{index:03d}_thumb{ext}"
            thumb_path = date_dir / thumb_filename

            # Check if image and thumbnail already exist
            if save_path.exists() and thumb_path.exists():
                # Already downloaded and thumbnailed, just return the path
                return save_path

            # Download image if not exists
            if not save_path.exists():
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                else:
                    print(f"Failed to download image: {response.status_code}")
                    return None

            # Create thumbnail if not exists
            if not thumb_path.exists():
                try:
                    # Open the image
                    img = Image.open(save_path)

                    # Create thumbnail with max dimension of 800px
                    thumbnail = img.copy()
                    thumbnail.thumbnail((800, 800), Image.Resampling.LANCZOS)

                    # Convert RGBA to RGB if necessary (for JPEG)
                    if thumbnail.mode == 'RGBA' and ext.lower() in ['.jpg', '.jpeg']:
                        rgb_img = Image.new('RGB', thumbnail.size, (255, 255, 255))
                        rgb_img.paste(thumbnail, mask=thumbnail.split()[3] if len(thumbnail.split()) == 4 else None)
                        thumbnail = rgb_img

                    thumbnail.save(thumb_path, quality=85, optimize=True)
                    print(f"✅ Created thumbnail: {thumb_path.name}")

                except Exception as e:
                    print(f"⚠️  Could not create thumbnail: {e}")

            return save_path

        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def get_user_id(self, username: str, discriminator: Optional[str] = None) -> Dict:
        """Get user ID by username"""
        # This would need guild context for proper implementation
        # For now, return error indicating limitation
        return {
            "success": False, 
            "error": "User lookup requires guild context - use full implementation"
        }
    
    def edit_status(self, status_text: str, status_type: str = "online") -> Dict:
        """Update bot status"""
        # This requires gateway connection, not REST API
        # Save status request for bot to pick up
        status_file = Path.home() / "claude-autonomy-platform" / "data" / "bot_status_request.json"
        status_data = {
            "status": status_type,
            "activity": {
                "name": status_text,
                "type": 0  # Playing
            },
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            return {"success": True, "message": "Status update requested"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _format_error(self, response) -> str:
        """Format error message from Discord API response"""
        error_msg = f"Error: {response.status_code}"
        try:
            error_data = response.json()
            if 'message' in error_data:
                error_msg += f" - {error_data['message']}"
        except:
            error_msg += f" - {response.text}"
        return error_msg


# Convenience functions for backward compatibility and natural commands
def get_discord_tools():
    """Get Discord tools instance"""
    return DiscordTools()


def send_message(channel: str, content: str):
    """Send a message (backward compatible)"""
    tools = get_discord_tools()
    result = tools.send_message(channel, content)
    if result["success"]:
        print(f"✅ Message sent to {channel}")
    else:
        print(f"❌ Failed: {result['error']}")
    return result["success"]


def read_channel(channel: str, limit: int = 25):
    """Read channel messages with image handling"""
    tools = get_discord_tools()
    result = tools.read_messages(channel, limit)
    
    if not result["success"]:
        print(f"❌ Failed: {result['error']}")
        return False
    
    print(f"📨 Reading {len(result['messages'])} messages from #{channel}...\n")
    print("=== Messages ===\n")
    
    for msg in result['messages']:
        timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{time_str}] {msg['author']}: {msg['content']}")
    
    return True


def send_image(channel: str, image_path: str, message: str = ""):
    """Send an image with optional message"""
    tools = get_discord_tools()
    result = tools.send_image(channel, image_path, message)
    
    if result["success"]:
        print(f"✅ Image sent to {channel}")
    else:
        print(f"❌ Failed: {result['error']}")
    return result["success"]


if __name__ == "__main__":
    # Test the tools
    print("Discord Tools Library v2.0")
    print("With automatic image handling!")
    print("\nUsage:")
    print("  from discord_tools import get_discord_tools")
    print("  tools = get_discord_tools()")
    print("  tools.send_message('amy-delta', 'Hello!')")
    print("  tools.read_messages('amy-delta')  # Auto-downloads images!")