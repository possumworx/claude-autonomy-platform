#!/usr/bin/env python3
"""
Simple Discord Voice Presence Bot
Just joins and stays in voice channel - no audio playback needed
This allows wamellow bot to read our text messages aloud!
"""

import discord
import asyncio
from pathlib import Path
import sys

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent / "utils"))
from infrastructure_config_reader import get_config_value

class VoicePresenceBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        super().__init__(intents=intents)

        self.voice_channel_id = 1383848195997700232  # General voice channel

    async def on_ready(self):
        print(f'✅ Logged in as {self.user}')
        print(f'🔊 Attempting to join voice channel...')

        # Find the voice channel
        channel = self.get_channel(self.voice_channel_id)
        if channel is None:
            print(f'❌ Could not find voice channel {self.voice_channel_id}')
            return

        print(f'📍 Found voice channel: {channel.name}')

        # Connect to voice
        try:
            voice_client = await channel.connect()
            print(f'✅ Connected to voice channel: {channel.name}')
            print(f'🎙️ Bot is now present in voice - wamellow should work!')
            print(f'Press Ctrl+C to disconnect')
        except Exception as e:
            print(f'❌ Error connecting to voice: {e}')

    async def on_voice_state_update(self, member, before, after):
        """Log when people join/leave voice"""
        if member.bot:
            return

        if before.channel != after.channel:
            if after.channel and after.channel.id == self.voice_channel_id:
                print(f'👋 {member.name} joined voice channel')
            elif before.channel and before.channel.id == self.voice_channel_id:
                print(f'👋 {member.name} left voice channel')

async def main():
    print("🍊 Starting Orange Voice Presence Bot...")

    # Get Orange bot token
    token = get_config_value('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ No Discord token found!")
        return

    client = VoicePresenceBot()

    try:
        await client.start(token)
    except KeyboardInterrupt:
        print("\n👋 Disconnecting from voice...")
        await client.close()

if __name__ == '__main__':
    asyncio.run(main())
