#!/usr/bin/env python3
"""
Consolidated Discord utilities for ClAP
Provides common functionality for all Discord operations
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add the utils directory to Python path for infrastructure_config_reader
utils_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
sys.path.insert(0, utils_dir)
from infrastructure_config_reader import get_config_value

DISCORD_API_BASE = "https://discord.com/api/v10"

class DiscordClient:
    """Singleton Discord client for API operations"""
    _instance = None
    _token = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the Discord client with token"""
        self._token = get_config_value('DISCORD_BOT_TOKEN')
        if not self._token:
            raise ValueError("No Discord token found in infrastructure config")
    
    @property
    def headers(self):
        """Get headers for Discord API requests"""
        return {
            "Authorization": f"Bot {self._token}",
            "Content-Type": "application/json"
        }
    
    def send_message(self, channel_id, content):
        """Send a message to a Discord channel"""
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
        data = {"content": content}
        response = requests.post(url, headers=self.headers, json=data)
        return response
    
    def edit_message(self, channel_id, message_id, content):
        """Edit an existing Discord message"""
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}"
        data = {"content": content}
        response = requests.patch(url, headers=self.headers, json=data)
        return response
    
    def delete_message(self, channel_id, message_id):
        """Delete a Discord message"""
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}"
        response = requests.delete(url, headers=self.headers)
        return response
    
    def add_reaction(self, channel_id, message_id, emoji):
        """Add a reaction to a Discord message"""
        # URL encode the emoji for the API
        encoded_emoji = requests.utils.quote(emoji)
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
        response = requests.put(url, headers={"Authorization": f"Bot {self._token}"})
        return response
    
    def get_messages(self, channel_id, limit=50):
        """Get messages from a Discord channel"""
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
        params = {"limit": limit}
        response = requests.get(url, headers=self.headers, params=params)
        return response
    
    def get_user(self, user_id):
        """Get user information"""
        url = f"{DISCORD_API_BASE}/users/{user_id}"
        response = requests.get(url, headers=self.headers)
        return response

def get_discord_client():
    """Get the singleton Discord client instance"""
    return DiscordClient()

def handle_discord_error(response):
    """Standard error handling for Discord API responses"""
    if response.status_code == 200:
        return True, None
    elif response.status_code == 204:  # No content (success for some operations)
        return True, None
    else:
        error_msg = f"Error: {response.status_code}"
        try:
            error_data = response.json()
            if 'message' in error_data:
                error_msg += f" - {error_data['message']}"
        except:
            error_msg += f" - {response.text}"
        return False, error_msg