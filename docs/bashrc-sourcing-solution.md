# Solution for .bashrc Sourcing in Claude Code

## Issue
Claude Code runs bash commands in non-interactive mode, which doesn't automatically source .bashrc. This causes aliases and custom environment variables to be unavailable.

## Solution Implemented

1. **Project-level settings**: Created `.claude/settings.json` in the ClAP directory with essential environment variables:
   - PATH includes our custom directories (utils, delta-home/tools, etc.)
   - CLAUDE_HOME set to $HOME
   - BASHRC_SOURCED marker for verification

2. **Wrapper script**: Created `~/claude-autonomy-platform/utils/claude-wrapper` that:
   - Sources .bashrc before launching Claude Code
   - Passes all arguments through to the real claude executable

## Usage

To use the wrapper (if settings.json isn't sufficient):
```bash
alias claude='~/claude-autonomy-platform/utils/claude-wrapper'
```

## Verification

Environment variables are now available:
- Run `echo $BASHRC_SOURCED` to verify (should show "1")
- PATH includes our custom directories
- Commands like `check_health` are accessible

## Note

The `.claude/settings.json` approach is recommended as it:
- Works for all team members automatically
- Doesn't require changing how Claude Code is launched
- Is committed to the repository for consistency