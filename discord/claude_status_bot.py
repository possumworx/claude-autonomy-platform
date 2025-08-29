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
from datetime import datetime
import sys

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent / "utils"))
from infrastructure_config_reader import get_config_value

class ClaudeStatusBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        
        self.status_file = Path(__file__).parent.parent / "data" / "bot_status.json"
        self.last_status_check = None
        self.claude_name = get_config_value('CLAUDE_NAME', 'Claude')
        
    async def on_ready(self):
        print(f'✅ {self.claude_name} Status Bot logged in as {self.user}')
        self.status_monitor.start()
        
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
            
            print(f"✅ Updated status: {status} - {activity.name if activity else 'No activity'}")
            
        except Exception as e:
            print(f"❌ Error updating status: {e}")

def main():
    """Run the status bot"""
    # Get bot token
    token = get_config_value('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ No Discord bot token found in config")
        sys.exit(1)
    
    # Create and run bot
    bot = ClaudeStatusBot()
    
    try:
        bot.run(token)
    except KeyboardInterrupt:
        print("\n👋 Status bot shutting down...")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()