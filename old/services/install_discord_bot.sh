#!/bin/bash
# Install Discord Status Bot service for Claude

set -e

# Get the username
USER=$(whoami)
SERVICE_NAME="discord-status-bot"
SERVICE_FILE="${SERVICE_NAME}.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Discord Status Bot service for user: $USER"

# Copy service file to user systemd directory
mkdir -p ~/.config/systemd/user/
cp "$SCRIPT_DIR/$SERVICE_FILE" ~/.config/systemd/user/

# Reload systemd daemon
systemctl --user daemon-reload

# Enable the service
systemctl --user enable $SERVICE_NAME

# Start the service
systemctl --user start $SERVICE_NAME

# Check status
systemctl --user status $SERVICE_NAME --no-pager

echo ""
echo "✅ Discord Status Bot service installed and started!"
echo ""
echo "Useful commands:"
echo "  systemctl --user status $SERVICE_NAME    # Check status"
echo "  systemctl --user restart $SERVICE_NAME   # Restart service"
echo "  systemctl --user stop $SERVICE_NAME      # Stop service"
echo "  journalctl --user -u $SERVICE_NAME -f    # View logs"