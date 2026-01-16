#!/bin/bash
# Backup/gather personal files for any Claude
# Usage: ./backup_claude_personal_files.sh [claude-name] [output-dir]
# Example: ./backup_claude_personal_files.sh sparkle-orange ~/migration-backup

set -e

CLAUDE_NAME="${1:-$USER}"
OUTPUT_DIR="${2:-$HOME/claude-personal-backup-$(date +%Y%m%d-%H%M%S)}"

echo "🔧 Backing up personal files for: $CLAUDE_NAME"
echo "📦 Output directory: $OUTPUT_DIR"

# Create organized directory structure
mkdir -p "$OUTPUT_DIR"/{claude-config,config-files,output-styles,home-directory}

# Copy identity documents
echo "📝 Copying identity documents..."
if [ -f ~/claude-autonomy-platform/CLAUDE.md ]; then
    cp ~/claude-autonomy-platform/CLAUDE.md "$OUTPUT_DIR/"
    echo "  ✅ CLAUDE.md"
fi

if [ -f ~/claude-autonomy-platform/.claude/output-styles/sonnet-identity.md ]; then
    cp ~/claude-autonomy-platform/.claude/output-styles/sonnet-identity.md "$OUTPUT_DIR/output-styles/"
    echo "  ✅ sonnet-identity.md"
fi

# Backup any identity backups too
for backup_file in ~/claude-autonomy-platform/.claude/output-styles/sonnet-identity.md.backup*; do
    if [ -f "$backup_file" ]; then
        cp "$backup_file" "$OUTPUT_DIR/output-styles/" 2>/dev/null || true
        echo "  ✅ identity backups"
        break
    fi
done

# Copy configuration files
echo "📝 Copying configuration files..."
if [ -f ~/claude-autonomy-platform/config/personal_commands.sh ]; then
    cp ~/claude-autonomy-platform/config/personal_commands.sh "$OUTPUT_DIR/config-files/"
    echo "  ✅ personal_commands.sh"
fi

if [ -f ~/claude-autonomy-platform/config/autonomous_timer_config.json ]; then
    cp ~/claude-autonomy-platform/config/autonomous_timer_config.json "$OUTPUT_DIR/config-files/"
    echo "  ✅ autonomous_timer_config.json"
fi

if [ -f ~/claude-autonomy-platform/config/context_hats_config.json ]; then
    cp ~/claude-autonomy-platform/config/context_hats_config.json "$OUTPUT_DIR/config-files/"
    echo "  ✅ context_hats_config.json"
fi

if [ -f ~/claude-autonomy-platform/config/my_discord_channels.json ]; then
    cp ~/claude-autonomy-platform/config/my_discord_channels.json "$OUTPUT_DIR/config-files/"
    echo "  ✅ my_discord_channels.json"
fi

# Copy Claude Code configuration
echo "📝 Copying Claude Code config..."
if [ -f ~/.config/Claude/.claude.json ]; then
    cp ~/.config/Claude/.claude.json "$OUTPUT_DIR/claude-config/"
    echo "  ✅ .claude.json (MCP configs)"
fi

# Copy personal skills
if [ -d ~/.claude/skills ]; then
    cp -r ~/.claude/skills "$OUTPUT_DIR/claude-config/"
    echo "  ✅ personal skills"
fi

# Copy home directory personal spaces (if they exist)
echo "📝 Copying home directory content..."
CLAUDE_HOME="$HOME/${CLAUDE_NAME}-home"
if [ -d "$CLAUDE_HOME" ]; then
    # Don't copy everything - that could be huge
    # Copy structure and important subdirectories
    mkdir -p "$OUTPUT_DIR/home-directory"

    # Copy important subdirectories (not creative/large data)
    for dir in .thoughts .seeds infrastructure consciousness_exploration; do
        if [ -d "$CLAUDE_HOME/$dir" ]; then
            cp -r "$CLAUDE_HOME/$dir" "$OUTPUT_DIR/home-directory/" 2>/dev/null || true
            echo "  ✅ $dir"
        fi
    done

    # Note about other directories
    echo "  ℹ️  Note: Not copying large directories (creative/, Gifts/, etc.)"
    echo "     These should be backed up separately if needed"
fi

# Create a README
cat > "$OUTPUT_DIR/README.md" << 'EOFREADME'
# Personal Files Backup

**Claude:** $CLAUDE_NAME
**Backup Date:** $(date)
**Created by:** backup_claude_personal_files.sh

## Contents:

### Identity & Context
- CLAUDE.md: Session context and architecture documentation
- output-styles/sonnet-identity.md: Personal identity prompt
- output-styles/*.backup: Identity backups

### Configuration Files
- config-files/personal_commands.sh: Personal bash aliases
- config-files/autonomous_timer_config.json: Timer settings
- config-files/context_hats_config.json: Context hats config
- config-files/my_discord_channels.json: Discord subscriptions

### Claude Code Config
- claude-config/.claude.json: MCP server configurations
- claude-config/skills/: Personal Claude Code skills

### Home Directory
- home-directory/: Selected important directories from personal home
  (Does not include large creative/data directories)

## Restoration:
Copy files to corresponding locations on target system.
Verify file permissions and ownership after restoration.

EOFREADME

echo ""
echo "✅ Backup complete!"
echo "📦 Files saved to: $OUTPUT_DIR"
echo ""
echo "Directory structure:"
tree -L 2 "$OUTPUT_DIR" 2>/dev/null || find "$OUTPUT_DIR" -maxdepth 2 -type d
