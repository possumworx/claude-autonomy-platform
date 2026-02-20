#!/bin/bash
# Export Personal ClAP Preferences & Configuration
# Backs up all personal (non-repo) files so a fresh pull can be done safely

set -e

# Get ClAP directory
CLAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CLAP_DIR"

# Create timestamped export directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EXPORT_DIR="$HOME/clap_personal_backup_${TIMESTAMP}"
mkdir -p "$EXPORT_DIR"

echo "🍊 Exporting Personal ClAP Preferences"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Export to: $EXPORT_DIR"
echo ""

# Function to copy with directory structure
copy_if_exists() {
    local source="$1"
    local dest_base="$2"

    if [ -e "$source" ]; then
        local dest="$dest_base/$(basename "$source")"
        mkdir -p "$(dirname "$dest")"

        if [ -d "$source" ]; then
            cp -r "$source" "$dest"
            count=$(find "$dest" -type f | wc -l)
            echo "  ✅ $(basename "$source")/ ($count files)"
        else
            cp "$source" "$dest"
            size=$(du -h "$source" | cut -f1)
            echo "  ✅ $(basename "$source") ($size)"
        fi
        return 0
    else
        echo "  ⏭️  $(basename "$source") (not found, skipping)"
        return 1
    fi
}

# Export manifest
MANIFEST="$EXPORT_DIR/MANIFEST.txt"
echo "ClAP Personal Preferences Export" > "$MANIFEST"
echo "Created: $(date)" >> "$MANIFEST"
echo "From: $CLAP_DIR" >> "$MANIFEST"
echo "User: $USER" >> "$MANIFEST"
echo "Host: $HOSTNAME" >> "$MANIFEST"
echo "" >> "$MANIFEST"
echo "Files included:" >> "$MANIFEST"

# 1. Personal Commands
echo "📝 Personal Commands:"
mkdir -p "$EXPORT_DIR/config"
if copy_if_exists "config/personal_commands.sh" "$EXPORT_DIR/config"; then
    echo "  config/personal_commands.sh" >> "$MANIFEST"
fi
echo ""

# 2. Infrastructure Config
echo "⚙️  Infrastructure Config:"
if copy_if_exists "config/claude_infrastructure_config.txt" "$EXPORT_DIR/config"; then
    echo "  config/claude_infrastructure_config.txt" >> "$MANIFEST"
fi
echo ""

# 3. Personal Skills (those WITHOUT _ prefix - core skills have _)
echo "🎯 Personal Skills:"
mkdir -p "$EXPORT_DIR/.claude/skills"
SKILL_COUNT=0
for skill_path in .claude/skills/*; do
    if [ -d "$skill_path" ]; then
        skill_name=$(basename "$skill_path")
        # Skip core skills (those starting with _)
        if [[ ! "$skill_name" =~ ^_ ]]; then
            cp -r "$skill_path" "$EXPORT_DIR/.claude/skills/"
            echo "  ✅ $skill_name"
            echo "  .claude/skills/$skill_name/" >> "$MANIFEST"
            SKILL_COUNT=$((SKILL_COUNT + 1))
        fi
    fi
done
if [ $SKILL_COUNT -eq 0 ]; then
    echo "  ⏭️  No personal skills found"
fi
echo ""

# 4. Identity/Output Styles
echo "🆔 Identity Configuration:"
mkdir -p "$EXPORT_DIR/.claude/output-styles"
IDENTITY_COUNT=0
# Use associative array to track already processed files
declare -A processed_identities
for identity_file in .claude/output-styles/*-identity.md; do
    if [ -f "$identity_file" ]; then
        identity_name=$(basename "$identity_file")
        if [ -z "${processed_identities[$identity_name]}" ]; then
            cp "$identity_file" "$EXPORT_DIR/.claude/output-styles/"
            size=$(du -h "$identity_file" | cut -f1)
            echo "  ✅ $identity_name ($size)"
            echo "  .claude/output-styles/$identity_name" >> "$MANIFEST"
            processed_identities[$identity_name]=1
            IDENTITY_COUNT=$((IDENTITY_COUNT + 1))
        fi
    fi
done
if [ $IDENTITY_COUNT -eq 0 ]; then
    echo "  ⏭️  No identity files found"
fi
echo ""

# 5. Discord Transcripts
echo "💬 Discord Transcripts:"
mkdir -p "$EXPORT_DIR/data"
if copy_if_exists "data/transcripts" "$EXPORT_DIR/data"; then
    echo "  data/transcripts/" >> "$MANIFEST"
fi
if copy_if_exists "data/transcript_attachments" "$EXPORT_DIR/data"; then
    echo "  data/transcript_attachments/" >> "$MANIFEST"
fi
if copy_if_exists "data/discord_channels.json" "$EXPORT_DIR/data"; then
    echo "  data/discord_channels.json" >> "$MANIFEST"
fi
echo ""

# 6. Optional files (may not exist for all users)
echo "📋 Optional Configuration:"
if copy_if_exists "config/my_discord_channels.json" "$EXPORT_DIR/config"; then
    echo "  config/my_discord_channels.json" >> "$MANIFEST"
fi
if copy_if_exists "discord/discord_dm_config.txt" "$EXPORT_DIR/discord"; then
    echo "  discord/discord_dm_config.txt" >> "$MANIFEST"
fi
if copy_if_exists "config/context_hats_config.json" "$EXPORT_DIR/config"; then
    echo "  config/context_hats_config.json" >> "$MANIFEST"
fi
echo ""

# Create compressed archive for easy transfer
echo "📦 Creating compressed archive..."
cd "$HOME"
ARCHIVE_NAME="clap_personal_backup_${TIMESTAMP}.tar.gz"
tar -czf "$ARCHIVE_NAME" "$(basename "$EXPORT_DIR")"
ARCHIVE_SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)
echo "  ✅ $ARCHIVE_NAME ($ARCHIVE_SIZE)"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Export Complete!"
echo ""
echo "📁 Backup directory: $EXPORT_DIR"
echo "📦 Archive: $HOME/$ARCHIVE_NAME"
echo "📋 Manifest: $MANIFEST"
echo ""
echo "To restore, use: ./utils/import_personal_prefs.sh $EXPORT_DIR"
echo "Or extract archive: tar -xzf ~/$ARCHIVE_NAME"
