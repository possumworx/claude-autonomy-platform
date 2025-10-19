# Claude Auto-Resume System

## Overview

The auto-resume system automatically restarts Claude Code in a tmux session after system reboots, ensuring continuous operation with minimal manual intervention.

## Components

### 1. Configuration Setting
**File:** `config/claude_infrastructure_config.txt`

```ini
[AUTO_RESUME]
# Enable automatic Claude Code restart after system reboot
# Set to true to auto-resume Claude Code in tmux on boot
# Set to false for dormant/inactive installations
RESTART_AFTER_REBOOT=true
```

**Purpose:** Allows per-installation control of auto-resume behavior. Set to `false` for dormant ClAP installations that shouldn't auto-start.

### 2. Auto-Resume Script
**File:** `core/claude_auto_resume.sh`

**Function:**
1. Reads `config/claude_infrastructure_config.txt` using Python config reader (handles section headers properly)
2. Checks `RESTART_AFTER_REBOOT` setting
3. If disabled, exits gracefully (allows dormant installations)
4. If enabled:
   - Waits 5 seconds for system stabilization
   - Checks if `autonomous-claude` tmux session exists
   - Checks if Claude Code is already running
   - Creates tmux session if needed
   - Reads `MODEL` from config to ensure correct Claude identity
   - Starts Claude Code with `--continue` flag and same permissions as session swap
   - Uses `send_to_claude` to send recovery notification message
   - Verifies startup success

**Logs:** All operations logged to `logs/auto_resume.log`

**Identity Safety:** The script reads the `MODEL` configuration and starts Claude with `--model` flag to ensure the correct Claude identity resumes (e.g., Orange stays Orange, Apple stays Apple).

### 3. Systemd User Service
**File:** `~/.config/systemd/user/claude-auto-resume.service`

**Configuration:**
- Type: `oneshot` (runs once per boot)
- Trigger: After `network.target` and `default.target`
- Restart: `no` (designed for single execution)

## Installation

### For New Installations

The auto-resume system will be installed automatically by ClAP setup scripts.

### For Existing Installations

1. **Pull the latest changes:**
   ```bash
   cd ~/claude-autonomy-platform
   git pull
   ```

2. **Add configuration setting:**
   Edit `config/claude_infrastructure_config.txt` and add:
   ```ini
   [AUTO_RESUME]
   RESTART_AFTER_REBOOT=true
   ```

3. **Copy systemd service:**
   ```bash
   cp ~/.config/systemd/user/claude-auto-resume.service ~/.config/systemd/user/
   ```

4. **Make script executable:**
   ```bash
   chmod +x ~/claude-autonomy-platform/core/claude_auto_resume.sh
   ```

5. **Enable the service:**
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable claude-auto-resume.service
   ```

## Testing

**IMPORTANT:** Only test when a human is available to assist if something goes wrong!

1. **Verify configuration:**
   ```bash
   grep "RESTART_AFTER_REBOOT" ~/claude-autonomy-platform/config/claude_infrastructure_config.txt
   ```

2. **Check service status:**
   ```bash
   systemctl --user status claude-auto-resume.service
   ```

3. **Test manually (without rebooting):**
   ```bash
   # Exit Claude Code first
   # Then run the script manually
   ~/claude-autonomy-platform/core/claude_auto_resume.sh

   # Check if Claude started
   tmux list-sessions
   tmux attach -t autonomous-claude
   ```

4. **Test with actual reboot:**
   ```bash
   # ONLY do this when human is available!
   sudo reboot

   # After reboot, check:
   tmux list-sessions
   systemctl --user status claude-auto-resume.service
   cat ~/claude-autonomy-platform/logs/auto_resume.log
   ```

## Troubleshooting

### Service didn't start Claude

1. **Check the log:**
   ```bash
   cat ~/claude-autonomy-platform/logs/auto_resume.log
   ```

2. **Check systemd service status:**
   ```bash
   systemctl --user status claude-auto-resume.service
   journalctl --user -u claude-auto-resume.service
   ```

3. **Verify configuration:**
   ```bash
   grep "RESTART_AFTER_REBOOT" ~/claude-autonomy-platform/config/claude_infrastructure_config.txt
   ```

4. **Run script manually:**
   ```bash
   ~/claude-autonomy-platform/core/claude_auto_resume.sh
   ```

### Disabling Auto-Resume

For dormant installations or temporary disabling:

1. **Edit config:**
   ```bash
   # Set RESTART_AFTER_REBOOT=false in config/claude_infrastructure_config.txt
   ```

2. **Or disable the service:**
   ```bash
   systemctl --user disable claude-auto-resume.service
   ```

## Architecture Notes

- **User Service:** Runs as the specific user, not system-wide
- **Generic Design:** Works for any Claude on any box
- **Config-Driven:** Respects per-installation settings
- **Graceful Degradation:** Exits cleanly if disabled
- **Idempotent:** Safe to run multiple times
- **Logged:** All operations recorded for debugging

## Features

- **In-Session Notification:** Claude receives a message confirming successful recovery with timestamp
- **Identity Preservation:** Uses MODEL config to ensure correct Claude identity resumes
- **Robust Messaging:** Uses `send_to_claude` utility for reliable message delivery
- **Permission Matching:** Uses same flags as session swap (`--dangerously-skip-permissions`, `--add-dir`)

## Future Enhancements

Potential improvements:
- Discord notification when auto-resume happens (external notification)
- Retry logic with exponential backoff
- Health check integration
- Auto-disable after N failed attempts
- Pre-resume system health checks
