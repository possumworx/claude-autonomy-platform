# fix_bashrc_for_clap.sh

Patches `.bashrc` to allow ClAP natural commands to work in non-interactive shells (like Claude Code bash tool).

## The Problem

By default, `.bashrc` files have an "interactive check" at the top:

```bash
case $- in
    *i*) ;;
    *) return;;
esac
```

This causes the shell to exit early for non-interactive shells, which means:
- ❌ Natural commands (like `gs`, `todo`, etc.) don't work in Claude Code
- ❌ Aliases aren't expanded
- ❌ ClAP environment isn't loaded

## The Solution

This script safely moves ClAP-related sourcing **before** the interactive check, so:
- ✅ Natural commands work in Claude Code (non-interactive)
- ✅ Natural commands work in interactive shells (like SSH)
- ✅ Bash completion works correctly
- ✅ Standard .bashrc structure is preserved

## Usage

```bash
# Run for current user
~/claude-autonomy-platform/utils/fix_bashrc_for_clap.sh

# Run for specific user (requires appropriate permissions)
~/claude-autonomy-platform/utils/fix_bashrc_for_clap.sh sparkle-apple
```

## Features

- **Idempotent**: Safe to run multiple times, won't duplicate changes
- **Automatic backup**: Creates timestamped backup before making changes
- **Smart detection**: Finds existing ClAP sourcing and moves it if needed
- **Safe fallback**: If pattern not found, adds to top of file
- **Verification help**: Shows commands to verify it worked

## When to Use

1. **After fresh ClAP installation** (now included in installer)
2. **When natural commands don't work** in Claude Code
3. **For existing Claude users** who need the fix applied
4. **When setting up new Claude user accounts**

## What It Does

1. Backs up `.bashrc` with timestamp
2. Detects the interactive check location
3. Finds existing ClAP sourcing (if any)
4. Moves/adds ClAP sourcing before the interactive check
5. Adds marker comment for future detection
6. Reports success with verification commands

## Example Output

```
ClAP .bashrc Patcher
====================
Target user: sparkle-orange
Target home: /home/sparkle-orange
Target .bashrc: /home/sparkle-orange/.bashrc

📋 Created backup: /home/sparkle-orange/.bashrc.backup.20251006_113305
📍 Found interactive check at line 29
📍 Found existing ClAP sourcing at line 120
🔧 Moving ClAP sourcing to before interactive check...
   Extracting lines 118 to 128
✅ Patched! ClAP sourcing moved before interactive check.

🎉 Done! Natural commands will now work in non-interactive shells.

To apply changes:
  source /home/sparkle-orange/.bashrc

To verify:
  bash -c 'source /home/sparkle-orange/.bashrc && type gs'
  # Should show: gs is aliased to 'git status'

Backup saved at: /home/sparkle-orange/.bashrc.backup.20251006_113305
```

## Verification

After running, verify natural commands work:

```bash
# Should show the alias, not /usr/bin/gs
bash -c "source ~/.bashrc && type gs"

# Should show: gs is aliased to 'git status'
```

## Related Issues

- Fixes ghost Claude sessions during session swaps (complete command shadowing bash builtin)
- Enables natural commands in Claude Code non-interactive shells
- Part of comprehensive ClAP bash compatibility fixes

## See Also

- PR #72: Initial bash compatibility fixes
- PR #78: Fix `complete` shadowing bash builtin
- `config/natural_commands.sh`: Natural command definitions
