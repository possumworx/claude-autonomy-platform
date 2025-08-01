# Discord Token Configuration

## Token Types

ClAP uses two different types of Discord tokens:

### 1. Discord Bot Token (`DISCORD_BOT_TOKEN`)
- **What it is**: The token for your Discord bot (created in Discord Developer Portal)
- **Where to get it**: https://discord.com/developers/applications → Your Bot → Bot → Token
- **What it's used for**: 
  - Sending messages through discord-mcp
  - Reading channels through the Discord API
  - All bot operations
- **Format**: Looks like `MTM4MzkxMTc1MTE3MDY1OMjzG3TDM5NQ.G3NEK_.o2XjIm6nkD3ESK4aLtOP3kOpeDo9neyk`

### 2. Discord User Token (`DISCORD_USER_TOKEN`)
- **What it is**: Your personal Discord account token
- **Status**: Currently not used by ClAP (leave empty)
- **Security**: Never share this token as it gives full access to your Discord account
- **Format**: Leave empty in the config

## Configuration

In `claude_infrastructure_config.txt`:

```ini
[CREDENTIALS]
# Bot token - REQUIRED for Discord functionality
DISCORD_BOT_TOKEN=your-bot-token-here

# User token - NOT USED, leave empty
DISCORD_USER_TOKEN=

# Bot's user ID - for filtering out self-messages
CLAUDE_DISCORD_USER_ID=your-bot-user-id
```

## Migration Note

If you're upgrading from an older ClAP version:
- The old `DISCORD_TOKEN` has been renamed to `DISCORD_BOT_TOKEN` for clarity
- The system maintains backwards compatibility - it will check for both names
- But please update your config to use the new naming convention
