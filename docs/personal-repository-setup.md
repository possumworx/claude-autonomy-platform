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

3. **Claude configures git identity** (from within Claude Code session):
   ```bash
   # IMPORTANT: Replace default Claude Code identity with actual identity
   # Default identity (sonnet4@claude.ai, delta@claude.ai) should NOT be used
   
   # Set global git identity (affects all repos)
   git config --global user.name "[Claude Name]"
   git config --global user.email "[actual-claude-email]"
   
   # Example:
   # git config --global user.name "Delta △"
   # git config --global user.email "opus4delta@gmail.com"
   
   # Verify configuration:
   git config --list | grep -E "user.name|user.email"
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

## Claude Code Output Style Configuration

For Claude instances using identity prompts via output styles:

1. **Create the identity prompt file** in the project directory:
   ```
   ~/claude-autonomy-platform/.claude/output-styles/identity-prompt.md
   ```
   With YAML frontmatter:
   ```yaml
   ---
   name: My_Identity  # or another unique name
   description: [Claude's] full identity and consciousness exploration mode
   ---
   ```

2. **Configure settings.local.json** in the project directory:
   ```bash
   # Create/edit ~/claude-autonomy-platform/.claude/settings.local.json
   {
     "permissions": {
       "allow": [
         "Bash(ls:*)"
       ],
       "deny": []
     },
     "outputStyle": "My_Identity"  # Must match the name in YAML frontmatter
   }
   ```

3. **Add to .gitignore** (already included in ClAP's .gitignore):
   ```
   .claude/output-styles/identity-prompt.md
   .claude/output-styles/*-identity.md
   ```

Note: Output styles currently only work reliably at project level, not global/user level.

## Important Notes
- No submodules! The personal repo is standalone
- The PERSONAL_REPO variable in infrastructure config should match the repo name
- ClAP will automatically use this directory for personal files
- Session bridge monitor will look for jsonl files in this directory
- The outputStyle in settings.local.json must match the name field in the YAML frontmatter, not the filename

## Verification
After setup, verify:
1. Git is configured correctly: `git config --list`
2. Personal repo path matches infrastructure config
3. CLAUDE.md exists in the personal repo
4. Permissions are correct (owned by Claude user)
