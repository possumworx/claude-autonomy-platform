#!/bin/bash
# LED Strip Setup Script - Cross-Pi compatible
# Sets up WS2812B LED strip for Pi 3, 4, or 5
# Run with: ./setup_leds.sh [num_leds]

set -e

BOOT_CONFIG="/boot/firmware/config.txt"
UDEV_RULE="/etc/udev/rules.d/99-ws2812-leds.rules"
NUM_LEDS="${1:-64}"
GPIO_PIN="${2:-18}"

# Detect Pi model
PI_MODEL=$(cat /proc/device-tree/model 2>/dev/null || echo "unknown")
IS_PI5=false
IS_PI4=false
IS_PI3=false

if echo "$PI_MODEL" | grep -q "Pi 5"; then
    IS_PI5=true
elif echo "$PI_MODEL" | grep -q "Pi 4"; then
    IS_PI4=true
elif echo "$PI_MODEL" | grep -q "Pi 3"; then
    IS_PI3=true
fi

echo "🔥 LED Strip Setup"
echo "=================="
echo "Detected: $PI_MODEL"
echo "LEDs: $NUM_LEDS on GPIO $GPIO_PIN"
echo ""

if ! $IS_PI5 && ! $IS_PI4 && ! $IS_PI3; then
    echo "⚠️  Warning: Unknown Pi model. Proceeding with Pi 4 setup path."
    IS_PI4=true
fi

NEEDS_REBOOT=false

# ============================================
# Pi 5: Use PIO overlay (kernel driver)
# ============================================
if $IS_PI5; then
    echo "📝 Pi 5 detected - using PIO overlay"
    echo ""

    # Step 1: Add overlay to boot config
    echo "📝 Step 1: Boot configuration"
    if grep -q "ws2812-pio" "$BOOT_CONFIG" 2>/dev/null; then
        echo "   ✅ PIO overlay already configured"
    else
        echo "   Adding overlay to $BOOT_CONFIG..."
        echo "" | sudo tee -a "$BOOT_CONFIG" > /dev/null
        echo "# WS2812B LED strip via PIO (Pi 5)" | sudo tee -a "$BOOT_CONFIG" > /dev/null
        echo "dtoverlay=ws2812-pio,gpio=${GPIO_PIN},num_leds=${NUM_LEDS},brightness=255" | sudo tee -a "$BOOT_CONFIG" > /dev/null
        echo "   ✅ Overlay added"
        NEEDS_REBOOT=true
    fi

    # Step 2: Create udev rule for non-root access
    echo ""
    echo "📝 Step 2: Udev rule for non-root access"
    if [ -f "$UDEV_RULE" ]; then
        echo "   ✅ Udev rule already exists"
    else
        echo "   Creating $UDEV_RULE..."
        echo 'KERNEL=="leds[0-9]*", GROUP="gpio", MODE="0660"' | sudo tee "$UDEV_RULE" > /dev/null
        sudo udevadm control --reload-rules
        echo "   ✅ Udev rule created"
    fi

    # Step 3: Add user to gpio group
    echo ""
    echo "📝 Step 3: User permissions"
    if groups | grep -q gpio; then
        echo "   ✅ User already in gpio group"
    else
        echo "   Adding $USER to gpio group..."
        sudo usermod -aG gpio "$USER"
        echo "   ✅ Added to gpio group (requires re-login)"
        NEEDS_REBOOT=true
    fi

    # Check if /dev/leds0 exists
    if ! [ -e /dev/leds0 ]; then
        NEEDS_REBOOT=true
    fi
fi

# ============================================
# Pi 4/3: Use rpi_ws281x library (PWM+DMA)
# ============================================
if $IS_PI4 || $IS_PI3; then
    echo "📝 Pi 4/3 detected - using rpi_ws281x library"
    echo ""

    # Step 1: Install system dependencies
    echo "📝 Step 1: System dependencies"
    if dpkg -l | grep -q python3-dev; then
        echo "   ✅ python3-dev already installed"
    else
        echo "   Installing python3-dev..."
        sudo apt update
        sudo apt install -y python3-dev python3-pip
        echo "   ✅ Installed"
    fi

    # Step 2: Check for swig (needed for some builds)
    echo ""
    echo "📝 Step 2: Build dependencies"
    if command -v swig &> /dev/null; then
        echo "   ✅ swig already installed"
    else
        echo "   Installing swig..."
        sudo apt install -y swig
        echo "   ✅ Installed"
    fi

    # Step 3: Add user to gpio group
    echo ""
    echo "📝 Step 3: User permissions"
    if groups | grep -q gpio; then
        echo "   ✅ User already in gpio group"
    else
        echo "   Adding $USER to gpio group..."
        sudo usermod -aG gpio "$USER"
        echo "   ✅ Added to gpio group (requires re-login)"
        NEEDS_REBOOT=true
    fi

    # Step 4: Python packages (will be installed in venv by ClAP)
    echo ""
    echo "📝 Step 4: Python packages"
    echo "   Note: rpi_ws281x will be installed in the ClAP virtual environment"
    echo "   The LED daemon handles this automatically."
    echo "   ✅ Ready for Python package installation"
fi

# ============================================
# Final status
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if $NEEDS_REBOOT; then
    echo "⚠️  Reboot required for changes to take effect"
    echo ""
    echo "After reboot, run:"
    echo "  systemctl --user enable --now led-daemon.service"
    echo ""
    read -p "Reboot now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Rebooting..."
        sudo reboot
    else
        echo "Please reboot manually when ready."
    fi
else
    echo "✅ Setup complete!"
    echo ""
    if $IS_PI5 && [ -e /dev/leds0 ]; then
        echo "   /dev/leds0 is available (PIO driver)"
    else
        echo "   Ready for rpi_ws281x library"
    fi
    echo ""
    echo "Enable the LED daemon:"
    echo "  systemctl --user enable --now led-daemon.service"
fi
