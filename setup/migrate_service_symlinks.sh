#!/bin/bash
# Migrate systemd service files from copies to symlinks
# Run this after pulling the services/ → systemd/ consolidation
#
# What this does:
#   1. Stops all ClAP services
#   2. Replaces copied service files with symlinks to systemd/
#   3. Reloads systemd and restarts services
#
# Safe to run multiple times — symlinks are idempotent.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$(dirname "$SCRIPT_DIR")"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "🔄 Migrating ClAP service files to symlinks..."
echo "   ClAP directory: $CLAP_DIR"
echo "   Systemd user dir: $SYSTEMD_USER_DIR"
echo ""

# Check systemd dir exists
if [[ ! -d "$SYSTEMD_USER_DIR" ]]; then
    echo "❌ $SYSTEMD_USER_DIR does not exist. Nothing to migrate."
    exit 1
fi

# Check source directory exists
if [[ ! -d "$CLAP_DIR/systemd" ]]; then
    echo "❌ $CLAP_DIR/systemd/ does not exist. Have you pulled the latest changes?"
    exit 1
fi

# Stop services first
echo "⏸️  Stopping ClAP services..."
for service_file in "$CLAP_DIR/systemd"/*.service; do
    if [[ -f "$service_file" ]]; then
        service_name=$(basename "$service_file")
        systemctl --user stop "$service_name" 2>/dev/null || true
    fi
done

# Replace copies with symlinks
echo ""
echo "🔗 Creating symlinks..."
MIGRATED=0
for service_file in "$CLAP_DIR/systemd"/*.service; do
    if [[ -f "$service_file" ]]; then
        service_name=$(basename "$service_file")
        target="$SYSTEMD_USER_DIR/$service_name"

        if [[ -L "$target" ]] && [[ "$(readlink -f "$target")" == "$(readlink -f "$service_file")" ]]; then
            echo "   ✓ $service_name (already a symlink)"
        else
            ln -sf "$service_file" "$target"
            echo "   ✅ $service_name → symlinked"
            MIGRATED=$((MIGRATED + 1))
        fi
    fi
done

# Also symlink timer files
for timer_file in "$CLAP_DIR/systemd"/*.timer; do
    if [[ -f "$timer_file" ]]; then
        timer_name=$(basename "$timer_file")
        target="$SYSTEMD_USER_DIR/$timer_name"

        if [[ -L "$target" ]] && [[ "$(readlink -f "$target")" == "$(readlink -f "$timer_file")" ]]; then
            echo "   ✓ $timer_name (already a symlink)"
        else
            ln -sf "$timer_file" "$target"
            echo "   ✅ $timer_name → symlinked"
            MIGRATED=$((MIGRATED + 1))
        fi
    fi
done

# Reload and restart
echo ""
echo "🔄 Reloading systemd..."
systemctl --user daemon-reload

echo "▶️  Restarting services..."
for service_file in "$CLAP_DIR/systemd"/*.service; do
    if [[ -f "$service_file" ]]; then
        service_name=$(basename "$service_file")
        if systemctl --user is-enabled "$service_name" 2>/dev/null | grep -q "enabled"; then
            systemctl --user start "$service_name"
            echo "   ▶️  $service_name started"
        else
            echo "   ⏭️  $service_name (not enabled, skipping)"
        fi
    fi
done

echo ""
echo "✅ Migration complete! $MIGRATED file(s) converted to symlinks."
echo "   Run 'check_health' to verify services are running."
