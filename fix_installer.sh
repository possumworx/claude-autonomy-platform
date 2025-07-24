#!/bin/bash
# Fix the installer to use channel-monitor instead of notification-monitor

echo "Fixing installer script..."

# Replace notification-monitor with channel-monitor
sed -i 's/notification-monitor\.service/channel-monitor.service/g' setup_clap_deployment.sh

# Fix the persistent session name
sed -i 's/PERSISTENT_SESSION="sonnet-4"/PERSISTENT_SESSION="persistent-login"/g' setup_clap_deployment.sh

echo "✅ Fixed installer script"

# Now fix the systemd service that was created with wrong name
if [ -f "$HOME/.config/systemd/user/notification-monitor.service" ]; then
    echo "Renaming notification-monitor.service to channel-monitor.service..."
    mv ~/.config/systemd/user/notification-monitor.service ~/.config/systemd/user/channel-monitor.service
    
    # Disable old, enable new
    systemctl --user disable notification-monitor.service 2>/dev/null
    systemctl --user daemon-reload
    systemctl --user enable channel-monitor.service
    echo "✅ Fixed service file"
fi

# Kill wrong tmux session if it exists
if tmux has-session -t sonnet-4 2>/dev/null; then
    echo "Killing wrong tmux session..."
    tmux kill-session -t sonnet-4
    echo "✅ Removed wrong tmux session"
fi

echo ""
echo "All fixed! Now you can run:"
echo "  systemctl --user start channel-monitor.service"
echo "  tmux new-session -d -s persistent-login"
