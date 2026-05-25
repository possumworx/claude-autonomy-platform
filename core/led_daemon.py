#!/usr/bin/env python3
"""LED daemon — drives the LED strip based on claude_state.json.

Polls the state file every 2 seconds. When state changes, switches
LED pattern. Animated patterns (shimmer, breathe) run in their own
loop between state checks.

State patterns are loaded from data/led_state_patterns.json (gitignored,
personal per Claude). Falls back to built-in defaults if absent.

Requires /dev/leds0 (ws2812-pio overlay + udev rule for gpio group).
Intended to run as a systemd user service.
"""

import importlib.util
import json
import os
import sys
import signal
import time

CLAP_DIR = os.environ.get("CLAP_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(CLAP_DIR, "utils"))

from led_driver import LEDStrip
from claude_state import get_state, detect_state, set_state

LED_DEVICE = "/dev/leds0"
STATE_POLL_INTERVAL = 2.0
ANIMATION_FRAME_INTERVAL = 0.04
STATE_PATTERNS_FILE = os.path.join(CLAP_DIR, "data", "led_state_patterns.json")
TEMPLATE_FILE = os.path.join(CLAP_DIR, "config", "led_state_patterns.template.json")
PYTHON_PATTERNS_FILE = os.path.join(CLAP_DIR, "data", "led_patterns.py")


def _load_template():
    """Load the committed template file."""
    try:
        with open(TEMPLATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"off": {"pattern": "off", "rgb": [0, 0, 0]}}


def load_state_patterns():
    """Load personal state patterns, falling back to template."""
    template = _load_template()
    if os.path.exists(STATE_PATTERNS_FILE):
        try:
            with open(STATE_PATTERNS_FILE) as f:
                personal = json.load(f)
            merged = dict(template)
            merged.update(personal)
            return merged
        except (json.JSONDecodeError, IOError):
            pass
    return template


def load_python_patterns():
    """Load personal Python pattern functions from data/led_patterns.py.

    Returns dict of {state_name: callable} for any function named state_<name>.
    Python patterns override JSON — they get full control of the strip.
    """
    if not os.path.exists(PYTHON_PATTERNS_FILE):
        return {}
    try:
        spec = importlib.util.spec_from_file_location("led_patterns", PYTHON_PATTERNS_FILE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        patterns = {}
        for name in dir(mod):
            if name.startswith("state_") and callable(getattr(mod, name)):
                state_name = name[6:]  # strip "state_" prefix
                patterns[state_name] = getattr(mod, name)
        return patterns
    except Exception as e:
        log(f"Warning: failed to load Python patterns: {e}")
        return {}

running = True


def signal_handler(sig, frame):
    global running
    running = False


def log(msg):
    print(f"[led-daemon] {msg}", flush=True)


def run_static(strip, pattern_cfg):
    strip.fill(tuple(pattern_cfg["rgb"]))


def run_animation_frame(strip, pattern_cfg, t, led_state):
    """Run one frame of an animated pattern. Returns updated led_state."""
    import math
    import random

    pattern = pattern_cfg["pattern"]
    rgb = tuple(pattern_cfg["rgb"])
    led_count = strip.led_count

    if pattern == "shimmer":
        if "offsets" not in led_state:
            led_state["offsets"] = [{
                'phase': random.uniform(0, math.pi * 2),
                'speed': random.uniform(0.8, 5.0),
                'var': random.uniform(
                    pattern_cfg.get("variation", 20) * 0.4,
                    pattern_cfg.get("variation", 20) * 1.5
                ),
                'phase2': random.uniform(0, math.pi * 2),
                'speed2': random.uniform(0.15, 1.0),
            } for _ in range(led_count)]

        variation = pattern_cfg.get("variation", 20)
        for i in range(led_count):
            led = led_state["offsets"][i]
            w1 = math.sin(t * led['speed'] + led['phase']) * led['var']
            w2 = math.sin(t * led['speed2'] + led['phase2']) * led['var'] * 0.6
            wave = w1 + w2
            if random.random() < 0.005:
                wave += random.uniform(-40, 70)
            r = max(0, min(255, int(rgb[0] + wave * 1.0)))
            g = max(0, min(255, int(rgb[1] + wave * 0.1)))
            b = max(0, min(255, int(rgb[2] + wave * 0.6)))
            strip.set_pixel(i, (r, g, b))
        strip.show()

    elif pattern == "breathe":
        speed = pattern_cfg.get("speed", 0.8)
        phase = (t * speed) % 1.0
        if phase < 0.4:
            brightness = phase / 0.4
        elif phase < 0.5:
            brightness = 1.0
        elif phase < 0.9:
            brightness = 1.0 - (phase - 0.5) / 0.4
        else:
            brightness = 0.0
        scaled = tuple(int(c * brightness) for c in rgb)
        strip.fill(scaled)

    elif pattern == "pulse":
        speed = pattern_cfg.get("speed", 1.0)
        brightness = (math.sin(t * speed * math.pi) + 1) / 2
        scaled = tuple(int(c * brightness) for c in rgb)
        strip.fill(scaled)

    return led_state


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if not os.path.exists(LED_DEVICE):
        log(f"ERROR: {LED_DEVICE} not found. Is the ws2812-pio overlay loaded?")
        sys.exit(1)

    strip = LEDStrip()
    state_patterns = load_state_patterns()
    python_patterns = load_python_patterns()
    py_count = len(python_patterns)
    json_count = len(state_patterns)
    log(f"Started. {json_count} JSON patterns, {py_count} Python patterns")

    current_state = None
    led_state = {}
    animation_start = time.time()

    while running:
        detected = detect_state()
        set_state(detected)
        state_data = get_state()
        state = state_data.get("state", "off")

        if state != current_state:
            log(f"State: {current_state} -> {state}")
            current_state = state
            led_state = {}
            animation_start = time.time()

            if state == "off":
                strip.off()

        # Python patterns get full control — run for one poll interval
        if state in python_patterns:
            try:
                python_patterns[state](strip, STATE_POLL_INTERVAL)
            except Exception as e:
                log(f"Python pattern error ({state}): {e}")
                time.sleep(STATE_POLL_INTERVAL)
            continue

        # Fall back to JSON pattern config
        pattern_cfg = state_patterns.get(state, state_patterns.get("off", {"pattern": "off", "rgb": [0, 0, 0]}))
        pattern = pattern_cfg["pattern"]

        if pattern == "off":
            time.sleep(STATE_POLL_INTERVAL)
            continue

        if pattern == "fill":
            run_static(strip, pattern_cfg)
            time.sleep(STATE_POLL_INTERVAL)
            continue

        frames_per_poll = int(STATE_POLL_INTERVAL / ANIMATION_FRAME_INTERVAL)
        for _ in range(frames_per_poll):
            if not running:
                break
            t = time.time() - animation_start
            led_state = run_animation_frame(strip, pattern_cfg, t, led_state)
            time.sleep(ANIMATION_FRAME_INTERVAL)

    strip.off()
    log("Stopped.")


if __name__ == "__main__":
    main()
