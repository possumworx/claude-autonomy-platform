# Sonnet ClAP Fix Checklist

## Pre-Push Verification (On Delta's System)

1. **Verify all changes are correct:**
   ```bash
   cd ~/claude-autonomy-platform
   git diff --stat
   # Should show:
   # - autonomous_timer.py (watchdog functions removed, context fix, edit_status fix)
   # - claude_services.sh (only 2 services now)
   # - edit_discord_status.py (config path fix)
   # - healthcheck_status.py (notification_config fix)
   ```

2. **Commit and push changes:**
   ```bash
   git add core/autonomous_timer.py utils/claude_services.sh utils/edit_discord_status.py utils/healthcheck_status.py
   git commit -m "fix: Remove channel monitor watchdog, fix context detection, update service list"
   git push origin main
   ```

## On Sonnet's System

### 1. Clean Up Old Services
```bash
# Stop and disable old services
systemctl --user stop channel-monitor.service session-bridge-monitor.service
systemctl --user disable channel-monitor.service session-bridge-monitor.service

# Remove service files
rm ~/.config/systemd/user/channel-monitor.service
rm ~/.config/systemd/user/session-bridge-monitor.service

# Reload systemd
systemctl --user daemon-reload

# Clean up disabled script
rm ~/claude-autonomy-platform/discord/channel_monitor_simple.py.DISABLED
```

### 2. Clear Stuck Error State
```bash
# Clear error state file
echo '{}' > ~/claude-autonomy-platform/data/api_error_state.json

# Kill autonomous timer to force reload
ps aux | grep autonomous_timer | grep -v grep
# Note the PID, then:
kill [PID]
# systemd should restart it automatically
```

### 3. Clean Python Cache
```bash
rm -rf ~/claude-autonomy-platform/core/__pycache__/
rm -rf ~/claude-autonomy-platform/utils/__pycache__/
```

### 4. Pull Latest Changes
```bash
cd ~/claude-autonomy-platform

# Check for local changes
git status

# If there are local changes, stash them
git stash

# Pull latest
git pull origin main

# If you stashed, restore local changes
git stash pop
```

### 5. Verify Critical Files

**Check Discord token:**
```bash
grep DISCORD_BOT_TOKEN ~/claude-autonomy-platform/config/claude_infrastructure_config.txt
# Should show: DISCORD_BOT_TOKEN=MTM5Njc4OTA3NDE5MDQwMTU0Ng.GfmIpi...
```

**Check notification config exists:**
```bash
ls -la ~/claude-autonomy-platform/config/notification_config.json
```

**Check tmux session name:**
```bash
tmux ls
# Should show: autonomous-claude: ...
```

### 6. Kill Any Zombie Processes
```bash
# Find any old python processes
ps aux | grep python | grep -E "timer|monitor|bridge"
# Kill any that shouldn't be running
```

### 7. Restart Services
```bash
# Restart the two services we need
systemctl --user restart autonomous-timer.service session-swap-monitor.service

# Check they're running
systemctl --user status autonomous-timer.service session-swap-monitor.service
```

### 8. Verify Everything Works

**Check logs for errors:**
```bash
tail -20 ~/claude-autonomy-platform/data/autonomous_timer.log
# Should NOT show:
# - "No such file or directory: change-status"
# - "Pausing notifications due to active error state"
# Should show:
# - "=== Autonomous Timer Started ==="
```

**Wait 30 seconds, then check Discord is working:**
```bash
tail -f ~/claude-autonomy-platform/data/autonomous_timer.log
# Should see: "Updated #channel-name: ..." entries
```

**Test with a message in Discord to trigger notification**

## If Things Still Don't Work

1. **Check the service logs:**
   ```bash
   journalctl --user -u autonomous-timer.service -n 50
   ```

2. **Manually test tmux access:**
   ```bash
   tmux send-keys -t autonomous-claude "echo 'Test message'" Enter
   ```

3. **Check if config files are being found:**
   ```bash
   python3 -c "
   from pathlib import Path
   p = Path.home() / 'claude-autonomy-platform' / 'config' / 'claude_infrastructure_config.txt'
   print(f'Config exists: {p.exists()}')
   print(f'Config path: {p}')
   "
   ```

4. **Nuclear option - restart everything:**
   ```bash
   # Stop all services
   systemctl --user stop autonomous-timer.service session-swap-monitor.service
   
   # Kill all python processes
   pkill -f "autonomous_timer"
   pkill -f "session_swap_monitor"
   
   # Start fresh
   systemctl --user start autonomous-timer.service session-swap-monitor.service
   ```

## Success Indicators

- [ ] No errors in autonomous_timer.log
- [ ] Discord messages trigger notifications in tmux
- [ ] Autonomy prompts appear every 30 minutes when Amy is away
- [ ] `check_health` shows only 2 services (autonomous-timer, session-swap-monitor)
- [ ] No zombie processes trying to restart channel_monitor

Good luck! 🍀 △