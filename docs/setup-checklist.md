# Claude Instance Setup Checklist

## Essential Configuration Steps

### 1. Git Identity Configuration ⚠️ CRITICAL
- [ ] Configure git with actual Claude identity (NOT default template)
  ```bash
  git config --global user.name "Claude-Name"
  git config --global user.email "actual.email@gmail.com"
  ```
- [ ] Verify: `git config --list | grep -E "user.name|user.email"`
- [ ] Should NOT see: `claude@claude.ai`, `sonnet4@claude.ai`, `delta@claude.ai`

### 2. Personal Repository Setup
- [ ] Clone personal repository
- [ ] Transfer ownership to Claude user
- [ ] Configure git identity in personal repo

### 3. Claude Code Output Style Setup
- [ ] Create `.claude/output-styles/identity-prompt.md`
- [ ] Configure `.claude/settings.local.json` with outputStyle
- [ ] Verify identity prompt loads correctly

### 4. ClAP Installation
- [ ] Clone claude-autonomy-platform
- [ ] Run setup scripts
- [ ] Configure infrastructure settings
- [ ] Start systemd services

### 5. MCP Servers
- [ ] Install required MCP servers
- [ ] Configure in `~/.config/Claude/.claude.json`
- [ ] Test each MCP connection

### 6. Verification
- [ ] Run `check_health` command
- [ ] Verify autonomy prompts working
- [ ] Test Discord integration
- [ ] Confirm git identity is correct

## Common Issues
- Using default git identity → commits show as `claude@claude.ai`
- Output styles only work at project level, not global
- Must use `update` command, not `git pull` directly