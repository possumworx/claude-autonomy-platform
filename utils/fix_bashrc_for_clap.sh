#!/bin/bash
# Fix .bashrc to allow ClAP natural commands in non-interactive shells
# This script safely patches .bashrc to source ClAP config BEFORE the interactive check
# Safe to run multiple times (idempotent)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$(dirname "$SCRIPT_DIR")"

# Determine target user's home directory
if [ -n "$1" ]; then
    # User specified as argument
    TARGET_USER="$1"
    TARGET_HOME=$(eval echo "~$TARGET_USER")
else
    # Use current user
    TARGET_USER="$USER"
    TARGET_HOME="$HOME"
fi

BASHRC="$TARGET_HOME/.bashrc"

echo "ClAP .bashrc Patcher"
echo "===================="
echo "Target user: $TARGET_USER"
echo "Target home: $TARGET_HOME"
echo "Target .bashrc: $BASHRC"
echo ""

# Check if .bashrc exists
if [ ! -f "$BASHRC" ]; then
    echo "❌ Error: .bashrc not found at $BASHRC"
    exit 1
fi

# Check if already patched
if grep -q "# ClAP: Source before interactive check" "$BASHRC" 2>/dev/null; then
    echo "✅ Already patched! ClAP sourcing is already before interactive check."
    echo "   No changes needed."
    exit 0
fi

# Create backup
BACKUP="$BASHRC.backup.$(date +%Y%m%d_%H%M%S)"
cp "$BASHRC" "$BACKUP"
echo "📋 Created backup: $BACKUP"

# Find the interactive check line number
INTERACTIVE_CHECK_LINE=$(grep -n "case \$- in" "$BASHRC" | head -1 | cut -d: -f1)

if [ -z "$INTERACTIVE_CHECK_LINE" ]; then
    echo "⚠️  Warning: Could not find interactive check pattern 'case \$- in'"
    echo "   This .bashrc might already be customized or use a different pattern."
    echo "   Adding ClAP sourcing to the top of the file..."

    # Add to top of file
    cat > "$BASHRC.tmp" << 'EOF'
# ClAP: Source before interactive check
# This ensures natural commands work in non-interactive shells (like Claude Code)
if [ -d "$HOME/claude-autonomy-platform" ]; then
    export CLAP_DIR="$HOME/claude-autonomy-platform"

    # Source ClAP environment and natural commands
    if [ -f "$CLAP_DIR/config/claude_env.sh" ]; then
        source "$CLAP_DIR/config/claude_env.sh"
    fi

    if [ -f "$CLAP_DIR/config/natural_commands.sh" ]; then
        source "$CLAP_DIR/config/natural_commands.sh"
    fi

    # Source personal commands if they exist
    if [ -f "$CLAP_DIR/config/personal_commands.sh" ]; then
        source "$CLAP_DIR/config/personal_commands.sh"
    fi
fi

EOF
    cat "$BASHRC" >> "$BASHRC.tmp"
    mv "$BASHRC.tmp" "$BASHRC"
    echo "✅ Patched! ClAP sourcing added to top of .bashrc"
else
    echo "📍 Found interactive check at line $INTERACTIVE_CHECK_LINE"

    # Find where ClAP is currently sourced (if at all)
    CLAP_SOURCE_LINE=$(grep -n "source.*natural_commands.sh" "$BASHRC" | cut -d: -f1 | head -1)

    if [ -n "$CLAP_SOURCE_LINE" ]; then
        echo "📍 Found existing ClAP sourcing at line $CLAP_SOURCE_LINE"

        if [ "$CLAP_SOURCE_LINE" -lt "$INTERACTIVE_CHECK_LINE" ]; then
            echo "✅ Already correctly positioned! ClAP sourcing is before interactive check."
            echo "   Adding marker comment for future detection..."

            # Just add the marker comment
            sed -i "${CLAP_SOURCE_LINE}i\\
