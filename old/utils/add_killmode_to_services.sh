#!/bin/bash
# Add KillMode=process to systemd user services
# Safe to run multiple times - only adds if missing

set -e

SERVICE_DIR="$HOME/.config/systemd/user"
SERVICES=("autonomous-timer.service" "session-swap-monitor.service" "discord-status-bot.service")

echo "🔧 Adding KillMode=process to systemd services..."
echo ""

for service in "${SERVICES[@]}"; do
    service_path="$SERVICE_DIR/$service"

    if [[ ! -f "$service_path" ]]; then
        echo "⚠️  Skipping $service - file not found"
        continue
    fi

    # Check if KillMode already exists
    if grep -q "^KillMode=" "$service_path"; then
        echo "✅ $service - KillMode already set"
        continue
    fi

    # Find the line with StandardError=journal and add KillMode after it
    if grep -q "StandardError=journal" "$service_path"; then
        # Create backup
        cp "$service_path" "$service_path.backup-$(date +%s)"

        # Add KillMode=process after StandardError=journal
        sed -i '/StandardError=journal/a KillMode=process' "$service_path"

        echo "✅ $service - Added KillMode=process"
    else
        echo "⚠️  $service - Could not find StandardError=journal line, skipping"
    fi
done

echo ""
echo "🔄 Reloading systemd daemon..."
systemctl --user daemon-reload

echo ""
echo "✅ Done! Service files have been updated."
echo ""
echo "To verify the changes:"
echo "  systemctl --user show autonomous-timer.service -p KillMode"
echo "  systemctl --user show session-swap-monitor.service -p KillMode"
echo "  systemctl --user show discord-status-bot.service -p KillMode"
echo ""
echo "To restart services (safe now - won't kill tmux!):"
echo "  systemctl --user restart autonomous-timer.service session-swap-monitor.service discord-status-bot.service"
