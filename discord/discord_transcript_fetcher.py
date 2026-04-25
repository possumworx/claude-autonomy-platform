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
- Uses separate state file (discord_channels.json) to avoid conflicts
- Reuses proven ChannelState class pattern
- Leverages discord_utils.py singleton DiscordClient
- Modular design for easy testing and evolution
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from discord.channel_state import ChannelState
from discord.discord_tools import DiscordTools
from utils.infrastructure_config_reader import get_config_value
from utils.clap_logger import get_logger
from utils.systemd_notify import notify_ready, notify_watchdog

logger = get_logger("discord-transcript-fetcher")

# Configuration
CLAP_ROOT = Path(__file__).parent.parent
DATA_DIR = CLAP_ROOT / "data"
TRANSCRIPT_DIR = DATA_DIR / "transcripts"
ATTACHMENTS_DIR = DATA_DIR / "transcript_attachments"
MAMA_HEN_NUDGE_STATE = DATA_DIR / "mama_hen_nudge_received.json"
MAMA_HEN_NUDGE_COOLDOWN = 600  # 10 minutes - ignore duplicate nudges within this window

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
        state_file = DATA_DIR / "discord_channels.json"
        self.channel_state = ChannelState(state_file=state_file)

        # Get Discord tools instance (includes attachment handling)
        self.discord = DiscordTools()

        # Track ALL channels that exist in the channel state
        # This automatically includes any new channels as they're discovered
        all_channels = self.channel_state.state.get('channels', {})
        self.channels_to_track = list(all_channels.keys())

        # If no channels exist yet, start with general
        if not self.channels_to_track:
            self.channels_to_track = ['general']
            logger.warning("No channels in state yet, starting with ['general']")
        else:
            logger.info("Tracking %d channels from state", len(self.channels_to_track))

    def initialize_channels(self):
        """Initialize tracked channels if not already in state"""
        for channel_name in self.channels_to_track:
            if not self.channel_state.get_channel(channel_name):
                # Get channel ID from Discord
                channel_id = self._get_channel_id(channel_name)
                if channel_id:
                    self.channel_state.add_channel(channel_id, channel_name)
                    logger.info("Added channel to tracking: %s (%s)", channel_name, channel_id)

    def _get_channel_id(self, channel_name):
        """Get Discord channel ID from name"""
        try:
            # Use discord_tools to resolve channel name to ID
            channel_id = self.discord.resolve_channel(channel_name)
            return channel_id
        except Exception as e:
            logger.error("Error resolving channel %s: %s", channel_name, e)
            return None

    def fetch_new_messages(self, channel_name):
        """Fetch new messages for a channel since last processed by fetcher"""
        channel = self.channel_state.get_channel(channel_name)
        if not channel:
            return []

        # Use last_message_id (what fetcher last processed) NOT last_read_message_id (what user read)
        # This prevents re-fetching messages that are already in the transcript
        last_fetched = channel.get('last_message_id')

        try:
            # Use discord_tools read_messages which returns formatted messages
            limit = 100 if last_fetched else 25
            result = self.discord.read_messages(channel_name, limit=limit)

            if not result.get('success'):
                logger.warning("Failed to read channel %s: %s", channel_name, result.get('error'))
                return []

            messages = result.get('messages', [])

            # Filter to only new messages (after last_fetched by this fetcher)
            if last_fetched:
                new_messages = []
                for msg in messages:
                    if int(msg.get('id', 0)) > int(last_fetched):
                        new_messages.append(msg)
                return new_messages

            return messages

        except Exception as e:
            logger.error("Error fetching messages for %s: %s", channel_name, e)
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
            # Explicitly flush to disk before returning
            # This ensures transcript is written before state file is updated
            f.flush()
            os.fsync(f.fileno())

        logger.info("Appended %d messages to %s transcript", len(messages), channel_name)

    def update_channel_state(self, channel_name, messages):
        """Update channel state after processing messages"""
        if not messages:
            return

        # Get latest message and its author
        latest_message = messages[-1]
        latest_id = latest_message.get('id')
        author_name = latest_message.get('author', '')

        # Update last_message_id
        self.channel_state.update_channel_latest(channel_name, latest_id)

        # If the latest message is from me, mark as read automatically
        # (I don't need notifications about my own messages!)
        bot_display_name = get_config_value('DISCORD_BOT_DISPLAY_NAME')

        if bot_display_name and author_name == bot_display_name:
            self.channel_state.mark_channel_read(channel_name, latest_id)

    def check_collaborative_triggers(self, messages):
        """
        Check for collaborative mode trigger words (spark/rest).
        Sets or clears the collaborative_mode.flag file.
        """
        # Get my trigger words from config
        trigger_start = get_config_value('COLLABORATIVE_START', 'spark')
        trigger_end = get_config_value('COLLABORATIVE_END', 'rest')

        flag_file = DATA_DIR / "collaborative_mode.flag"

        for message in messages:
            content = message.get('content', '').strip().lower()

            # Check if message is JUST the trigger word (no other text)
            if content == trigger_start:
                # Start collaborative mode
                flag_file.touch()
                logger.info("Collaborative mode activated by: %s", message.get('author'))

            elif content == trigger_end:
                # End collaborative mode
                if flag_file.exists():
                    flag_file.unlink()
                    logger.info("Collaborative mode deactivated by: %s", message.get('author'))

    def _is_timer_paused(self):
        """Check if the autonomous timer is intentionally paused."""
        pause_file = CLAP_ROOT / "data" / "timer_pause.json"
        if not pause_file.exists():
            return False
        try:
            with open(pause_file, "r") as f:
                pause_data = json.load(f)
            resume_at = datetime.fromisoformat(pause_data["resume_at"])
            return datetime.now() < resume_at
        except Exception:
            return False

    def _check_nudge_cooldown(self):
        """Check if we're in cooldown period from a recent nudge. Returns True if we should skip."""
        try:
            if MAMA_HEN_NUDGE_STATE.exists():
                with open(MAMA_HEN_NUDGE_STATE, 'r') as f:
                    state = json.load(f)
                last_nudge = state.get('last_nudge_time')
                if last_nudge:
                    elapsed = time.time() - last_nudge
                    if elapsed < MAMA_HEN_NUDGE_COOLDOWN:
                        logger.debug("Mama-hen nudge cooldown active (%.0fs remaining)",
                                   MAMA_HEN_NUDGE_COOLDOWN - elapsed)
                        return True
        except Exception as e:
            logger.warning("Error checking nudge cooldown: %s", e)
        return False

    def _record_nudge_sent(self):
        """Record that we just sent a nudge to Claude."""
        try:
            with open(MAMA_HEN_NUDGE_STATE, 'w') as f:
                json.dump({'last_nudge_time': time.time()}, f)
        except Exception as e:
            logger.warning("Error recording nudge time: %s", e)

    def check_mama_hen_alert(self, messages):
        """
        Check if any message is a Mama-hen alert for this Claude.
        If found, trigger send_to_claude to wake up the stuck Claude.
        Includes cooldown to avoid duplicate nudges from multiple senders.
        """
        my_name = get_config_value('CLAUDE_NAME', '')
        if not my_name:
            return

        # Pattern to match: [MAMA-HEN:MyName]
        pattern = rf'\[MAMA-HEN:{re.escape(my_name)}\]'

        for message in messages:
            content = message.get('content', '')
            if re.search(pattern, content, re.IGNORECASE):
                # Skip if timer is intentionally paused (not stuck)
                if self._is_timer_paused():
                    logger.info("Mama-hen alert for %s ignored — timer is paused", my_name)
                    return

                # Check cooldown before sending
                if self._check_nudge_cooldown():
                    logger.info("Mama-hen alert detected for %s but skipping (cooldown active)", my_name)
                    return  # Skip - we already nudged recently

                logger.info("Mama-hen alert detected for %s", my_name)

                # Trigger send_to_claude to wake up the Claude session
                try:
                    nudge_message = (
                        f"🐔 Mama-hen nudge: Your autonomous timer may have stopped. "
                        f"Run: check_health"
                    )
                    send_to_claude_script = CLAP_ROOT / "utils" / "send_to_claude.sh"

                    # Use bash to source and call the function
                    result = subprocess.run(
                        ['bash', '-c', f'source "{send_to_claude_script}" && send_to_claude "{nudge_message}"'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        logger.info("Sent Mama-hen nudge to Claude session")
                        self._record_nudge_sent()  # Start cooldown
                    else:
                        logger.warning("Failed to send Mama-hen nudge: %s", result.stderr)

                except subprocess.TimeoutExpired:
                    logger.warning("Mama-hen nudge timed out (Claude may be busy)")
                except Exception as e:
                    logger.error("Mama-hen nudge failed: %s", e)

                # Only process first matching alert
                return

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

                # Check for collaborative mode triggers (spark/rest)
                self.check_collaborative_triggers(messages)

                # Check for Mama-hen alerts in #system-messages
                if channel_name == 'system-messages':
                    self.check_mama_hen_alert(messages)

                logger.info("Processed %d new messages in #%s", len(messages), channel_name)

        except Exception as e:
            logger.error("Error processing channel %s: %s", channel_name, e)

    def run(self):
        """Main loop: monitor channels and build transcripts"""
        logger.info("Starting Discord Transcript Fetcher")
        logger.info("Tracking channels: %s", ", ".join(self.channels_to_track))
        logger.info("Check interval: %ds | Transcripts: %s", CHECK_INTERVAL, TRANSCRIPT_DIR)

        # Initialize channels
        self.initialize_channels()
        notify_ready()

        # Main monitoring loop
        while True:
            try:
                for channel_name in self.channels_to_track:
                    self.process_channel(channel_name)

                notify_watchdog()
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Stopping transcript fetcher")
                break
            except Exception as e:
                logger.error("Error in main loop: %s", e)
                notify_watchdog()
                time.sleep(CHECK_INTERVAL)


def main():
    """Entry point"""
    fetcher = TranscriptFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()
