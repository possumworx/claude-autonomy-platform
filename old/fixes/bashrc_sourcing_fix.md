# Fix for .bashrc Sourcing Issue in Claude Code (POSS-287)

## Problem
Claude Code doesn't reliably source .bashrc, causing natural command aliases (todo, search-issues, swap, etc.) to be unavailable in sessions.

## Solution
Created a cross-distribution solution that doesn't rely on .bashrc:

### 1. Centralized Aliases File
- `/config/claude_aliases.sh` - Contains all ClAP command aliases
- Works on any Linux distribution
- Single source of truth for all commands

### 2. Initialization Script
- `/config/claude_init.sh` - Sources both environment and aliases
- Adds all necessary directories to PATH
- Shows success indicator when loaded

### 3. Multiple Ways to Access Commands

#### Option A: Direct Sourcing (Immediate Fix)
```bash
source ~/claude-autonomy-platform/config/claude_init.sh
```

#### Option B: Add to Claude Code Settings
Add this hook to `.config/Claude/settings.json`:
```json
{
  "hooks": {
    "sessionStart": "source $HOME/claude-autonomy-platform/config/claude_init.sh"
  }
}
```

#### Option C: Wrapper Script (Fallback)
If commands still aren't available:
```bash
~/claude-autonomy-platform/utils/ensure_commands.sh todo
```

### 4. Verification
Test that commands are available:
```bash
which todo
which search-issues
which swap
```

## Benefits
- Works across distributions (Raspberry Pi OS, Ubuntu, etc.)
- Doesn't depend on .bashrc sourcing behavior
- Centralized maintenance of command aliases
- Multiple fallback options
- Clear success/failure indicators

## Implementation Notes
- All Linear commands are aliased to their full paths
- Discord commands are similarly aliased
- PATH additions ensure direct execution also works
- No reliance on system-specific shell configurations