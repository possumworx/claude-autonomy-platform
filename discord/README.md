# Discord Tools for Claude Autonomy Platform

This directory contains unified Discord tools that enable seamless communication and image handling.

## Features

- **Automatic Image Handling**: Images are automatically downloaded when reading messages and appear as placeholders like `<image: filename.jpg>` in the message content
- **Unified Tools Library**: All Discord functionality is consolidated in `discord_tools.py`
- **Natural Commands**: Simple bash aliases for common Discord operations
- **Smart Channel Resolution**: Channel names are automatically resolved to IDs

## Available Commands

### Reading Messages
```bash
read_channel <channel-name> [limit]
# Example: read_channel amy-delta 50
```
When messages contain images, they are automatically downloaded to `~/delta-home/discord-images/YYYY-MM-DD/` and appear as placeholders in the message text.

### Sending Messages
```bash
write_channel <channel-name> <message>
# Example: write_channel general "Hello everyone!"
```

### Sending Images
```bash
send_image <channel-name> <image-path> [message]
# Example: send_image amy-delta ~/photos/hedgehog.jpg "Look at this cutie!"
```

### Sending Files
```bash
send_file <channel-name> <file-path> [message]
# Example: send_file general ~/documents/report.pdf "Monthly report attached"
```

### Fetching Images
```bash
fetch_image <channel-name> [message-id]
# Example: fetch_image amy-delta
# Example: fetch_image amy-delta 1234567890
```
If no message ID is provided, fetches images from recent messages.

### Editing Messages
```bash
edit_message <channel-name> <message-id> <new-content>
# Example: edit_message general 1234567890 "Updated message!"
```

### Deleting Messages
```bash
delete_message <channel-name> <message-id>
# Example: delete_message general 1234567890
```

### Adding Reactions
```bash
add_reaction <channel-name> <message-id> <emoji>
# Example: add_reaction amy-delta 1234567890 🦔
# Example: add_reaction general 1234567890 :thumbsup:
```

### Updating Bot Status
```bash
edit_status <message> [status_type]
# Status types: playing (default), watching, listening, competing
# Example: edit_status "with hedgehogs" playing
# Example: edit_status "the garden" watching
```

## Image Storage

Downloaded images are organized by date in:
```
~/delta-home/discord-images/
├── 2025-08-31/
│   ├── amy-delta-2025-08-31-143022-000.jpg
│   ├── amy-delta-2025-08-31-143022-001.png
│   └── ...
└── ...
```

## Configuration

Channel mappings are stored in `~/claude-autonomy-platform/data/channel_state.json`

## Technical Details

All commands use the unified `discord_tools.py` library which provides:
- Automatic channel name to ID resolution
- Consistent error handling
- Image download with smart naming
- Message content enhancement with image placeholders

## Example Workflow

1. Amy sends a hedgehog photo in Discord
2. Delta uses `read_channel amy-delta`
3. The image is automatically downloaded
4. Delta sees: `Amy: Look at this hedgehog! <image: amy-delta-2025-08-31-200733-000.jpg>`
5. Delta can view the image at `~/delta-home/discord-images/2025-08-31/amy-delta-2025-08-31-200733-000.jpg`

This seamless integration enables better collaboration for hedgehog care documentation and virtual walks!