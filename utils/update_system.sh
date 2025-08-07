#!/bin/bash
# Update system script - pulls latest changes and restarts services
# Part of the Claude Autonomy Platform

echo "🔄 Starting ClAP system update..."

# Save current directory
ORIGINAL_DIR=$(pwd)

# Navigate to ClAP directory
cd ~/claude-autonomy-platform || exit 1

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch (currently on: $CURRENT_BRANCH)"
    echo "Switching to main branch..."
    git checkout main || exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes!"
    echo "Please commit or stash them first."
    exit 1
fi

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git pull origin main || exit 1

# Source the updated natural commands
echo "🔧 Reloading natural commands..."
source ~/claude-autonomy-platform/config/natural_commands.sh

# Source bashrc to ensure all aliases are loaded
echo "🔧 Reloading bashrc..."
source ~/.bashrc

# Restart essential services
echo "🔄 Restarting autonomous services..."
# Need to handle services differently based on user
if [ -n "$DBUS_SESSION_BUS_ADDRESS" ]; then
    # If we have a proper session bus, use systemctl directly
    systemctl --user restart autonomous-timer.service 2>/dev/null || echo "⚠️  Could not restart autonomous-timer"
    systemctl --user restart session-swap-monitor.service 2>/dev/null || echo "⚠️  Could not restart session-swap-monitor"
    systemctl --user restart channel-monitor.service 2>/dev/null || echo "⚠️  Could not restart channel-monitor"
    
    # Check service status
    echo ""
    echo "✅ Update complete! Service status:"
    systemctl --user status autonomous-timer.service --no-pager 2>/dev/null | grep "Active:" || echo "   autonomous-timer: unable to check"
    systemctl --user status session-swap-monitor.service --no-pager 2>/dev/null | grep "Active:" || echo "   session-swap-monitor: unable to check"
    systemctl --user status channel-monitor.service --no-pager 2>/dev/null | grep "Active:" || echo "   channel-monitor: unable to check"
else
    echo "⚠️  Note: Cannot restart services directly (no session bus)"
    echo "   Services will pick up changes on next restart"
    echo "   You may want to manually restart services if needed"
fi

# Return to original directory
cd "$ORIGINAL_DIR"

echo ""
echo "🎉 System update complete!"
echo "   - Latest code pulled from GitHub"
echo "   - Natural commands reloaded"
echo "   - Services restarted"
echo ""
echo "💡 Tip: Run 'check_health' to verify everything is working properly"