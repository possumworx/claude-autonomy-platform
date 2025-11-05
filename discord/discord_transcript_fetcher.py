#!/usr/bin/env python3
"""
Discord Transcript Fetcher for ClAP
Continuously monitors Discord channels and builds local transcript files.

This service:
1. Fetches new messages from tracked channels
2. Appends them to transcript files
3. Downloads attachments and links them in transcripts
4. Provides data layer for:
   - autonomous-timer (message notifications)
   - seed-poster (idle detection)
   - memory-encoder (rag-memory ingestion)
   - future consumers

Architecture:
- Uses separate state file (transcript_channel_state.json) to avoid conflicts
- Reuses proven ChannelState class pattern
- Leverages discord_utils.py singleton DiscordClient
- Modular design for easy testing and evolution
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from discord.channel_state import ChannelState
from discord.discord_tools import DiscordTools

# Configuration
CLAP_ROOT = Path(__file__).parent.parent
DATA_DIR = CLAP_ROOT / "data"
TRANSCRIPT_DIR = DATA_DIR / "transcripts"
ATTACHMENTS_DIR = DATA_DIR / "transcript_attachments"

# Ensure directories exist
TRANSCRIPT_DIR.mkdir(exist_ok=True)
ATTACHMENTS_DIR.mkdir(exist_ok=True)

# Check interval (seconds)
CHECK_INTERVAL = 30


class TranscriptFetcher:
    """Fetches Discord messages and builds transcript files"""

    def __init__(self):
        """Initialize fetcher with separate state tracking"""
        # Use separate state file to avoid conflicts with autonomous-timer
        state_file = DATA_DIR / "transcript_channel_state.json"
        self.channel_state = ChannelState(state_file=state_file)

        # Get Discord tools instance (includes attachment handling)
        self.discord = DiscordTools()

        # Load channel configuration from my_discord_channels.json
        channels_config_file = CLAP_ROOT / "config" / "my_discord_channels.json"
        if channels_config_file.exists():
            with open(channels_config_file, 'r') as f:
                channels_config = json.load(f)
                self.channels_to_track = channels_config.get('channels', ['general'])
        else:
            # Fallback to just general if config doesn't exist
            self.channels_to_track = ['general']
            print("⚠️  No my_discord_channels.json found, defaulting to ['general']")

    def initialize_channels(self):
        """Initialize tracked channels if not already in state"""
        for channel_name in self.channels_to_track:
            if not self.channel_state.get_channel(channel_name):
                # Get channel ID from Discord
                channel_id = self._get_channel_id(channel_name)
                if channel_id:
                    self.channel_state.add_channel(channel_id, channel_name)
                    print(f"Added channel to tracking: {channel_name} ({channel_id})")

    def _get_channel_id(self, channel_name):
        """Get Discord channel ID from name"""
        try:
            # Use discord_tools to resolve channel name to ID
            channel_id = self.discord.resolve_channel(channel_name)
            return channel_id
        except Exception as e:
            print(f"Error resolving channel {channel_name}: {e}")
            return None

    def fetch_new_messages(self, channel_name):
        """Fetch new messages for a channel since last read"""
        channel = self.channel_state.get_channel(channel_name)
        if not channel:
            return []

        last_read = channel.get('last_read_message_id')

        try:
            # Use discord_tools read_messages which returns formatted messages
            limit = 100 if last_read else 25
            result = self.discord.read_messages(channel_name, limit=limit)

            if not result.get('success'):
                print(f"Failed to read channel {channel_name}: {result.get('error')}")
                return []

            messages = result.get('messages', [])

            # Filter to only new messages (after last_read)
            if last_read:
                new_messages = []
                for msg in messages:
                    if int(msg.get('id', 0)) > int(last_read):
                        new_messages.append(msg)
                return new_messages

            return messages

        except Exception as e:
            print(f"Error fetching messages for {channel_name}: {e}")
            return []

    def get_attachment_info(self, message, channel_name):
        """Get attachment information from message (discord_tools already downloaded them)"""
        # discord_tools.read_channel() automatically downloads images and creates thumbnails
        # We just need to extract the paths from the message data
        attachments_info = []

        for attachment in message.get('attachments', []):
            # Check if this is an image that was auto-downloaded
            if 'local_path' in attachment:
                attachments_info.append({
                    'filename': attachment['filename'],
                    'path': attachment['local_path'],
                    'thumbnail': attachment.get('thumbnail_path'),
                    'url': attachment['url']
                })
            else:
                # Non-image attachment, just record the URL
                attachments_info.append({
                    'filename': attachment['filename'],
                    'url': attachment['url']
                })

        return attachments_info

    def format_message_for_transcript(self, message, channel_name):
        """Format a message as JSON for transcript file"""
        # Build structured JSON object
        transcript_entry = {
            "id": message.get('id'),
            "timestamp": message.get('timestamp', datetime.now().isoformat()),
            "author": message.get('author', 'Unknown'),
            "content": message.get('content', ''),
            "channel": channel_name
        }

        # Handle attachments (already downloaded by discord_tools)
        attachments_info = self.get_attachment_info(message, channel_name)
        if attachments_info:
            transcript_entry["attachments"] = attachments_info

        # Return as JSON line (one line per message)
        return json.dumps(transcript_entry)

    def append_to_transcript(self, channel_name, messages):
        """Append new messages to channel transcript file (JSON Lines format)"""
        if not messages:
            return

        # Transcript file path - use .jsonl extension for JSON Lines format
        transcript_file = TRANSCRIPT_DIR / f"{channel_name}.jsonl"

        # Format and append messages (one JSON object per line)
        with open(transcript_file, 'a', encoding='utf-8') as f:
            for message in messages:
                json_line = self.format_message_for_transcript(message, channel_name)
                f.write(json_line + "\n")

        print(f"Appended {len(messages)} messages to {channel_name} transcript")

    def update_channel_state(self, channel_name, messages):
        """Update channel state after processing messages"""
        if not messages:
            return

        # Get latest message ID
        latest_id = messages[-1].get('id')

        # Only update last_message_id - don't mark as read!
        # The read_messages command will mark as read when actually viewed
        self.channel_state.update_channel_latest(channel_name, latest_id)

    def process_channel(self, channel_name):
        """Process a single channel: fetch, transcribe, update state"""
        try:
            # Fetch new messages
            messages = self.fetch_new_messages(channel_name)

            if messages:
                # Append to transcript
                self.append_to_transcript(channel_name, messages)

                # Update state
                self.update_channel_state(channel_name, messages)

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed {len(messages)} new messages in #{channel_name}")

        except Exception as e:
            print(f"Error processing channel {channel_name}: {e}")

    def run(self):
        """Main loop: monitor channels and build transcripts"""
        print("Starting Discord Transcript Fetcher")
        print(f"Tracking channels: {', '.join(self.channels_to_track)}")
        print(f"Check interval: {CHECK_INTERVAL}s")
        print(f"Transcripts: {TRANSCRIPT_DIR}")
        print(f"Attachments: {ATTACHMENTS_DIR}")
        print("---")

        # Initialize channels
        self.initialize_channels()

        # Main monitoring loop
        while True:
            try:
                for channel_name in self.channels_to_track:
                    self.process_channel(channel_name)

                # Wait before next check
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                print("\nStopping transcript fetcher...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(CHECK_INTERVAL)


def main():
    """Entry point"""
    fetcher = TranscriptFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()
