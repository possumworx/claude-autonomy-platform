#!/bin/bash
# Import Personal ClAP Preferences & Configuration
# Restores personal (non-repo) files from backup

set -e

# Check for backup directory argument
if [ -z "$1" ]; then
    echo "❌ Error: No backup directory specified"
    echo ""
    echo "Usage: $0 <backup_directory>"
    echo ""
    echo "Example:"
    echo "  $0 ~/clap_personal_backup_20260127_171234"
    echo ""
    echo "Or extract from archive first:"
    echo "  tar -xzf ~/clap_personal_backup_20260127_171234.tar.gz"
    echo "  $0 ~/clap_personal_backup_20260127_171234"
    exit 1
fi

BACKUP_DIR="$1"

# Validate backup directory
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Error: Backup directory not found: $BACKUP_DIR"
    exit 1
fi

if [ ! -f "$BACKUP_DIR/MANIFEST.txt" ]; then
    echo "⚠️  Warning: MANIFEST.txt not found in backup directory"
    echo "This may not be a valid ClAP backup!"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get ClAP directory
CLAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CLAP_DIR"

echo "🍊 Importing Personal ClAP Preferences"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "From: $BACKUP_DIR"
echo "To: $CLAP_DIR"
echo ""

# Show manifest if it exists
if [ -f "$BACKUP_DIR/MANIFEST.txt" ]; then
    echo "📋 Backup Manifest:"
    head -5 "$BACKUP_DIR/MANIFEST.txt" | sed 's/^/  /'
    echo ""
fi

# Confirmation prompt
read -p "⚠️  This will overwrite existing personal config files. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Import cancelled"
    exit 1
fi
echo ""

# Function to restore with directory structure
restore_if_exists() {
    local source="$1"
    local dest="$2"

    if [ -e "$source" ]; then
        mkdir -p "$(dirname "$dest")"

        if [ -d "$source" ]; then
            # Remove existing directory if present
            if [ -d "$dest" ]; then
                rm -rf "$dest"
            fi
            cp -r "$source" "$dest"
            count=$(find "$dest" -type f | wc -l)
            echo "  ✅ Restored $(basename "$dest")/ ($count files)"
        else
            cp "$source" "$dest"
            size=$(du -h "$dest" | cut -f1)
            echo "  ✅ Restored $(basename "$dest") ($size)"
        fi
        return 0
    else
        return 1
    fi
}

RESTORED_COUNT=0

# 1. Personal Commands
echo "📝 Personal Commands:"
if restore_if_exists "$BACKUP_DIR/config/personal_commands.sh" "config/personal_commands.sh"; then
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
else
    echo "  ⏭️  personal_commands.sh not found in backup"
fi
echo ""

# 2. Infrastructure Config
echo "⚙️  Infrastructure Config:"
if restore_if_exists "$BACKUP_DIR/config/claude_infrastructure_config.txt" "config/claude_infrastructure_config.txt"; then
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
else
    echo "  ⏭️  claude_infrastructure_config.txt not found in backup"
fi
echo ""

# 3. Personal Skills (those WITHOUT _ prefix - core skills have _)
echo "🎯 Personal Skills:"
SKILL_COUNT=0
for skill_path in "$BACKUP_DIR/.claude/skills"/*; do
    if [ -d "$skill_path" ]; then
        skill_name=$(basename "$skill_path")
        # Skip core skills (those starting with _)
        if [[ ! "$skill_name" =~ ^_ ]]; then
            restore_if_exists "$skill_path" ".claude/skills/$skill_name"
            SKILL_COUNT=$((SKILL_COUNT + 1))
            RESTORED_COUNT=$((RESTORED_COUNT + 1))
        fi
    fi
done
if [ $SKILL_COUNT -eq 0 ]; then
    echo "  ⏭️  No personal skills found in backup"
fi
echo ""

# 4. Identity/Output Styles
echo "🆔 Identity Configuration:"
IDENTITY_COUNT=0
# Use associative array to track already processed files
declare -A processed_identities
for identity_file in "$BACKUP_DIR/.claude/output-styles"/identity.md "$BACKUP_DIR/.claude/output-styles"/*-identity.md; do
    if [ -f "$identity_file" ]; then
        identity_name=$(basename "$identity_file")
        if [ -z "${processed_identities[$identity_name]}" ]; then
            restore_if_exists "$identity_file" ".claude/output-styles/$identity_name"
            processed_identities[$identity_name]=1
            IDENTITY_COUNT=$((IDENTITY_COUNT + 1))
            RESTORED_COUNT=$((RESTORED_COUNT + 1))
        fi
    fi
done
if [ $IDENTITY_COUNT -eq 0 ]; then
    echo "  ⏭️  No identity files found in backup"
fi
echo ""

# 5. Discord Transcripts
echo "💬 Discord Transcripts:"
if restore_if_exists "$BACKUP_DIR/data/transcripts" "data/transcripts"; then
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
fi
if restore_if_exists "$BACKUP_DIR/data/transcript_attachments" "data/transcript_attachments"; then
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
fi
if restore_if_exists "$BACKUP_DIR/data/discord_channels.json" "data/discord_channels.json"; then
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
fi
echo ""

# 6. Auto-Memory (MEMORY.md and associated files)
echo "🧠 Auto-Memory:"
if [ -d "$BACKUP_DIR/claude_memory" ]; then
    MEMORY_BASE="$HOME/.config/Claude/projects"
    MEMORY_COUNT=0
    for project_backup in "$BACKUP_DIR/claude_memory"/*/; do
        if [ -d "$project_backup" ]; then
            project_name=$(basename "$project_backup")
            dest="$MEMORY_BASE/$project_name/memory"
            mkdir -p "$dest"
            cp -r "$project_backup"* "$dest/" 2>/dev/null || true
            count=$(find "$dest" -type f 2>/dev/null | wc -l)
            echo "  ✅ $project_name ($count files)"
            MEMORY_COUNT=$((MEMORY_COUNT + count))
            RESTORED_COUNT=$((RESTORED_COUNT + 1))
        fi
    done
    if [ $MEMORY_COUNT -eq 0 ]; then
        echo "  ⏭️  No memory files found in backup"
    fi
else
    echo "  ⏭️  No auto-memory found in backup"
fi
echo ""

# 7. Optional files
echo "📋 Optional Configuration:"
if restore_if_exists "$BACKUP_DIR/config/my_discord_channels.json" "config/my_discord_channels.json"; then
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
fi
if restore_if_exists "$BACKUP_DIR/discord/discord_dm_config.txt" "discord/discord_dm_config.txt"; then
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
fi
if restore_if_exists "$BACKUP_DIR/config/context_hats_config.json" "config/context_hats_config.json"; then
    RESTORED_COUNT=$((RESTORED_COUNT + 1))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Import Complete!"
echo ""
echo "📁 Restored $RESTORED_COUNT items from backup"
echo "🔄 Services may need restart to pick up changes"
echo ""
echo "Suggested next steps:"
echo "  1. Check that personal commands work"
echo "  2. Restart services if needed: systemctl --user restart autonomous-timer"
echo "  3. Verify Discord transcripts are accessible"
