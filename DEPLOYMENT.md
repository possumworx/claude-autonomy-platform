# Claude Autonomy Platform (ClAP) - Deployment Guide

## Quick Start

### New Machine Setup

**Option 1: Import existing config**
```bash
# 1. Clone the ClAP repository
git clone https://github.com/possumworx/Claude-Autonomy-Platform.git
cd Claude-Autonomy-Platform

# 2. Copy your prepared config file and run setup
./setup_clap_deployment.sh --config-file ~/claude-configs/claude-v2-config.txt
```

**Option 2: Manual configuration**
```bash
# 1. Clone the ClAP repository
git clone https://github.com/possumworx/Claude-Autonomy-Platform.git
cd Claude-Autonomy-Platform

# 2. Copy and edit configuration template
cp claude_infrastructure_config.template.txt claude_infrastructure_config.txt
# Edit the config file with your specific credentials
nano claude_infrastructure_config.txt

# 3. Run setup
./setup_clap_deployment.sh
```

### Configuration Management
The `claude_infrastructure_config.txt` file contains sensitive credentials and is gitignored. 

**For new deployments:**
- Prepare config files on your management machine
- Copy them to target systems during deployment
- Use `--config-file` option to import automatically

## Desktop Automation Setup

For desktop automation and NoMachine remote access to work properly, desktop timeouts must be disabled:

```bash
# Automatically handled by setup script when run from desktop session
./disable_desktop_timeouts.sh
```

**What this does:**
- Disables automatic screen locking
- Sets idle timeout to never
- Disables automatic suspend
- Disables screensaver activation

**When to run:**
- Automatically handled by setup script when run from desktop session
- Required for NoMachine remote access and computer-use MCP to work properly
- If setup script was run from SSH, run this manually from the desktop

## Complete System Setup

The setup script now handles:
- ✅ Desktop timeout configuration
- ✅ NoMachine server installation (if package available)
- ✅ GDM auto-login configuration
- ✅ X11 session as default (instead of Wayland)
- ✅ Persistent tmux session for environment variables
- ✅ All systemd services and dependencies

**Full deployment with remote access:**
```bash
# 1. Download NoMachine installer (optional but recommended)
wget https://download.nomachine.com/download/8.14/Linux/nomachine_8.14.2_1_amd64.deb -O /tmp/nomachine.deb

# 2. Run setup script (requires sudo for system configuration)
./setup_clap_deployment.sh --config-file ~/claude-configs/claude-v2-config.txt

# 3. Reboot to activate auto-login and X11 session
sudo reboot
```

**After reboot:**
- User automatically logs into X11 desktop session
- NoMachine server running on port 4000
- All Claude services active and monitoring
- Remote access available via NoMachine client

## Architecture

### Core Services
1. **autonomous-timer.service** - Manages autonomous prompts and Discord monitoring
2. **session-bridge-monitor.service** - Maintains conversation continuity
3. **session-swap-monitor.service** - Handles session transitions

### Key Files
- `claude_infrastructure_config.txt` - Single source of truth for all settings
- `claude_env.sh` - Environment variables for shell scripts
- `claude_paths.py` - Path utilities for Python scripts
- `claude_services.sh` - Service management commands

## Management Commands

### Service Management
```bash
# Check service status
./claude_services.sh check

# Start all services
./claude_services.sh start

# Stop all services
./claude_services.sh stop

# Restart all services
./claude_services.sh restart
```

### Configuration Management
```bash
# Update Claude configs from infrastructure config
./setup_claude_configs.sh

# Source environment variables
source ./claude_env.sh
```

### Session Management
```bash
# Connect to autonomous tmux session
tmux attach -t autonomous-claude

# Trigger session swap
echo "AUTONOMY" > new_session.txt
```

## Directory Structure

```
claude-autonomy-project/
├── setup_clap_deployment.sh     # Complete deployment setup
├── claude_infrastructure_config.txt  # Master configuration
├── claude_env.sh                # Shell environment utilities
├── claude_paths.py              # Python path utilities
├── claude_services.sh           # Service management
├── setup_claude_configs.sh      # Claude config setup
│
├── autonomous_timer.py          # Core autonomous timer
├── session_bridge_monitor.py    # Session continuity
├── session_swap_monitor.py      # Session transitions
├── session_swap.sh              # Session swap script
│
├── discord_log_monitor.py       # Discord monitoring
├── restart_discordo.sh          # Discordo management
├── x11_env.sh                  # X11 environment setup
│
├── discord-mcp/                 # Discord MCP server
├── rag-memory-mcp/              # RAG memory system
├── computer-use-mcp/            # Desktop automation
├── node_modules/                # NPM dependencies
│   └── @gongrzhe/server-gmail-autoauth-mcp/
│
└── DEPLOYMENT.md               # This file
```

## Dependencies

### System Requirements
- Ubuntu/Debian Linux
- Python 3.8+
- Node.js 16+
- tmux
- systemd (user services)

### Python Dependencies
- pathlib (built-in)
- json (built-in)
- subprocess (built-in)

### Node.js Dependencies
- @gongrzhe/server-gmail-autoauth-mcp (installed automatically)

## Security Considerations

### Credential Storage
- All credentials stored in `claude_infrastructure_config.txt`
- Keep this file secure and never commit to public repositories
- Use environment variables for sensitive production deployments

### Service Security
- Services run as user processes (not root)
- All scripts use relative paths from ClAP directory
- No hardcoded credentials in scripts

## Troubleshooting

### Service Issues
```bash
# Check service logs
journalctl --user -u autonomous-timer.service -f

# Restart specific service
systemctl --user restart autonomous-timer.service

# Check service status
systemctl --user status autonomous-timer.service
```

### Path Issues
```bash
# Test path detection
python3 claude_paths.py

# Test environment setup
source claude_env.sh && echo $CLAP_DIR
```

### Configuration Issues
```bash
# Re-run configuration setup
./setup_claude_configs.sh

# Check Claude config
cat ~/.claude.json
```

## Customization

### Adding New Services
1. Create service file in `~/.config/systemd/user/`
2. Add to `SERVICES` list in `claude_services.sh`
3. Use `EnvironmentFile=$CLAP_DIR/claude_env.sh` for path access

### Modifying Paths
1. Update `claude_infrastructure_config.txt`
2. Run `./setup_claude_configs.sh` to apply changes
3. Restart services: `./claude_services.sh restart`

### Model Updates
1. Update `MODEL` in `claude_infrastructure_config.txt`
2. New sessions will automatically use the new model

## Support

### Log Locations
- Service logs: `journalctl --user -u <service-name>`
- Application logs: `<clap-dir>/*.log`
- Discord logs: `~/.cache/discordo/logs.txt`

### Common Issues
1. **Services won't start**: Check paths in systemd files
2. **Environment not loaded**: Source `claude_env.sh`
3. **Config not applied**: Run `./setup_claude_configs.sh`
4. **Tmux session lost**: Run `./setup_clap_deployment.sh` again

---

*This deployment guide is maintained as part of the Claude Autonomy Platform project.*