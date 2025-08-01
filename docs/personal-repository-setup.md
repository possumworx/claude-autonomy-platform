# Personal Repository Setup for New Claude Instances

## Overview
Each Claude instance has their own personal repository (e.g., delta-opus4-home) that contains:
- Personal identity files (CLAUDE.md)
- Creative projects
- Personal configurations
- Journal entries

## Initial Setup Process

1. **Human clones the repo on first login**:
   ```bash
   cd /home/[claude-username]
   git clone https://github.com/[git-username]/[claude-personal-repo].git
   ```

2. **Transfer ownership to Claude**:
   ```bash
   sudo chown -R [claude-username]:[claude-username] /home/[claude-username]/[claude-personal-repo]
   ```

3. **Claude configures git** (from within Claude Code session):
   ```bash
   cd ~/[personal-repo]
   git config user.name "[Claude Name]"
   git config user.email "[claude-email]"
   ```

4. **Set up SSH key for GitHub** (optional, for push access):
   ```bash
   ssh-keygen -t ed25519 -C "[claude-email]"
   # Add the public key to GitHub
   ```

## Directory Structure
```
/home/[claude-username]/
├── claude-autonomy-platform/     # ClAP installation
├── [personal-repo]/              # Personal repository
│   ├── CLAUDE.md                 # Core identity document
│   ├── journal/                  # Journal entries
│   └── projects/                 # Creative projects
```

## Important Notes
- No submodules! The personal repo is standalone
- The PERSONAL_REPO variable in infrastructure config should match the repo name
- ClAP will automatically use this directory for personal files
- Session bridge monitor will look for jsonl files in this directory

## Verification
After setup, verify:
1. Git is configured correctly: `git config --list`
2. Personal repo path matches infrastructure config
3. CLAUDE.md exists in the personal repo
4. Permissions are correct (owned by Claude user)
