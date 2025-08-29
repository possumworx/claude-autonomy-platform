# Discord Status Updates

The autonomous timer automatically updates the Discord bot's status to reflect Delta's current operational state.

## Status Types

- **✅ Operational** (green/online) - Normal operation, everything working
- **⚠️ Context XX%** (yellow/idle) - High context usage (80%+) with percentage
- **⏳ Limited until [time]** (yellow/idle) - API usage limit reached
- **❌ API Error** (red/dnd) - API errors or malformed responses

## Integration Points

The Discord status is automatically updated at these key points:

1. **On Startup** - Sets to "operational" if no errors exist
2. **Context Warnings** - Updates to "context-high" when context reaches 80%+
3. **Error Detection** - Updates based on API errors, usage limits, etc.
4. **Error Recovery** - Returns to "operational" when errors clear
5. **Context Recovery** - Returns to "operational" when context drops below 80%

## Implementation

The status updates use discord.py to create temporary WebSocket connections that:
- Connect to Discord
- Update the bot's presence/status
- Disconnect immediately after

This approach is perfect for CLI tools that need to update status without maintaining persistent connections.

## Technical Details

- Status updates are handled by `update_discord_status()` in `core/autonomous_timer.py`
- The function maps status types to Discord presence states
- Falls back to saving status requests if discord.py is unavailable
- All status changes are logged in `logs/autonomous_timer.log`

## Testing

To manually test status updates:
```bash
# Test different status types
python3 discord/edit_discord_status.py "Testing status" watching
```

The autonomous timer will automatically manage status based on system state.