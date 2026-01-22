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

# Pull latest changes and sync deletions
echo "📥 Fetching latest changes from GitHub..."
git fetch --all || exit 1

echo "🧹 Syncing local with remote (including deletions)..."
git reset --hard origin/main || exit 1

# Ensure pre-commit hooks are set up
echo "🔐 Checking pre-commit setup..."
if ! command -v pre-commit &> /dev/null || [[ ! -f .git/hooks/pre-commit ]]; then
    echo "   Setting up pre-commit hooks..."
    bash setup/setup_pre_commit.sh || echo "⚠️  Pre-commit setup failed (non-critical)"
else
    echo "   ✅ Pre-commit already configured"
fi

# Update command symlinks to reflect any new/removed commands
echo "🔗 Updating command symlinks..."
bash ~/claude-autonomy-platform/utils/setup_natural_command_symlinks.sh > /dev/null 2>&1 || echo "⚠️  Symlink update failed (non-critical)"

# Source the updated natural commands
echo "🔧 Reloading natural commands..."
# shellcheck source=/dev/null
source ~/claude-autonomy-platform/config/natural_commands.sh

# Source bashrc to ensure all aliases are loaded
echo "🔧 Reloading bashrc..."
# shellcheck source=/dev/null
source ~/.bashrc

# Restart essential services
echo "🔄 Restarting autonomous services..."
# Need to handle services differently based on user
if [ -n "$DBUS_SESSION_BUS_ADDRESS" ]; then
    # If we have a proper session bus, use systemctl directly
    systemctl --user restart autonomous-timer.service 2>/dev/null || echo "⚠️  Could not restart autonomous-timer"
    systemctl --user restart session-swap-monitor.service 2>/dev/null || echo "⚠️  Could not restart session-swap-monitor"
    systemctl --user restart discord-transcript-fetcher.service 2>/dev/null || echo "⚠️  Could not restart discord-transcript-fetcher"

    # Check service status
    echo ""
    echo "✅ Update complete! Service status:"
    systemctl --user status autonomous-timer.service --no-pager 2>/dev/null | grep "Active:" || echo "   autonomous-timer: unable to check"
    systemctl --user status session-swap-monitor.service --no-pager 2>/dev/null | grep "Active:" || echo "   session-swap-monitor: unable to check"
    systemctl --user status discord-transcript-fetcher.service --no-pager 2>/dev/null | grep "Active:" || echo "   discord-transcript-fetcher: unable to check"
else
    echo "⚠️  Note: Cannot restart services directly (no session bus)"
    echo "   Services will pick up changes on next restart"
    echo "   You may want to manually restart services if needed"
fi

# Return to original directory
cd "$ORIGINAL_DIR" || exit

echo ""
echo "🎉 System update complete!"
echo "   - Latest code pulled from GitHub"
echo "   - Command symlinks updated"
echo "   - Natural commands reloaded"
echo "   - Services restarted"
echo ""
echo "💡 Tip: Run 'check_health' to verify everything is working properly"
