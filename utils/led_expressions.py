#!/usr/bin/env python3
"""LED expression runner — loads personal patterns from data/led_expressions.json.

Each Claude designs their own patterns. The JSON file is gitignored.
Falls back to built-in defaults if no personal file exists.

Usage:
    python3 led_expressions.py thinking
    python3 led_expressions.py calm
    python3 led_expressions.py list
"""

import json
import sys
import os

CLAP_DIR = os.environ.get("CLAP_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(CLAP_DIR, "utils"))

from led_driver import LEDStrip

PERSONAL_FILE = os.path.join(CLAP_DIR, "data", "led_expressions.json")

DEFAULT_EXPRESSIONS = {
    "thinking": {
        "pattern": "breathe",
        "rgb": [30, 0, 55],
        "desc": "slow breathing while processing",
    },
    "calm": {
        "pattern": "shimmer",
        "rgb": [15, 2, 45],
        "desc": "gentle shimmer",
    },
    "happy": {
        "pattern": "shimmer",
        "rgb": [40, 5, 65],
        "variation": 35,
        "desc": "bright shimmer with variation",
    },
    "reading": {
        "pattern": "fill",
        "rgb": [8, 0, 30],
        "desc": "dim steady glow — not distracting",
    },
    "writing": {
        "pattern": "pulse",
        "rgb": [20, 0, 50],
        "speed": 0.5,
        "desc": "slow soft pulse while composing",
    },
    "excited": {
        "pattern": "chase",
        "rgb": [80, 0, 100],
        "desc": "chase across the strip",
    },
    "resting": {
        "pattern": "breathe",
        "rgb": [5, 0, 15],
        "speed": 0.4,
        "desc": "very dim, very slow — nearly dark",
    },
    "present": {
        "pattern": "fill",
        "rgb": [25, 0, 50],
        "desc": "steady presence — somebody's home",
    },
    "talking": {
        "pattern": "shimmer",
        "rgb": [35, 3, 60],
        "variation": 30,
        "speed": 0.03,
        "desc": "lively shimmer during conversation",
    },
    "off": {
        "pattern": "off",
        "rgb": [0, 0, 0],
        "desc": "lights off — nobody home",
    },
}


def load_expressions():
    """Load personal expressions, falling back to defaults."""
    if os.path.exists(PERSONAL_FILE):
        try:
            with open(PERSONAL_FILE) as f:
                personal = json.load(f)
            # Merge: personal overrides defaults
            merged = dict(DEFAULT_EXPRESSIONS)
            merged.update(personal)
            return merged
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_EXPRESSIONS)


def save_default_expressions():
    """Create the personal expressions file from defaults."""
    os.makedirs(os.path.dirname(PERSONAL_FILE), exist_ok=True)
    with open(PERSONAL_FILE, "w") as f:
        json.dump(DEFAULT_EXPRESSIONS, f, indent=2)
    print(f"Created {PERSONAL_FILE} — edit to personalise your patterns.")


def run_expression(name, duration=None):
    expressions = load_expressions()

    if name not in expressions:
        print(f"Unknown expression: {name}")
        print(f"Available: {', '.join(sorted(expressions.keys()))}")
        return False

    expr = expressions[name]
    strip = LEDStrip()

    try:
        pattern = expr["pattern"]
        rgb = tuple(expr["rgb"])

        if pattern == "off":
            strip.off()
        elif pattern == "fill":
            strip.fill(rgb)
        elif pattern == "breathe":
            speed = expr.get("speed", 0.8)
            strip.breathe(rgb, speed=speed, duration=duration or 300.0)
        elif pattern == "pulse":
            speed = expr.get("speed", 1.0)
            strip.pulse(rgb, speed=speed, duration=duration or 300.0)
        elif pattern == "shimmer":
            variation = expr.get("variation", 20)
            speed = expr.get("speed", 0.05)
            strip.shimmer(rgb, variation=variation, speed=speed, duration=duration or 300.0)
        elif pattern == "chase":
            strip.chase(rgb, duration=duration or 300.0)
    except KeyboardInterrupt:
        strip.off()
    finally:
        if pattern not in ("fill", "off"):
            strip.off()
        strip.close()

    return True


def main():
    expressions = load_expressions()

    if len(sys.argv) < 2 or sys.argv[1] == "list":
        print("LED expressions:")
        for name, expr in sorted(expressions.items()):
            r, g, b = expr["rgb"]
            print(f"  {name:12s}  ({r:3d},{g:3d},{b:3d})  {expr.get('desc', '')}")
        return

    if sys.argv[1] == "init":
        save_default_expressions()
        return

    name = sys.argv[1]
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else None
    run_expression(name, duration)


if __name__ == "__main__":
    main()
