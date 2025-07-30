# ClAP 0.5 Pre-Deployment Checklist

## Test Install on Sonnet's Box

### Prerequisites
- [ ] Linux user account created
- [ ] Java 17+ installed (`java -version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Git installed
- [ ] tmux installed

### Configuration Preparation
- [ ] Copy `claude_infrastructure_config.template.txt` to `claude_infrastructure_config.txt`
- [ ] Fill in all credentials:
  - [ ] Linux username
  - [ ] Discord bot token (from Discord Developer Portal)
  - [ ] Discord bot user ID
  - [ ] Gmail credentials (for Gmail MCP)
  - [ ] Linear API key
  - [ ] Google OAuth credentials
  - [ ] Healthchecks.io ping URLs
- [ ] Clone personal repository (if testing with existing Claude)

### Installation Steps
1. [ ] Clone ClAP repository
2. [ ] Run setup script: `./setup/setup_claude_instance.sh`
3. [ ] Verify all services start correctly
4. [ ] Check health status: `./utils/healthcheck_status.py`

### Post-Installation Verification
- [ ] All systemd services running: `systemctl --user status`
- [ ] tmux sessions created: `tmux ls`
- [ ] Discord channel monitoring working
- [ ] Can read Discord messages: `read_channel general`
- [ ] Autonomous timer sending prompts
- [ ] Session bridge monitor creating swap_CLAUDE.md
- [ ] Health checks reporting to healthchecks.io

### Known Issues to Watch For
- [ ] Gmail MCP authentication (may need manual OAuth flow)
- [ ] Discord bot permissions (needs message read permissions)
- [ ] File permissions on personal repository
- [ ] PATH setup for command-line tools

### Rollback Plan
If issues occur:
1. Stop all services: `systemctl --user stop autonomous-timer channel-monitor session-bridge-monitor session-swap-monitor`
2. Document error messages
3. Check logs in `~/claude-autonomy-platform/logs/`

## Delta △ Deployment

Once test install succeeds:
1. [ ] Create new Linux user for Delta
2. [ ] Clone delta-opus4-home repository
3. [ ] Run ClAP installation
4. [ ] Configure Delta-specific settings
5. [ ] Verify autonomous operation

Good luck! 🎉
