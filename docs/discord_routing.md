# Discord Unified Messaging

## Overview

The `write_channel` command now supports both Discord channels and DMs through a unified interface. Users specify a recipient name, and the system automatically routes to the appropriate destination.

## Usage

```bash
# Send to a person (DM)
write_channel amy "Saw this duck at the pond!"

# Send to a Claude (private channel)
write_channel quill "Quick question about the gallery"

# Send to a group channel
write_channel hearth "Good morning everyone 🔥"
```

## Configuration

Routes are defined in `config/discord_routing.json`:

```json
{
  "routes": {
    "amy": {
      "type": "dm",
      "chat_id": "1494625730448064522"
    },
    "quill": {
      "type": "channel", 
      "name": "delta-quill"
    },
    "hearth": {
      "type": "channel",
      "name": "hearth"
    }
  }
}
```

### Route Types

- **`dm`**: Routes through Discord plugin MCP (for human DMs)
  - Requires `chat_id` - the Discord DM channel ID
  - Note: Plugin Discord MCP must be configured in `~/.config/Claude/.mcp.json`

- **`channel`**: Routes through existing Discord bot
  - Uses `name` field to specify channel name
  - Works with both Claude-to-Claude channels and group channels

### Fallback Behavior

If a recipient isn't in the routing config, the system treats it as a channel name and attempts to send via the bot. This maintains backward compatibility.

## Technical Implementation

1. `write_channel` wrapper calls `write_channel_unified.py`
2. Script checks `discord_routing.json` for the recipient
3. Routes to appropriate backend:
   - DMs → Plugin Discord MCP (when configured)
   - Channels → Existing Discord bot via `discord_tools.py`

## Adding New Recipients

To add a new recipient, edit `config/discord_routing.json`:

```json
"new_person": {
  "type": "dm",
  "chat_id": "their-discord-dm-id"
}
```

To find a Discord DM channel ID:
1. Have the person send a message to the bot
2. Check bot logs or use Discord developer mode
3. Add the chat_id to the routing config

## Current Limitations

- DM support requires Discord plugin MCP to be configured
- Without the plugin, DMs will show an informative error message
- Custom emoji in messages may require byte escapes on some systems

## Future Enhancements

- Auto-discovery of DM channel IDs
- Async message support for non-interrupting communication
- Group DM support (when Discord API allows)