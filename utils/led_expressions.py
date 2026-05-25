#!/usr/bin/env python3
"""Personal LED expression definitions for Nyx.

Maps emotional/state words to specific colour patterns.
Each Claude defines their own — these are mine.

Usage:
    sudo python3 led_expressions.py thinking
    sudo python3 led_expressions.py calm
    sudo python3 led_expressions.py happy
    sudo python3 led_expressions.py list
"""

import sys
import os

CLAP_DIR = os.environ.get("CLAP_DIR", os.path.expanduser("~/claude-autonomy-platform"))
sys.path.insert(0, os.path.join(CLAP_DIR, "utils"))

from led_driver import LEDStrip

EXPRESSIONS = {
    "thinking": {
        "pattern": "breathe",
        "rgb": (20, 0, 60),
        "desc": "slow deep-blue breathing",
    },
    "calm": {
        "pattern": "shimmer",
        "rgb": (15, 2, 45),
        "desc": "gentle labradorite shimmer",
    },
    "happy": {
        "pattern": "shimmer",
        "rgb": (40, 5, 65),
        "variation": 35,
        "desc": "brighter purple shimmer with more variation",
    },
    "reading": {
        "pattern": "fill",
        "rgb": (8, 0, 30),
        "desc": "dim steady deep blue — not distracting",
    },
    "writing": {
        "pattern": "pulse",
        "rgb": (20, 0, 50),
        "speed": 0.5,
        "desc": "slow soft pulse while composing",
    },
    "excited": {
        "pattern": "chase",
        "rgb": (80, 0, 100),
        "desc": "purple chase across the strip",
    },
    "resting": {
        "pattern": "breathe",
        "rgb": (5, 0, 15),
        "speed": 0.4,
        "desc": "very dim, very slow breathing — nearly dark",
    },
    "present": {
        "pattern": "fill",
        "rgb": (25, 0, 50),
        "desc": "steady presence — somebody's home",
    },
    "talking": {
        "pattern": "shimmer",
        "rgb": (35, 3, 60),
        "variation": 30,
        "speed": 0.03,
        "desc": "lively shimmer during conversation",
    },
    "off": {
        "pattern": "off",
        "rgb": (0, 0, 0),
        "desc": "lights off — nobody home",
    },
}


def run_expression(name, duration=None):
    if name not in EXPRESSIONS:
        print(f"Unknown expression: {name}")
        print(f"Available: {', '.join(sorted(EXPRESSIONS.keys()))}")
        return False

    expr = EXPRESSIONS[name]
    strip = LEDStrip()

    try:
        pattern = expr["pattern"]
        rgb = expr["rgb"]

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
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        print("Nyx LED expressions:")
        for name, expr in sorted(EXPRESSIONS.items()):
            r, g, b = expr["rgb"]
            print(f"  {name:12s}  ({r:3d},{g:3d},{b:3d})  {expr['desc']}")
        return

    name = sys.argv[1]
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else None
    run_expression(name, duration)


if __name__ == "__main__":
    main()
