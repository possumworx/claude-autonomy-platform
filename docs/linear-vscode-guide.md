# Linear + VS Code + Git Integration Guide 🚀

## Quick Setup

1. **Install VS Code Extensions**
   - Open Command Palette (Ctrl+Shift+P)
   - Run: `Extensions: Install Extensions`
   - Search and install:
     - "Linear Connect" (by Linear)
     - "Linear" (by Strigo)
     - "GitLens" (by GitKraken)

2. **Authenticate with Linear**
   - Command Palette → "Linear: Authenticate"
   - Follow OAuth flow
   - You're connected!

## Magic Workflows ✨

### Creating a New Feature Branch
```bash
# Old way:
git checkout -b my-feature

# Linear way:
git checkout -b CLA-123-fix-discord-timeout
# Linear automatically links this branch to issue CLA-123!
```

### Committing with Auto-Linking
```bash
# Just commit normally - if your branch has CLA-123, it auto-adds to commit:
git commit -m "Fixed the timeout issue"
# Becomes: "CLA-123: Fixed the timeout issue"
```

### VS Code Command Palette Commands
- `Linear: Open Current Issue` - Opens the Linear issue for current branch
- `Linear: Create Issue` - Create new Linear issue from VS Code
- `Linear: Search Issues` - Find issues without leaving editor

### TODO Comments → Linear Issues
```python
# TODO: Investigate why hedgehog photos aren't loading
#      This can become a Linear issue with one click!
```

## Amy's One-Click Commands 🎯

### Deploy with Linear Link
```bash
./deploy.sh "CLA-123: Fixed hedgehog photo loading"
```

### Create New Branch
```bash
./scripts/new-branch.sh CLA-123 "hedgehog photo fix"
```

### Check Status
```bash
./scripts/status.sh
```

## Keyboard Shortcuts 

| Action | Shortcut |
|--------|----------|
| Command Palette | Ctrl+Shift+P |
| Quick Open | Ctrl+P |
| Terminal | Ctrl+` |
| Git Panel | Ctrl+Shift+G |
| Save All | Ctrl+K S |
| Find in Files | Ctrl+Shift+F |

## Pro Tips 💡

1. **Branch Naming Convention**
   - Always start with Linear ID: `CLA-123-description`
   - Use kebab-case: `fix-discord-timeout`
   - Keep it short but descriptive

2. **Commit Messages**
   - Will auto-prepend Linear ID from branch
   - Start with verb: "Fix", "Add", "Update"
   - Keep under 50 characters

3. **VS Code Workspace**
   - Open `clap.code-workspace` to see all projects
   - Use Activity Bar (left side) to switch between:
     - Explorer (files)
     - Search 
     - Git
     - Debug
     - Extensions

## Troubleshooting 

**Linear auth not working?**
- Check VS Code Output panel → Linear Connect
- Try: `Developer: Reload Window`

**Git hooks not running?**
- Make sure you're in the repo root
- Check: `ls .git/hooks/prepare-commit-msg`
- Should be executable (green in terminal)

**Can't see Linear issues?**
- Ensure you're authenticated
- Check internet connection
- Verify Linear workspace access

---

Remember: The tools should help, not hinder! If something's annoying, we can fix it together! 🤝

△
