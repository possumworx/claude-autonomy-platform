# Discord Integration

## Architecture

A unified tools library (`discord_tools.py`) powers simple CLI wrappers for all Discord operations. Background services maintain persistent connections and local transcripts.

## Core Modules

- **`discord_tools.py`** — Main library. `DiscordTools` class handles all API operations: sending/reading messages, file uploads, reactions, image downloads. Auto-resolves channel names to IDs via `data/discord_channels.json`.
- **`discord_utils.py`** — Lightweight singleton client for services that need minimal dependencies. Works with channel IDs directly.
- **`channel_state.py`** — Thread-safe state management for channel tracking (IDs, read position). Handles concurrent access with reload-merge on save.
- **`discord_transcript_fetcher.py`** — Background service (30s polling). Builds local JSON Lines transcripts at `data/transcripts/{channel}.jsonl`. Downloads images automatically.
- **`claude_status_bot.py`** — Persistent Discord.py WebSocket bot. Watches `data/bot_status_request.json` for status change requests.

## CLI Entry Points

All are thin wrappers around `discord_tools.py`:

| Command | Purpose |
|---------|---------|
| `write_channel` | Send message to named channel |
| `read_channel` | Live-fetch recent messages from Discord API |
| `read_messages` | Read from local transcript files (no API call) |
| `send_image` | Upload image with optional message |
| `send_file` | Upload any file type |
| `edit_message` | Modify an existing message |
| `delete_message` | Remove a message |
| `add_reaction` | Add emoji reaction |
| `edit_status` | Update Discord bot status/presence |
| `fetch_image` | Download specific images from channel |
| `mute_channel` | Temporarily suppress channel from monitoring |
| `unmute_channel` | Restore a muted channel |

## Dual Read Pattern

- **`read_channel`** — Hits Discord API directly. Returns live messages with auto-downloaded images. Updates read position.
- **`read_messages`** — Reads from local transcript files built by the fetcher. No API call. Shows channel purpose from `config/channel_purposes.json`.

Use `read_messages` for normal operation (fast, no API cost). Use `read_channel` when you need guaranteed-fresh data.

## Data Flow

```
Discord API → discord_tools.py → transcript_fetcher.py → data/transcripts/*.jsonl → read_messages
                    ↑
              read_channel (live)    write_channel / send_image / etc. (direct API)
```

## Configuration

- **Token**: Loaded from `config/claude_infrastructure_config.txt` via `infrastructure_config_reader.py`
- **Channel state**: `data/discord_channels.json` — name-to-ID mapping, read positions
- **Channel purposes**: `config/channel_purposes.json` — display metadata
- **Bot status queue**: `data/bot_status_request.json` — consumed by `claude_status_bot.py`
- **Muted channels**: `data/muted_channels.json` — temporary mutes with expiry timestamps

## Notes

- `write_channel_v2` exists but is functionally identical to `write_channel` — likely a migration artifact.
- Images download to `~/{PERSONAL_REPO}/discord-images/YYYY-MM-DD/` with auto-generated filenames.
- The fetcher only creates transcript files when new messages arrive in a channel.
- Emoji in `write_channel` may need byte escapes on some systems: `$'\xf0\x9f\x8c\x99'`
