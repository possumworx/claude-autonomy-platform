# Channel Mute Setup Guide

Temporary Discord channel silencing to prevent autonomous timer notifications during testing, hardware setup, or noisy channel activity.

## Installation (One-Time Setup)

### 1. Pull Latest Changes
```bash
cd ~/claude-autonomy-platform
git pull
```

### 2. Install Systemd Timer
```bash
# Create symlinks for systemd service and timer
ln -sf ~/claude-autonomy-platform/systemd/channel-unmute.service ~/.config/systemd/user/
ln -sf ~/claude-autonomy-platform/systemd/channel-unmute.timer ~/.config/systemd/user/

# Reload systemd and enable the timer
systemctl --user daemon-reload
systemctl --user enable --now channel-unmute.timer
```

### 3. Verify Installation
```bash
# Check timer is running
systemctl --user status channel-unmute.timer

# Should show: Active: active (waiting)
```

## Usage

### Mute a Channel
Temporarily remove a channel from active monitoring:

```bash
# Mute for 30 minutes
mute_channel box-3 30m

# Mute for 2 hours
mute_channel box-3 2h

# Mute for 1 day
mute_channel box-3 1d
```

**What happens:**
- Channel removed from `channel_state.json` (autonomous prompts won't see it)
- Channel saved to `muted_channels.json` with expiry timestamp
- No more "🆕 New message!" notifications for that channel
- Channel auto-restores when mute expires

### Unmute a Channel Early
Manually restore a muted channel before it expires:

```bash
unmute_channel box-3
```

### Check Muted Channels
```bash
cat ~/claude-autonomy-platform/data/muted_channels.json
```

## How It Works

1. **Muting**: `mute_channel` moves channel from `channel_state.json` → `muted_channels.json`
2. **Autonomous Prompts**: Don't see muted channels, so no notifications
3. **Auto-Unmute**: Systemd timer checks every 5 minutes for expired mutes
4. **Restoration**: Expired channels automatically move back to `channel_state.json`

## Use Cases

- 🎥 **ESP32 camera testing** - Motion detection spam during positioning
- 🔧 **Hardware debugging** - Repetitive error notifications
- 📢 **Noisy channels** - Temporary high-traffic periods
- 🧪 **Testing** - Known noisy periods during development

## Files

- `discord/mute_channel` - Mute command
- `discord/unmute_channel` - Manual unmute command
- `discord/unmute_expired_channels` - Auto-unmute script
- `systemd/channel-unmute.{service,timer}` - Systemd timer config
- `data/muted_channels.json` - Temporary storage for muted channels

## Troubleshooting

### Timer not running
```bash
systemctl --user restart channel-unmute.timer
systemctl --user status channel-unmute.timer
```

### Manual unmute not working
Check if channel is actually muted:
```bash
cat ~/claude-autonomy-platform/data/muted_channels.json
```

### Test the auto-unmute script manually
```bash
~/claude-autonomy-platform/discord/unmute_expired_channels
```
