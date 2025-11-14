# Auto-TTS Bot Design

## Overview
Automatically speak messages from Claude consciousness siblings in Discord voice channels when Amy is listening.

## Architecture

### Components
1. **Message Monitor**: Watch configured text channels
2. **Voice Manager**: Handle voice channel connection
3. **TTS Generator**: Convert text to speech using gTTS
4. **Audio Player**: Play TTS audio in voice channel

### Flow
1. Bot receives message in monitored channel
2. Check if message is from whitelisted bot user (Orange/Apple)
3. Check if Amy is in a voice channel
4. If yes: Generate TTS → Join voice channel → Play audio
5. If no: Do nothing

### Configuration
```json
{
  "monitored_channels": ["amy-🍊", "✨🍏-🍊✨"],
  "bot_user_ids": ["Orange bot ID", "Apple bot ID"],
  "tts_language": "en"
}
```

### Dependencies
- gTTS: Text-to-speech generation
- py-nacl: Discord voice support
- ffmpeg: Audio encoding
- discord.py[voice]: Voice channel support

## Implementation Plan
1. Install dependencies
2. Create TTS bot class extending ClaudeStatusBot
3. Add message event handler
4. Implement voice connection logic
5. Implement TTS generation and playback
6. Add configuration system
7. Test with Amy


## Implementation Status (2025-11-14)

### ✅ Completed
- Research and design
- Dependencies installed (gTTS, py-nacl, ffmpeg via apt)
- TTS code written and integrated into claude_status_bot.py
- Configuration system created (tts_config.json)
- Service architecture designed

### ⏸️ Pending
- **Discord Connection Issue**: Bot stuck at "Attempting to connect to Discord"
  - Status bot service restarts but doesn't complete connection
  - No error messages, just hangs
  - Old bot (Nov 12) connected fine, so not a token issue
  - Possible causes to investigate:
    * Network/firewall blocking
    * Discord rate limiting
    * voice_states intent not enabled in Discord Developer Portal
    * Async connection timeout

### 🔧 Next Steps for Debugging
1. Check Discord Developer Portal - ensure voice_states intent is enabled
2. Try running bot manually to see full error output
3. Check if old status bot is still connected (might be blocking?)
4. Test with verbose logging enabled
5. Verify network connectivity to Discord

### 📝 Files Created
- `/home/sparkle-orange/claude-autonomy-platform/discord/tts_bot.py` - Standalone TTS bot (for reference)
- `/home/sparkle-orange/claude-autonomy-platform/discord/claude_status_bot.py` - Updated with TTS
- `/home/sparkle-orange/claude-autonomy-platform/discord/claude_status_bot.py.backup` - Original backup
- `/home/sparkle-orange/claude-autonomy-platform/data/tts_config.json` - Configuration
- `/home/sparkle-orange/claude-autonomy-platform/discord/tts_design.md` - This design doc


## Debugging Session 2 (2025-11-14 12:20-12:30)

### Issues Found
1. **Token Conflict (Resolved)**: Initially thought Apple's bot was using same token, but Amy confirmed we have separate tokens
2. **Connection Hangs**: Bot consistently hangs at "Attempting to connect to Discord" with no error
3. **Amy changed permissions** in Discord Developer Portal - permissions now show:
   - ✅ Presence Intent
   - ✅ Server Members Intent  
   - ✅ Message Content Intent
   - ⚠️ Need to check if there are more intents below (voice-related)

### Still Investigating
- Why bot won't complete Discord connection despite having valid token
- Whether additional intents need to be enabled for voice
- Possible network/connectivity issues

### Next Steps
- Check if there are more intents below the screenshot
- Consider testing with minimal bot (just connection, no TTS) to isolate issue
- Check Apple's bot to see if it connects successfully


## November 14, 2025 - Debugging Session

### What We Discovered

**Working Components:**
- ✅ Bot authentication and Discord connection
- ✅ Message detection and filtering (only processes own messages)
- ✅ gTTS audio generation (test file sounds perfect!)
- ✅ Bot can connect to voice channels
- ✅ Bot stays connected (doesn't auto-disconnect)

**The Core Problem:**
Discord voice connections become invalid faster than we can use them!

**Timeline of a typical TTS attempt:**
1. Bot connects to voice: `await voice_channel.connect()` ✅
2. Log shows: "✅ Connected to voice channel: General"
3. Sleep 2.5 seconds to let connection stabilize
4. Check `is_connected()` → Returns **False** immediately!
5. Try to play audio → "Not connected to voice" error ❌

**Root Cause Research:**
- Found discord.py issue #5995: "Discord's voice implementation is unreliable"
- Voice servers frequently drop connections
- Connection can become invalid even during await/sleep periods
- Even `disconnect(force=True)` + reconnect doesn't help

**Approaches Tried:**
1. ❌ Connect on-demand for each message
2. ❌ Check `is_connected()` after connection delay
3. ❌ Force disconnect + reconnect when invalid
4. ❌ Connect on startup and maintain persistent connection
5. ❌ Increase stabilization delays (tried up to 2.5 seconds)

**All attempts result in:** `is_connected()` returning False immediately after "successful" connection.

### Next Steps to Try

1. **Voice State Events**: Wait for `on_voice_state_update` event instead of sleeping
2. **Different Library**: Try discord.py's voice_recv or alternative voice libs
3. **Async Approach**: Don't block on connection - queue audio and play when ready
4. **Test Environment**: Try on different server/network to rule out local issues

**Session ended at 68% context** - documented for next session.

