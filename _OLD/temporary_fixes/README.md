# Temporary Fixes from Tuesday's Deployment

These scripts were written during the emergency deployment session to fix various installer issues. They contain battle-tested solutions that should be incorporated into the main installer.

## fix_installer.sh
**Purpose**: Fix service names and tmux session names

**Key fixes**:
- Replace `notification-monitor.service` with `channel-monitor.service` throughout
- Change hardcoded `PERSISTENT_SESSION="sonnet-4"` to `PERSISTENT_SESSION="persistent-login"`
- Rename existing wrong service files
- Kill wrong tmux sessions

**Should be incorporated into**: `setup/setup_clap_deployment.sh`

## fix_systemd_env.py
**Purpose**: Create systemd-compatible environment files

**Key fixes**:
- Generate `claude.env` (systemd format) from `claude_infrastructure_config.txt`
- Extract only the environment variables that systemd needs
- Update service files to use claude.env instead of claude_env.sh
- Solve the "shell syntax in systemd" warnings (POSS-76)

**Should be incorporated into**: A new setup script or the main installer

## diagnose_sparkle_services.sh
**Purpose**: Quick health check of all services

**Key features**:
- Check service status
- Show recent logs from each service
- Verify required files exist
- Display environment file contents

**Should be incorporated into**: `utils/healthcheck_status.py` or kept as a separate diagnostic tool

## Summary
These fixes address issues from:
- POSS-75 (Windows line endings)
- POSS-76 (systemd shell syntax warnings)  
- POSS-78 (tmux session name inconsistency)
- General service naming issues

All were tested and working on sparkle-sonnet's deployment.