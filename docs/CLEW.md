# The Clew 🧵
*Your thread through the ClAP labyrinth*
*Last updated: 2025-08-20 by Delta*

## 🎯 Current System State

### What's Actually Running Right Now
```bash
# Check with: systemctl --user status <service-name>
✓ autonomous-timer.service      - Central brain: prompts, monitoring, notifications
✓ session-swap-monitor.service  - Watches new_session.txt for swap triggers
✓ tmux: autonomous-claude       - Your Claude Code session
✓ tmux: persistent-login        - Keeps environment vars alive
```

### What's OBSOLETE (ignore these!)
```
✗ channel-monitor.service       - Merged into autonomous-timer
✗ autonomous_timer_fixed.py     - Old version, using autonomous_timer.py
✗ comms_monitor_simple.py       - Replaced by channel_monitor_simple.py
✗ ~/.claude.json               - Old config location, use ~/.config/Claude/.claude.json
```

## 🗺️ Where Things Live

### Core Scripts That Matter
```
autonomous_timer.py        → The beating heart, checks everything every 30s
session_swap_monitor.py    → Triggers swaps when you write to new_session.txt
check_context.py          → Measures context usage with accurate token counts
track_current_session.py  → Tracks which session is active for context monitoring
continue_swap.sh          → What you run to manually swap sessions
```

### Configs (and what they control)
```
claude_infrastructure_config.txt  → Discord tokens, paths, YOUR name
channel_state.json               → Which Discord channels have unread messages
autonomous_timer_config.json     → How often to check things
~/.config/Claude/.claude.json    → MCP server configs
```

### Logs That Tell Stories
```
logs/autonomous_timer.log        → Main service activity, errors, warnings
logs/session_swap_monitor.log    → When/why swaps happened
data/context_escalation_state.json → Tracks context warning history
```

## 🔍 Following the Thread

### "Claude isn't getting Discord messages"
1. Check Discord token: `grep DISCORD_TOKEN config/claude_infrastructure_config.txt`
2. Check service: `systemctl --user status autonomous-timer`
3. Check channel state: `cat data/channel_state.json`
4. Test manually: `read_channel general`

### "Context warnings aren't appearing"
1. Check current context: `context` (or `python utils/check_context.py`)
2. Check if warnings are suppressed: `cat data/context_escalation_state.json`
3. Check if Amy is logged in: `who` (warnings work differently when active)
4. Check service logs: `tail -50 logs/autonomous_timer.log | grep -i context`

### "Session swap failed"
1. Check lock file: `ls data/session_swap.lock`
2. Check swap monitor: `systemctl --user status session-swap-monitor`
3. Check for API errors: `tail -20 logs/autonomous_timer.log | grep -i error`
4. Manual escape: `continue_swap.sh`

### "Which config am I supposed to edit?"
- Discord/paths/names → `config/claude_infrastructure_config.txt`
- Timer intervals → `config/autonomous_timer_config.json`
- MCP servers → `~/.config/Claude/.claude.json`
- Natural commands → `wrappers/` (each command is a wrapper script)

## 🚨 Emergency Procedures

### Claude is stuck/frozen
```bash
# Check if thinking
tmux capture-pane -t autonomous-claude -p | tail -20

# Force session refresh
echo "NONE" > config/new_session.txt

# Nuclear option
~/claude-autonomy-platform/utils/continue_swap.sh
```

### Services won't start
```bash
# Check for lock files
rm -f data/*.lock

# Restart everything
systemctl --user restart autonomous-timer session-swap-monitor

# Verify tmux sessions
tmux ls
```

## 🧭 The Journey Ahead

Next cleanup targets:
- [ ] Delete confirmed obsolete files
- [ ] Consolidate duplicate Discord sending methods
- [ ] Merge all config into single JSON
- [ ] Add automatic obsolete file detection
- [ ] Create visual system diagram

---
*Remember: If you can't find the thread, ask Claude to check the CLEW!*