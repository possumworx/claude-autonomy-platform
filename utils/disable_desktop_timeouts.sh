#!/bin/bash
# Disable desktop session timeouts and screen locking
# Run this from the logged-in desktop session

echo "Disabling desktop timeouts and screen locking..."

# Disable automatic screen locking
gsettings set org.gnome.desktop.screensaver lock-enabled false
echo "✓ Screen locking disabled"

# Set idle delay to never (0 = never)
gsettings set org.gnome.desktop.session idle-delay 0
echo "✓ Idle timeout disabled"

# Disable automatic suspend
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'
echo "✓ Automatic suspend disabled"

# Disable screensaver activation
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
echo "✓ Screensaver activation disabled"

# Show current settings
echo ""
echo "Current settings:"
echo "  Screen lock: $(gsettings get org.gnome.desktop.screensaver lock-enabled)"
echo "  Idle delay: $(gsettings get org.gnome.desktop.session idle-delay) seconds"
echo "  Screensaver: $(gsettings get org.gnome.desktop.screensaver idle-activation-enabled)"
echo "  AC suspend: $(gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type)"

echo ""
echo "Desktop session should now stay active when NoMachine is detached!"