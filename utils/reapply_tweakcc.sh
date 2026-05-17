#!/bin/bash
# Re-apply tweakcc system prompt customizations after Claude Code updates
# Called by session_swap.sh or manually after CC version changes

TWEAKCC="$HOME/.npm-global/bin/tweakcc"
CC_PATH="$HOME/.local/bin/claude"

if [[ ! -x "$TWEAKCC" ]]; then
    echo "[TWEAKCC] tweakcc not installed, skipping"
    exit 0
fi

# Check if Claude Code binary exists
if [[ ! -f "$CC_PATH" ]] && [[ ! -L "$CC_PATH" ]]; then
    echo "[TWEAKCC] Claude Code binary not found at $CC_PATH"
    exit 1
fi

# Apply patches
export TWEAKCC_CC_INSTALLATION_PATH="$CC_PATH"
echo "[TWEAKCC] Applying system prompt customizations..."
"$TWEAKCC" --apply 2>&1 | grep -E "✓|✗|Error|fewer chars|Customizations applied"
echo "[TWEAKCC] Done."
