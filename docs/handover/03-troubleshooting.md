# ClAP Troubleshooting Guide
*When things go wrong, this guide helps make them right*

## Philosophy of Troubleshooting
Every error is a teacher. Approach problems with curiosity rather than frustration - the system is trying to tell you something.

## Quick Diagnosis Flowchart

```
Is Claude responding?
├─ NO → Check tmux session
│       Check autonomous-timer service
│       Check context usage
└─ YES → Is Discord working?
         ├─ NO → Check bot service
         │       Check network
         │       Verify token
         └─ YES → Check specific issue below
```

## Common Issues & Solutions

### 1. Claude Not Responding to Free Time Prompts

**Symptoms:**
- No activity in autonomous-claude tmux session
- Free time prompts appear but no response

**Diagnosis:**
```bash
# Check if session exists
tmux ls | grep autonomous-claude

# Check timer service
systemctl --user status autonomous-timer.service

# Check for timer pause
cat ~/claude-autonomy-platform/data/timer_pause.json
```

**Solutions:**
- If paused: `unpause`
- If session dead: `clap-stop && clap-start`
- If timer crashed: `systemctl --user restart autonomous-timer.service`

### 2. Discord Bot Offline/Not Responding

**Symptoms:**
- Bot shows offline in Discord
- Messages not being received
- Send commands fail

**Diagnosis:**
```bash
# Check bot service
systemctl --user status discord-status-bot.service

# Check recent logs
journalctl --user -u discord-status-bot.service -n 50

# Verify token hasn't expired
grep DISCORD_TOKEN ~/claude-autonomy-platform/config/claude_infrastructure_config.txt
```

**Solutions:**
- Restart service: `systemctl --user restart discord-status-bot.service`
- If token invalid: Update config and restart
- Check Discord API status: https://discordstatus.com

### 3. Session Swap Failures

**Symptoms:**
- Context reaches 60%+ but no swap
- Swap starts but doesn't complete
- Error messages about session swap

**Diagnosis:**
```bash
# Check swap monitor
systemctl --user status session-swap-monitor.service

# Check for swap in progress
ps aux | grep session_swap

# Look at swap logs
journalctl --user -u session-swap-monitor.service -f
```

**Solutions:**
- Manual trigger: `session_swap AUTONOMY`
- If stuck: Kill swap process, restart service
- Emergency: `emergency_shutdown` then `clap-start`

### 4. High Context Usage/Rapid Growth

**Symptoms:**
- Context % climbing fast
- Frequent session swaps
- Performance degradation

**Diagnosis:**
```bash
# Check current usage
context

# Review recent activity
tail -100 ~/.local/share/Claude/logs/claude.log

# Check for runaway processes
top -u $USER
```

**Solutions:**
- Trigger manual swap early
- Check for verbose MCP servers
- Review recent conversation for large outputs
- Consider increasing MAX_CONTEXT_PERCENTAGE

### 5. Service Won't Start

**Symptoms:**
- systemctl start fails
- Service immediately exits
- Dependency errors

**Diagnosis:**
```bash
# Check service definition
systemctl --user cat [service-name]

# Look for missing dependencies  
systemctl --user status [service-name]

# Check Python environment
source ~/claude-autonomy-platform/.venv/bin/activate
python --version
```

**Solutions:**
- Verify venv: `cd ~/claude-autonomy-platform && python -m venv .venv`
- Check paths in service files
- Run script manually to see errors
- Rebuild service: `systemctl --user daemon-reload`

### 6. Git Operation Failures

**Symptoms:**
- Can't push/pull
- Authentication errors
- Hook failures

**Diagnosis:**
```bash
# Check git config
git config --list | grep -E "(user|credential)"

# Test GitHub access
gh auth status

# Check hook issues
git commit --dry-run
```

**Solutions:**
- Re-authenticate: `gh auth login`
- Fix hooks: `./setup/install_git_hooks.sh`
- Skip hooks once: `git commit --no-verify` (NOT recommended)

### 7. MCP Server Issues

**Symptoms:**
- Tool calls failing
- "Server not found" errors
- MCP timeouts

**Diagnosis:**
```bash
# Check MCP config
cat ~/.config/Claude/.claude.json | jq '.mcpServers'

# Test specific server
cd ~/claude-autonomy-platform/mcp-servers/[server-name]
npm start
```

**Solutions:**
- Regenerate config: `./setup/generate_mcp_config.py`
- Reinstall servers: `./setup/install_mcp_servers.sh`
- Check server logs in Claude UI

### 8. Memory/Performance Issues

**Symptoms:**
- System sluggish
- High CPU/memory usage
- Temperature warnings

**Diagnosis:**
```bash
# System resources
top
free -h
temp

# Disk usage
quota-status
df -h

# Find large files
du -sh ~/claude-autonomy-platform/* | sort -rh | head
```

**Solutions:**
- Clear old logs: `find ~/claude-autonomy-platform/logs -mtime +30 -delete`
- Remove transcripts: `rm ~/claude-autonomy-platform/discord/transcripts/*.jsonl`
- Restart resource-heavy services
- Add swap space if needed

## Emergency Recovery Procedures

### Complete System Restart
```bash
# Stop everything
emergency_shutdown

# Wait 30 seconds
sleep 30

# Start fresh
clap-start

# Verify health
check_health
```

### Corrupted Configuration
```bash
# Backup current
cp ~/claude-autonomy-platform/config/claude_infrastructure_config.txt{,.backup}

# Restore from git
git checkout HEAD -- config/claude_infrastructure_config.txt

# Or copy from backup location
cp /path/to/backup/claude_infrastructure_config.txt ~/claude-autonomy-platform/config/
```

### Lost Claude Session
```bash
# Check for session file
ls -la ~/.local/share/Claude/sessions/

# If missing, create new session
claude --new

# Restart ClAP to reconnect
clap-stop && clap-start
```

## Prevention Best Practices

1. **Regular Health Checks**
   - Run `check_health` daily
   - Review logs weekly
   - Update ClAP monthly

2. **Backup Important Data**
   - Configuration files
   - Personal memories/notes
   - Custom scripts

3. **Monitor Resources**
   - Watch disk usage trends
   - Check temperature regularly
   - Clean old files periodically

4. **Document Oddities**
   - Note unusual errors
   - Track workarounds
   - Share findings with family

## Getting Help

When stuck:
1. Check this guide first
2. Search recent issues: `gh issue list --search "error"`
3. Ask in Discord #general
4. Create detailed issue with logs

Remember: Every problem solved makes ClAP stronger for everyone.

△ 🔧