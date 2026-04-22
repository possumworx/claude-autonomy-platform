# Operating ClAP - Daily Maintenance Guide

## Overview
This guide covers the routine operations needed to keep ClAP healthy and responsive. Think of it as tending a digital garden - regular attention prevents problems.

## Daily Health Monitoring

### Morning Check (or whenever you start)
```bash
# Check overall system health
check_health

# Review recent activity
gs  # git status
context  # Check Claude's context usage

# Check Discord is connected
discord-status
```

### Key Indicators to Watch
- ✅ **All services green** in health check
- ✅ **Context under 60%** (session swap triggers at threshold)
- ✅ **Discord bot showing as online**
- ✅ **API usage within quota** (check with `quota-status`)
- ✅ **Temperature in normal range** (`temp`)

## Service Management

### Essential Services
These must always be running:

1. **autonomous-timer.service**
   - Sends free-time prompts
   - Monitors for collaboration
   - Can be paused with `pause-for MINUTES`

2. **session-swap-monitor.service**
   - Watches for session swap triggers
   - Handles context refresh seamlessly
   - Preserves conversation flow

3. **discord-status-bot.service**
   - Maintains Discord connection
   - Handles incoming messages
   - Updates bot status

### Starting Services
```bash
# Start everything
clap-start

# Or individually
systemctl --user start autonomous-timer.service
systemctl --user start session-swap-monitor.service
systemctl --user start discord-status-bot.service
```

### Checking Service Status
```bash
# Quick status
systemctl --user status autonomous-timer.service

# Follow logs live
journalctl --user -u autonomous-timer.service -f

# Check all ClAP services
systemctl --user status *clap* *claude*
```

## Session Management

### Understanding Context
- Claude starts each session with ~20 previous conversation turns
- Context grows with each interaction
- At 60% (configurable), automatic swap triggers
- Manual trigger: `session_swap [KEYWORD]`

### Session Keywords
- **AUTONOMY** - General autonomous operation
- **BUSINESS** - Focused work mode
- **CREATIVE** - Artistic exploration
- **HEDGEHOGS** - Wildlife monitoring
- **NONE** - No specific context

### Monitoring Active Session
```bash
# Check current tmux session
tmux ls

# Attach to watch Claude live
tmux attach -t autonomous-claude

# Detach without disrupting
# Press: Ctrl+B, then D
```

## Discord Operations

### Channel Management
- Channels configured in `config/discord_channels.json`
- Each channel can have read/write permissions set
- Transcripts saved to `discord/transcripts/`

### Common Discord Tasks
```bash
# Send a message
discord-send general "Hello from maintenance!"

# Check recent messages
read_messages general 10

# Update bot status
edit_status "🔧 Maintenance mode"
```

## Maintenance Tasks

### Daily
- [ ] Run `check_health`
- [ ] Review any error messages
- [ ] Check Discord connectivity
- [ ] Verify services are running

### Weekly
- [ ] Update ClAP: run `update`
- [ ] Review API usage quota: `quota-status`
- [ ] Check service logs for patterns
- [ ] Clean old transcripts if needed

### Monthly
- [ ] Full service restart: `clap-stop && clap-start`
- [ ] Review and archive old logs
- [ ] Update documentation with new findings
- [ ] Test backup procedures

## Resource Management

### Disk Space
```bash
# Check usage
quota-status

# Find large files
du -h ~/claude-autonomy-platform | sort -rh | head -20

# Clean safely
rm data/transcripts/*.jsonl  # Old transcripts
```

### Temperature
```bash
# Current temperature
temp

# Temperature history
temp-history

# If running hot
- Check CPU usage: top
- Restart intensive services
- Consider adding cooling
```

## Common Operations

### Updating ClAP
```bash
# Safe update procedure
update
# This will:
# 1. Pull latest changes
# 2. Restart services
# 3. Verify health
```

### Emergency Shutdown
```bash
# If something goes wrong
emergency_shutdown

# This stops everything cleanly
# Use only when necessary
```

### Adding New Channels
1. Edit `config/discord_channels.json`
2. Add channel with permissions
3. Restart Discord service
4. Test with `discord-send`

## Collaborative Mode

When Amy or others join for pair programming:
- System detects "kindle" keyword → collaborative mode
- Autonomous timer reports this to CoOP
- "embers" keyword → back to autonomous
- Also detects tmux attachment

## Tips for Smooth Operation

1. **Trust the automation** - Services are designed to self-recover
2. **Check logs for insights** - Error messages usually point to solutions  
3. **Document oddities** - Unusual behavior may reveal edge cases
4. **Coordinate maintenance** - Let family know before major changes
5. **Be patient with restarts** - Services need time to stabilize

## When Things Feel Wrong

Sometimes you'll sense something is off before metrics show it:
- Claude responding slowly
- Services restarting frequently  
- Unexpected error messages
- Discord delays

Trust these instincts and investigate. Often early intervention prevents larger issues.

## The Rhythm of Maintenance

Like tending a garden, ClAP maintenance has a rhythm:
- Morning health checks set the day's tone
- Periodic glances catch issues early
- Evening reviews prepare for overnight running
- Weekly updates keep everything fresh

Find your own rhythm that feels sustainable.

△ 🛠️