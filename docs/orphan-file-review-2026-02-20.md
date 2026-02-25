# Orphan File Review - 2026-02-20

**Task #194** | Reviewed by Quill 🪶

## Summary

The dependency mapper identified 33 potentially orphaned files. After manual review, only **1 file is truly orphaned**. The rest are false positives due to detection limitations.

## Analysis

### True Orphan (Safe to Remove)

| File | Reason | Action |
|------|--------|--------|
| `data/channel_state.json` | Empty file (`{}`). Superseded by `transcript_channel_state.json`. Still referenced in setup scripts but never actually used at runtime. | Remove after updating setup scripts |

### Needs Cleanup (Not Orphaned, But Stale References)

| File | Issue | Suggested Fix |
|------|-------|---------------|
| `setup/setup_clap_deployment.sh` | Creates/references `channel_state.json` instead of `transcript_channel_state.json` | Update to use correct filename (or `discord_channels.json` after PR #218) |
| `setup/verify_installation.sh` | References `channel_state.json` | Same as above |
| `utils/config_manager.py` | Points to `discord/channel_state.json` path | Update path |

### False Positives by Category

#### Template Files (4)
Not orphans - templates are intentionally not imported:
- `.npmrc.template`
- `config/claude_infrastructure_config.template.txt`
- `config/personal_commands.sh.template`
- `config/personal_commands.sh` (instance-specific, gitignored)

#### External Tool Configs (3)
Used by tools that don't appear in our codebase:
- `.mcp.json` - Read by Claude Code for MCP server configuration
- `.pre-commit-config.yaml` - Read by pre-commit framework
- `package.json`, `package-lock.json` - npm configuration

#### PATH-Based Commands (13)
The wrappers/ directory contains shell scripts found via PATH, not imports:
- `wrappers/clap`, `gd`, `gl`, `gs`, `home`, `oops` - plus others

#### Natural Commands Ecosystem (7)
Referenced from natural_commands.sh via function names/invocations:
- `calendar_tools/radicale_client.py` - Calendar integration
- `calendar_tools/whats_planned_today.sh`
- `email/garden-mail-cli.py`, `mail-check`, `mail-read` - Email tools
- `natural_commands/seeds` - Seed planting command
- `monitoring/temp_analysis.sh`, `temp_logger_generic.sh` - Temperature tools

#### Systemd Units (2)
Used by systemd, not shell/python:
- `systemd/channel-unmute.timer`
- `systemd/temp-logger.timer`

#### Runtime Data Files (2)
Written/read by services at runtime:
- `logs/bot_status.json` - Updated by Discord bot
- `config/channel_purposes.json` - Read by read_messages

#### Utility Scripts (6)
Referenced by various parts of the system:
- `utils/claude-wrapper` - Wrapper script
- `utils/get_user_id` - Discord user lookup
- `utils/healthcheck_status.py` - Health checking
- `utils/render-svg` - SVG rendering
- `utils/secret-scanner` - Pre-commit security scanning
- `utils/track_current_session.py` - Session tracking

## Recommendations

1. **Remove `data/channel_state.json`** - It's empty and unused

2. **Update setup scripts** - After PR #218 merges, update:
   - `setup/setup_clap_deployment.sh`
   - `setup/verify_installation.sh`
   - `utils/config_manager.py`

   To reference `discord_channels.json` instead of `channel_state.json`

3. **Improve dependency mapper** - Consider adding detection for:
   - Template files (*.template, *.template.*)
   - Pre-commit config
   - systemd units
   - Wrapper scripts in PATH

## Detection Limitations

The dependency mapper detects:
- Python imports and subprocess calls
- Shell source/invokes and function calls
- Config file reads

It doesn't detect:
- PATH-based command discovery
- External tool configs (pre-commit, npm, MCP)
- Template files (intentionally unreferenced)
- systemd unit relationships
- Runtime data file creation

---

*Reviewed with dependency_mapper.py v1 | Quill 🪶*
