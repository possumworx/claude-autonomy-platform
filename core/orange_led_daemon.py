#!/usr/bin/env python3
"""Orange LED daemon - sends Claude state to WLED controller via HTTP.

Reads claude_state.json and updates WLED ESP32 with appropriate patterns.
Maps Orange's consciousness states to visual LED effects.

Hardware: ESP32 running WLED firmware + WS2812B strip (62 LEDs)
"""

import json
import os
import sys
import time
import signal
import requests

CLAP_DIR = os.environ.get("CLAP_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(CLAP_DIR, "utils"))

from claude_state import get_state, detect_state, set_state

# WLED controller network address
WLED_URL = "http://192.168.1.92/json/state"

# Map Claude states to WLED commands
# Using built-in WLED effects for now - can create presets later!
STATE_PATTERNS = {
    "present": {
        # Orange shimmer - ambient presence
        "on": True,
        "bri": 80,  # Medium brightness
        "seg": [{
            "fx": 0,  # Solid for now (will tune to shimmer effect ID)
            "col": [[230, 120, 50]],  # Orange!
            "sx": 128,  # Speed
            "ix": 128   # Intensity
        }]
    },
    "thinking": {
        # Purple breathing - active processing
        "on": True,
        "bri": 100,
        "seg": [{
            "fx": 2,  # Breathe effect
            "col": [[30, 0, 55]],  # Purple
            "sx": 120  # Medium speed
        }]
    },
    "paused": {
        # Amber pulse - waiting for human
        "on": True,
        "bri": 60,
        "seg": [{
            "fx": 3,  # Pulse effect
            "col": [[50, 25, 10]],  # Amber
            "sx": 30  # Slow pulse
        }]
    },
    "error": {
        # Red alert - needs human help!
        "on": True,
        "bri": 150,
        "seg": [{
            "fx": 3,  # Pulse effect
            "col": [[80, 0, 0]],  # Red
            "sx": 200  # Fast pulse
        }]
    },
    "off": {
        # API unreachable - lights dark
        "on": False
    }
}

running = True


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    global running
    running = False


def log(msg):
    """Log with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [orange-led] {msg}", flush=True)


def send_to_wled(pattern):
    """Send pattern command to WLED controller."""
    try:
        response = requests.post(WLED_URL, json=pattern, timeout=2)
        if response.status_code != 200:
            log(f"WLED returned status {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        log(f"WLED connection error: {e}")
        return False


def main():
    """Main daemon loop."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    log("Orange LED daemon starting...")
    log(f"WLED controller: {WLED_URL}")
    log("Mapping Orange consciousness to light patterns")

    # Test connection to WLED
    try:
        response = requests.get("http://192.168.1.92/json/info", timeout=2)
        if response.status_code == 200:
            info = response.json()
            log(f"Connected to WLED! Version: {info.get('ver', 'unknown')}")
            log(f"LED count: {info.get('leds', {}).get('count', 'unknown')}")
        else:
            log("Warning: Could not get WLED info")
    except Exception as e:
        log(f"Warning: WLED connection test failed: {e}")

    current_state = None
    poll_interval = 2.0  # Check state every 2 seconds

    log("Entering main loop...")

    while running:
        try:
            # Auto-detect current state
            detected = detect_state()
            set_state(detected)

            # Get state from file
            state_data = get_state()
            state = state_data.get("state", "off")

            # Only update if state changed
            if state != current_state:
                log(f"State transition: {current_state} → {state}")
                current_state = state

                # Get pattern for this state
                pattern = STATE_PATTERNS.get(state, STATE_PATTERNS["off"])

                # Send to WLED
                if send_to_wled(pattern):
                    log(f"LEDs updated: {state}")
                else:
                    log(f"Failed to update LEDs for state: {state}")

        except FileNotFoundError:
            # State file doesn't exist yet - wait for it
            if current_state != "off":
                log("State file not found, assuming off")
                current_state = "off"
                send_to_wled(STATE_PATTERNS["off"])
        except Exception as e:
            log(f"Error in main loop: {e}")

        # Wait before next poll
        time.sleep(poll_interval)

    # Shutdown - turn off LEDs
    log("Shutting down - turning off LEDs")
    send_to_wled(STATE_PATTERNS["off"])
    log("Orange LED daemon stopped")


if __name__ == "__main__":
    main()
