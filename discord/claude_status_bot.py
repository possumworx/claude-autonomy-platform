#!/usr/bin/env python3
"""
Claude Status Bot - Persistent Discord bot for status updates
Based on curl-bot architecture but focused on Claude operational status

This bot maintains a WebSocket connection and watches for status update requests
"""

import discord
from discord.ext import tasks
import json
import asyncio
from pathlib import Path
import sys

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent / "utils"))
from infrastructure_config_reader import get_config_value
from clap_logger import get_logger

logger = get_logger("discord-status-bot")

class ClaudeStatusBot(discord.Client):
    def __init__(self):
        logger.info("Initializing bot class")
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.presences = True
        super().__init__(intents=intents)
        logger.info("Bot class initialized")
        
        self.status_file = Path(__file__).parent.parent / "data" / "bot_status.json"
        self.last_status_check = None
        self.claude_name = get_config_value('CLAUDE_NAME', 'Claude')
        
    async def on_ready(self):
        logger.info("%s Status Bot logged in as %s", self.claude_name, self.user)
        logger.info("Connected to %d guild(s)", len(self.guilds))
        # Set initial status from file if it exists
        await self.update_status_from_file()
        # Start monitoring for changes
        self.status_monitor.start()
        logger.info("Status monitor started")
        
    async def update_status_from_file(self):
        """Update status from the status file"""
        if not self.status_file.exists():
            logger.info("No status file found, using default status")
            await self.change_presence(
                status=discord.Status.online,
                activity=discord.Activity(
                    name="✅ Operational",
                    type=discord.ActivityType.watching
                )
            )
            return
            
        try:
            # Read status request
            with open(self.status_file, 'r') as f:
                status_data = json.load(f)
            
            # Map status types to Discord.Status
            discord_status_map = {
                "online": discord.Status.online,
                "idle": discord.Status.idle,
                "dnd": discord.Status.dnd,
                "invisible": discord.Status.invisible
            }
            
            # Extract presence data
            presence = status_data.get('presence', {})
            status = presence.get('status', 'online')
            activities = presence.get('activities', [])
            
            # Create activity if specified
            activity = None
            if activities:
                act = activities[0]
                activity_type_map = {
                    0: discord.ActivityType.playing,
                    1: discord.ActivityType.streaming,
                    2: discord.ActivityType.listening,
                    3: discord.ActivityType.watching,
                    4: discord.ActivityType.custom,
                    5: discord.ActivityType.competing
                }
                
                activity = discord.Activity(
                    name=act.get('name', 'ClAP Status'),
                    type=activity_type_map.get(act.get('type', 3), discord.ActivityType.watching)
                )
            
            # Update presence
            await self.change_presence(
                status=discord_status_map.get(status, discord.Status.online),
                activity=activity
            )
            
            logger.info("Updated status: %s - %s", status, activity.name if activity else "No activity")

        except Exception as e:
            logger.error("Error updating status: %s", e)
    
    @tasks.loop(seconds=5)
    async def status_monitor(self):
        """Monitor for status update requests"""
        if not self.status_file.exists():
            return
            
        try:
            # Check if status file has been updated
            stat = self.status_file.stat()
            if self.last_status_check and stat.st_mtime <= self.last_status_check:
                return
                
            self.last_status_check = stat.st_mtime
            
            # Update status from file
            await self.update_status_from_file()
            
        except Exception as e:
            logger.error("Error in status monitor: %s", e)


async def run_bot():
    """Run the bot asynchronously"""
    token = get_config_value('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("No Discord bot token found in config")
        sys.exit(1)

    logger.info("Starting %s Status Bot...", get_config_value('CLAUDE_NAME', 'Claude'))
    logger.info("Status file: %s", Path(__file__).parent.parent / 'data' / 'bot_status.json')

    bot = ClaudeStatusBot()

    try:
        logger.info("Attempting to connect to Discord...")
        await bot.start(token)
    except discord.LoginFailure as e:
        logger.error("Discord login failed: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("Bot error: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting bot")
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Status bot shutting down")