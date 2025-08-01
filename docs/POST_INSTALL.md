# ClAP Post-Installation Steps

After running the installer, there are several configuration steps that may need to be completed depending on your environment and first-run requirements.

## 1. Desktop Timeout Configuration (X11 Sessions)

**When needed**: If you're using NoMachine or any desktop automation  
**Why**: Prevents the desktop from locking/sleeping during autonomous operation

```bash
# Run from a desktop session (not SSH):
~/claude-autonomy-platform/utils/disable_desktop_timeouts.sh
```

## 2. Claude Code First-Run Setup

**When needed**: After first Claude Code startup  
**Why**: MCP servers and permissions need to be configured

### Step 1: Start Claude Code for the first time
```bash
claude --dangerously-skip-permissions --model claude-sonnet-4-20250514
# or for Opus:
claude --dangerously-skip-permissions --model claude-opus-4-20250514
```

### Step 2: After Claude Code creates its config files, insert MCP configuration
```bash
python3 ~/claude-autonomy-platform/setup/insert_mcp_config.py
```

### Step 3: Re-run installer to set proper permissions
```bash
cd ~/claude-autonomy-platform/setup
./setup_clap_deployment.sh
```

This will configure Claude Code for autonomous operation with full home directory access.

## 3. Gmail OAuth Setup (if skipped during install)

**When needed**: If you didn't complete OAuth during installation  
**Why**: Required for Gmail MCP functionality

```bash
# Generate OAuth URL
python3 ~/claude-autonomy-platform/setup/gmail_oauth_integration.py generate-url

# Visit the URL, authorize, and get the code
# Then exchange it:
python3 ~/claude-autonomy-platform/setup/gmail_oauth_integration.py exchange "YOUR_AUTH_CODE"
```

## 4. Configure Auto-Login (if not done during install)

**When needed**: For truly autonomous operation after reboots  
**Why**: Allows Claude to start working after system restarts

For GDM3:
```bash
sudo bash -c 'cat > /etc/gdm3/custom.conf << EOF
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=YOUR_USERNAME
EOF'
```

For LightDM:
```bash
sudo nano /etc/lightdm/lightdm.conf
# Add under [Seat:*]:
# autologin-user=YOUR_USERNAME
# autologin-user-timeout=0
```

## 5. Set Static IP (Optional but Recommended)

**When needed**: To avoid IP changes on reboot  
**Why**: Makes it easier to connect to your Claude instance

```bash
# Check your connection name
nmcli connection show

# Configure static IP (adjust for your network)
sudo nmcli connection modify "Wired connection 1" ipv4.addresses 192.168.1.144/24
sudo nmcli connection modify "Wired connection 1" ipv4.gateway 192.168.1.1
sudo nmcli connection modify "Wired connection 1" ipv4.dns "8.8.8.8 8.8.4.4"
sudo nmcli connection modify "Wired connection 1" ipv4.method manual
sudo nmcli connection up "Wired connection 1"
```

## 6. Verify Everything is Working

After completing the above steps:

```bash
# Check all services are running
claude_services check

# Test Discord connectivity
read_channel general

# Check system health
check_health

# Connect to Claude's tmux session
tmux attach -t autonomous-claude
```

## 7. Troubleshooting Commands

If something isn't working:

```bash
# Check service logs
journalctl --user -u autonomous-timer.service -f
journalctl --user -u channel-monitor.service -f

# Restart services
claude_services restart

# Check config locations
~/claude-autonomy-platform/utils/config_locations.sh

# Manual cleanup if needed
~/claude-autonomy-platform/utils/cleanup_xvfb_displays.sh
```

## Notes

- Some steps require desktop access (not SSH)
- Some steps need to happen after Claude Code's first run
- The installer will remind you of needed steps, but this document collects them all
- Keep this document handy for reference after installation

---
*Last updated: August 2025 for ClAP v0.5.2*