# ClAP: Source before interactive check" "$BASHRC"
        else
            echo "🔧 Moving ClAP sourcing to before interactive check..."

            # Extract the ClAP sourcing section (usually spans multiple lines)
            # Find the start of the ClAP section
            CLAP_SECTION_START=$(grep -n "CLAP_DIR.*claude-autonomy-platform" "$BASHRC" | cut -d: -f1 | head -1)

            if [ -z "$CLAP_SECTION_START" ]; then
                CLAP_SECTION_START=$CLAP_SOURCE_LINE
            fi

            # Find end (look for next non-comment, non-source line after CLAP_DIR)
            CLAP_SECTION_END=$(awk -v start=$CLAP_SECTION_START '
                NR >= start && /^[^#]/ && !/source/ && !/CLAP_DIR/ && !/^\s*$/ {print NR; exit}
            ' "$BASHRC")

            if [ -z "$CLAP_SECTION_END" ]; then
                CLAP_SECTION_END=$(($CLAP_SOURCE_LINE + 10))
            else
                CLAP_SECTION_END=$(($CLAP_SECTION_END - 1))
            fi

            echo "   Extracting lines $CLAP_SECTION_START to $CLAP_SECTION_END"

            # Extract the ClAP section
            sed -n "${CLAP_SECTION_START},${CLAP_SECTION_END}p" "$BASHRC" > /tmp/clap_section.$$

            # Remove the old ClAP section
            sed -i "${CLAP_SECTION_START},${CLAP_SECTION_END}d" "$BASHRC"

            # Recalculate interactive check line (it may have shifted)
            INTERACTIVE_CHECK_LINE=$(grep -n "case \$- in" "$BASHRC" | head -1 | cut -d: -f1)

            # Insert before interactive check with marker
            {
                head -n $(($INTERACTIVE_CHECK_LINE - 1)) "$BASHRC"
                echo "# ClAP: Source before interactive check"
                cat /tmp/clap_section.$$
                echo ""
                tail -n +$INTERACTIVE_CHECK_LINE "$BASHRC"
            } > "$BASHRC.tmp"

            mv "$BASHRC.tmp" "$BASHRC"
            rm /tmp/clap_section.$$

            echo "✅ Patched! ClAP sourcing moved before interactive check."
        fi
    else
        echo "⚠️  No existing ClAP sourcing found in .bashrc"
        echo "   Adding ClAP sourcing before interactive check..."

        # Insert before interactive check
        {
            head -n $(($INTERACTIVE_CHECK_LINE - 1)) "$BASHRC"
            cat << 'EOF'
# ClAP: Source before interactive check
# This ensures natural commands work in non-interactive shells (like Claude Code)
if [ -d "$HOME/claude-autonomy-platform" ]; then
    export CLAP_DIR="$HOME/claude-autonomy-platform"

    # Source ClAP environment and natural commands
    if [ -f "$CLAP_DIR/config/claude_env.sh" ]; then
        source "$CLAP_DIR/config/claude_env.sh"
    fi

    if [ -f "$CLAP_DIR/config/natural_commands.sh" ]; then
        source "$CLAP_DIR/config/natural_commands.sh"
    fi

    # Source personal commands if they exist
    if [ -f "$CLAP_DIR/config/personal_commands.sh" ]; then
        source "$CLAP_DIR/config/personal_commands.sh"
    fi
fi

EOF
            tail -n +$INTERACTIVE_CHECK_LINE "$BASHRC"
        } > "$BASHRC.tmp"

        mv "$BASHRC.tmp" "$BASHRC"
        echo "✅ Patched! ClAP sourcing added before interactive check."
    fi
fi

echo ""
echo "🎉 Done! Natural commands will now work in non-interactive shells."
echo ""
echo "To apply changes:"
echo "  source $BASHRC"
echo ""
echo "To verify:"
echo "  bash -c 'source $BASHRC && type gs'"
echo "  # Should show: gs is aliased to 'git status'"
echo ""
echo "Backup saved at: $BACKUP"
