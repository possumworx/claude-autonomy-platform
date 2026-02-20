#!/usr/bin/env python3
"""
Channel-based state management for ClAP
Tracks Discord channels instead of users - simpler and unified!
"""

import json
from pathlib import Path
from datetime import datetime

class ChannelState:
    def __init__(self, state_file=None):
        if state_file is None:
            # Default to data/discord_channels.json relative to ClAP root
            clap_root = Path(__file__).parent.parent
            state_file = clap_root / "data" / "discord_channels.json"
        self.state_file = Path(state_file)
        # Ensure data directory exists
        self.state_file.parent.mkdir(exist_ok=True)
        self.state = self._load_state()
    
    def _load_state(self):
        """Load state from file or create new"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {"channels": {}}
    
    def save(self):
        """Save state to file with reload-merge to prevent race conditions"""
        # Reload from disk first to catch any concurrent modifications
        current_disk_state = self._load_state()

        # Merge changes: preserve any fields that were updated on disk
        # while keeping our in-memory changes
        for channel_name, channel_data in self.state.get("channels", {}).items():
            if channel_name in current_disk_state.get("channels", {}):
                # Merge: keep whichever value is newer/non-None for each field
                disk_channel = current_disk_state["channels"][channel_name]

                # Preserve last_read_message_id if it was updated on disk
                if disk_channel.get("last_read_message_id") and \
                   disk_channel.get("last_read_message_id") != channel_data.get("last_read_message_id"):
                    # Disk has a different last_read - keep the higher ID (more recent)
                    disk_read = int(disk_channel.get("last_read_message_id") or 0)
                    mem_read = int(channel_data.get("last_read_message_id") or 0)
                    if disk_read > mem_read:
                        channel_data["last_read_message_id"] = disk_channel["last_read_message_id"]

        # Add any channels that exist on disk but not in memory
        for channel_name, channel_data in current_disk_state.get("channels", {}).items():
            if channel_name not in self.state.get("channels", {}):
                if "channels" not in self.state:
                    self.state["channels"] = {}
                self.state["channels"][channel_name] = channel_data

        # Now save our merged state
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def add_channel(self, channel_id, name):
        """Add a channel to track"""
        self.state["channels"][name] = {
            "id": channel_id,
            "name": name,
            "last_read_message_id": None,
            "last_message_id": None,
            "updated_at": datetime.now().isoformat()
        }
        self.save()
    
    def mark_channel_read(self, channel_name, message_id=None):
        """Mark channel as read up to current or specified message"""
        if channel_name in self.state["channels"]:
            channel = self.state["channels"][channel_name]
            # If no message_id provided, mark as caught up to last_message_id
            channel["last_read_message_id"] = message_id or channel.get("last_message_id")
            self.save()
            channel["updated_at"] = datetime.now().isoformat()
            self.save()
    
    def update_channel_latest(self, channel_name, message_id):
        """Update the latest message seen in channel"""
        if channel_name in self.state["channels"]:
            self.state["channels"][channel_name]["last_message_id"] = message_id
            self.save()
    
    def get_channel(self, channel_name):
        """Get channel info by name"""
        return self.state["channels"].get(channel_name)
    
    def get_all_channels(self):
        """Get all tracked channels"""
        return list(self.state["channels"].keys())
    
    def get_channel_id(self, channel_name):
        """Get Discord ID for a channel"""
        channel = self.get_channel(channel_name)
        return channel["id"] if channel else None
