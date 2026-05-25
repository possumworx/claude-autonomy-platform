#!/usr/bin/env python3
"""LED expression runner — loads personal patterns from data/led_expressions.json.

Each Claude designs their own patterns. The personal JSON file is gitignored.
Template at config/led_expressions.template.json (committed, shared starting point).
Falls back to template if no personal file exists.

Usage:
    python3 led_expressions.py thinking
    python3 led_expressions.py list
    python3 led_expressions.py init    # create personal file from template
"""

import json
import sys
import os

CLAP_DIR = os.environ.get("CLAP_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(CLAP_DIR, "utils"))

from led_driver import LEDStrip

PERSONAL_FILE = os.path.join(CLAP_DIR, "data", "led_expressions.json")
TEMPLATE_FILE = os.path.join(CLAP_DIR, "config", "led_expressions.template.json")


def _load_template():
    """Load the committed template file."""
    try:
        with open(TEMPLATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_expressions():
    """Load personal expressions, falling back to template."""
    template = _load_template()
    if os.path.exists(PERSONAL_FILE):
        try:
            with open(PERSONAL_FILE) as f:
                personal = json.load(f)
            merged = dict(template)
            merged.update(personal)
            return merged
        except (json.JSONDecodeError, IOError):
            pass
    return template


def save_default_expressions():
    """Create the personal expressions file from template."""
    template = _load_template()
    os.makedirs(os.path.dirname(PERSONAL_FILE), exist_ok=True)
    with open(PERSONAL_FILE, "w") as f:
        json.dump(template, f, indent=2)
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
