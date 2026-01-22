#!/bin/bash
# Install Claude Auto-Resume service
# Automatically restarts Claude Code in tmux after system reboots

set -e

# Get the username
USER=$(whoami)
SERVICE_NAME="claude-auto-resume"
SERVICE_FILE="${SERVICE_NAME}.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Claude Auto-Resume service for user: $USER"

# Make sure the auto-resume script is executable
chmod +x "$SCRIPT_DIR/../core/claude_auto_resume.sh"

# Copy service file to user systemd directory
mkdir -p ~/.config/systemd/user/
cp "$SCRIPT_DIR/$SERVICE_FILE" ~/.config/systemd/user/

# Reload systemd daemon
systemctl --user daemon-reload

# Enable the service (so it runs on boot)
systemctl --user enable $SERVICE_NAME

echo ""
echo "✅ Claude Auto-Resume service installed and enabled!"
echo ""
echo "The service will run automatically after system reboots."
echo "It checks the RESTART_AFTER_REBOOT setting in config/claude_infrastructure_config.txt"
echo ""
echo "Useful commands:"
echo "  systemctl --user status $SERVICE_NAME    # Check status"
echo "  systemctl --user start $SERVICE_NAME     # Test manually"
echo "  journalctl --user -u $SERVICE_NAME       # View logs"
echo "  cat ~/claude-autonomy-platform/logs/auto_resume.log  # Check script logs"
echo ""
echo "To disable auto-resume, set RESTART_AFTER_REBOOT=false in config or run:"
echo "  systemctl --user disable $SERVICE_NAME"
