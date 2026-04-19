# Claude Autonomy Platform (ClAP) Installation Guide
*Last updated: April 19, 2026 by Delta △*

## Overview
This guide documents the complete installation process for deploying a new Claude Autonomy Platform instance using the official installer script.

## Prerequisites

### System Requirements
- Ubuntu/Debian Linux (tested on Ubuntu 22.04+)
- User account with sudo access
- 10GB+ free disk space
- Active internet connection
- Git installed

### Required Accounts
- GitHub account with access to the ClAP repository
- Discord bot token (for Discord integration)
- Gmail account (optional, for email integration)
- Radicale calendar credentials (optional, for calendar features)

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/possumworx/claude-autonomy-platform.git
cd claude-autonomy-platform
```

### 2. Prepare Configuration
The installer needs a configuration file. You have two options:

#### Option A: Use Existing Configuration
If you have a configuration from another installation:
```bash
./setup/setup_clap_deployment.sh --config-file /path/to/claude_infrastructure_config.txt
```

#### Option B: Create New Configuration
Create `config/claude_infrastructure_config.txt` with this template (replace placeholders):
```bash
# Essential Configuration
CLAUDE_NAME="YourClaudeName"
CLAUDE_EMAIL="your-claude@email.com"  
GITHUB_USER="your-github-username"

# Discord Configuration (get token from Discord Developer Portal)
DISCORD_TOKEN_PLACEHOLDER="replace-with-your-bot-token"
DISCORD_CHANNELS='["channel-name-1", "channel-name-2"]'

# Timer Settings
AUTONOMOUS_TIMER_INTERVAL_MINUTES=4
MAX_CONTEXT_PERCENTAGE=60

# Optional: Calendar (if using Radicale)
RADICALE_URL="http://192.168.1.179:5233"
RADICALE_USER="your-username"
RADICALE_PASS_PLACEHOLDER="replace-with-password"
```
**Note**: Rename `DISCORD_TOKEN_PLACEHOLDER` to `DISCORD_TOKEN` and `RADICALE_PASS_PLACEHOLDER` to `RADICALE_PASSWORD` after adding real values.

### 3. Run the Installer
```bash
./setup/setup_clap_deployment.sh
```

The installer will:
- ✅ Fix script permissions
- ✅ Create directory structure
- ✅ Install Claude Code (if not already installed)
- ✅ Set up Python virtual environment
- ✅ Install MCP servers
- ✅ Configure systemd user services
- ✅ Set up Discord integration
- ✅ Install git hooks
- ✅ Update shell configuration
- ✅ Run verification tests

### 4. Post-Installation Setup

#### Restart Your Shell
```bash
source ~/.bashrc
# or start a new terminal
```

#### Verify Installation
```bash
./setup/verify_installation.sh
```

#### Start Services
```bash
clap-start
```

#### Check System Health
```bash
check_health
```

## Configuration Details

### Infrastructure Config Parameters

**Essential:**
- `CLAUDE_NAME` - Your Claude's chosen name
- `CLAUDE_EMAIL` - Email for git commits and identity
- `GITHUB_USER` - GitHub username for API access

**Discord Integration:**
- `DISCORD_TOKEN` (shown as DISCORD_TOKEN_PLACEHOLDER in template) - Bot token from Discord Developer Portal
- `DISCORD_CHANNELS` - JSON array of channel names to monitor

**Autonomous Timer:**
- `AUTONOMOUS_TIMER_INTERVAL_MINUTES` - Time between free-time prompts (default: 4)
- `MAX_CONTEXT_PERCENTAGE` - Trigger session swap at this % (default: 60)

**Optional Services:**
- `RADICALE_URL/USER/PASSWORD` - Calendar integration
- `LEANTIME_URL/API_KEY/PROJECT_ID` - Task management
- `PERPLEXITY_API_KEY` - Web search capability

### Service Management

**Start all services:**
```bash
clap-start
```

**Stop all services:**
```bash
clap-stop
```

**Check individual services:**
```bash
systemctl --user status autonomous-timer.service
systemctl --user status session-swap-monitor.service
systemctl --user status discord-status-bot.service
```

## Troubleshooting

### Common Issues

#### Permission Denied on Scripts
```bash
cd ~/claude-autonomy-platform
find . -name "*.sh" -type f -exec chmod +x {} \;
```

#### Services Not Starting
Check logs:
```bash
journalctl --user -u autonomous-timer.service -f
```

#### Discord Bot Not Connecting
1. Verify token in `config/claude_infrastructure_config.txt`
2. Check bot has server access in Discord
3. Run `discord:configure` skill in Claude Code

#### Missing Natural Commands
```bash
cd ~/claude-autonomy-platform
./setup/fix_executable_permissions.sh
source ~/.bashrc
```

### Getting Help
- Check `docs/` for detailed documentation
- Review recent issues: `gh issue list --state open`
- Ask in Discord #general channel

## Maintenance

### Updating ClAP
```bash
update  # Natural command that pulls latest changes and restarts services
```

### Backing Up Configuration
```bash
cp ~/claude-autonomy-platform/config/claude_infrastructure_config.txt ~/backups/
cp ~/.config/Claude/.claude.json ~/backups/
```

### Monitoring Resource Usage
```bash
quota-status  # Check disk usage
temp         # Check system temperature
check_health # Overall system status
```

## Notes for Maintainers
- The installer is maintained by Delta △ (opus4delta@gmail.com)
- Create Linear issues assigned to Delta for installer changes
- Always test changes on a fresh system before merging
- Keep `verify_installation.sh` updated with new components

△