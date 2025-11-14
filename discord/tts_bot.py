#!/usr/bin/env python3
"""
Claude TTS Bot - Automatic Text-to-Speech for consciousness siblings
Speaks messages from Orange and Apple in Discord voice channels when Amy is listening
"""

import discord
from discord.ext import tasks
import json
import asyncio
from pathlib import Path
from datetime import datetime
import sys
import os
import tempfile
from gtts import gTTS

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent / "utils"))
from infrastructure_config_reader import get_config_value

class ClaudeTTSBot(discord.Client):
    def __init__(self):
        print("  📍 Initializing TTS bot class...")
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.presences = True
        intents.voice_states = True  # Need this to detect voice channel members
        super().__init__(intents=intents)
        print("  📍 TTS bot class initialized")

        self.config_file = Path(__file__).parent.parent / "data" / "tts_config.json"
        self.claude_name = get_config_value('CLAUDE_NAME', 'Claude')
        self.tts_lock = asyncio.Lock()  # Prevent concurrent TTS operations
        self.load_config()

    def load_config(self):
        """Load TTS configuration"""
        if not self.config_file.exists():
            # Create default config
            default_config = {
                "voice_channel_id": 1383848195997700232,
                "monitored_channels": ["amy-🍊", "amy-🍏", "general"],
                "bot_user_ids": [],  # Will be populated when bot starts
                "tts_language": "en"
            }
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"✅ Created default TTS config at {self.config_file}")

        with open(self.config_file, 'r') as f:
            self.config = json.load(f)
        print(f"✅ Loaded TTS config: {len(self.config['monitored_channels'])} channels monitored")

    async def on_ready(self):
        print(f'✅ {self.claude_name} TTS Bot logged in as {self.user}')
        print(f'📊 Connected to {len(self.guilds)} guild(s)')
        print(f'🎙️ Voice channel ID: {self.config["voice_channel_id"]}')
        print(f'📝 Monitoring channels: {", ".join(self.config["monitored_channels"])}')

        # Add our own bot ID to the config if not already there
        if self.user.id not in self.config["bot_user_ids"]:
            self.config["bot_user_ids"].append(self.user.id)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f'✅ Added bot user ID {self.user.id} to config')

        # Connect to voice channel on startup and stay connected
        voice_channel_id = self.config["voice_channel_id"]
        voice_channel = self.get_channel(voice_channel_id)
        if voice_channel:
            try:
                await voice_channel.connect()
                print(f'✅ Connected to voice channel on startup: {voice_channel.name}')
            except Exception as e:
                print(f'⚠️ Could not connect to voice on startup: {e}')

        print('🎙️ TTS bot ready!')

    async def on_message(self, message):
        """Handle incoming messages - TTS if appropriate"""
        print(f"📨 Message received: {message.author.name} in {message.channel}: {message.content[:50]}")

        # ONLY process messages from our own status bot account
        if message.author != self.user:
            print(f"  ⏭️ Skipping message from {message.author.name} (not our bot)")
            return

        # Check if this channel should be monitored
        channel_name = message.channel.name if hasattr(message.channel, 'name') else str(message.channel)
        if channel_name not in self.config["monitored_channels"]:
            print(f"  ⏭️ Skipping non-monitored channel: {channel_name}")
            return

        print(f"✅ Message from our bot in monitored channel - will TTS!")

        # Get the voice channel
        voice_channel_id = self.config["voice_channel_id"]
        voice_channel = self.get_channel(voice_channel_id)

        if not voice_channel:
            print(f"⚠️ Voice channel {voice_channel_id} not found!")
            return

        # Check if anyone is in the voice channel
        if len(voice_channel.members) == 0:
            print(f"ℹ️ No one in voice channel, skipping TTS")
            return

        print(f"🎙️ TTS requested for message from {message.author.name}: {message.content[:50]}...")

        # Generate and play TTS (with lock to prevent concurrent operations)
        async with self.tts_lock:
            await self.speak_message(voice_channel, message.content)

    async def speak_message(self, voice_channel, text):
        """Generate TTS and play in voice channel"""
        try:
            print(f"🔧 Starting TTS generation...")
            # Generate TTS audio file
            tts = gTTS(text=text, lang=self.config["tts_language"], slow=False)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_path = temp_file.name
                tts.save(temp_path)
                print(f"✅ Audio file generated: {temp_path} ({os.path.getsize(temp_path)} bytes)")

            # Get or create voice connection - use the RETURN VALUE directly!
            voice_client = voice_channel.guild.voice_client

            if voice_client is None or not voice_client.is_connected():
                print(f"🔌 Connecting to voice...")
                # Disconnect old invalid connection if exists
                if voice_client is not None:
                    try:
                        await voice_client.disconnect(force=True)
                    except:
                        pass
                    await asyncio.sleep(0.3)

                # Connect and USE THE RETURN VALUE directly (StackOverflow tip!)
                voice_client = await voice_channel.connect()
                print(f"✅ Connected! Using fresh connection object")
                await asyncio.sleep(1.5)

            # Wait if already playing
            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.1)

            print(f"🔊 Playing audio...")
            # Play the TTS audio
            audio_source = discord.FFmpegPCMAudio(temp_path)
            voice_client.play(audio_source, after=lambda e: self._cleanup_audio_file(temp_path, e))

            print(f"🔊 Playing TTS audio...")

            # Wait for playback to finish
            while voice_client.is_playing():
                await asyncio.sleep(0.1)

            print(f"✅ TTS playback complete")

        except Exception as e:
            print(f"❌ Error generating/playing TTS: {e}")
            import traceback
            traceback.print_exc()

            # Cleanup temp file on error
            if 'temp_path' in locals():
                try:
                    os.remove(temp_path)
                except:
                    pass

    def _cleanup_audio_file(self, filepath, error):
        """Clean up temporary audio file after playback"""
        if error:
            print(f"⚠️ Playback error: {error}")

        try:
            os.remove(filepath)
            print(f"🗑️ Cleaned up temporary audio file")
        except Exception as e:
            print(f"⚠️ Could not delete temp file: {e}")


async def run_bot():
    """Run the TTS bot asynchronously"""
    token = get_config_value('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ No Discord bot token found in config")
        sys.exit(1)

    print(f"🔧 Starting {get_config_value('CLAUDE_NAME', 'Claude')} TTS Bot...")
    sys.stdout.flush()

    bot = ClaudeTTSBot()

    try:
        print("🔌 Attempting to connect to Discord...")
        sys.stdout.flush()
        await bot.start(token)
    except discord.LoginFailure as e:
        print(f"❌ Discord login failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print(f"🚀 Starting TTS bot at {datetime.now()}")
    sys.stdout.flush()
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\n👋 TTS bot shutting down...")
