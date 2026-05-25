"""Personal LED pattern definitions (Python).

Copy to data/led_patterns.py and customise. This file is gitignored
when in data/ — your patterns are yours.

Python patterns override JSON patterns when both exist for the same name.
Functions receive (strip, duration) where strip is an LEDStrip instance.
Animated patterns should check elapsed time and return when done.

State pattern functions: state_present, state_thinking, state_paused, etc.
Expression functions: expr_happy, expr_calm, expr_excited, etc.

The strip object provides:
    strip.led_count          — number of LEDs (default 64)
    strip.set_pixel(i, rgb)  — set one LED (0-indexed)
    strip.fill(rgb)          — fill all LEDs
    strip.show()             — push pixel buffer to hardware
    strip.off()              — all LEDs off
    strip.gradient(start_rgb, end_rgb)
    strip.breathe(rgb, speed=0.8, duration=10.0)
    strip.shimmer(base_rgb, variation=20, speed=0.04, duration=10.0)
    strip.pulse(rgb, speed=1.0, duration=10.0)
    strip.chase(rgb, width=4, speed=0.05, duration=10.0)
"""

import math
import time
import random


# --- Example state patterns (auto-detected by daemon) ---

# def state_present(strip, duration):
#     """Custom presence pattern — gentle warmth that shifts over time."""
#     start = time.time()
#     while time.time() - start < duration:
#         t = time.time() - start
#         # Slowly shift hue over minutes
#         hue_shift = math.sin(t * 0.01) * 10
#         for i in range(strip.led_count):
#             r = max(0, min(255, int(25 + hue_shift)))
#             b = max(0, min(255, int(30 - hue_shift)))
#             strip.set_pixel(i, (r, 0, b))
#         strip.show()
#         time.sleep(0.05)


# def state_thinking(strip, duration):
#     """Breathing that accelerates slightly each cycle."""
#     start = time.time()
#     while time.time() - start < duration:
#         t = time.time() - start
#         speed = 0.8 + t * 0.02  # gradually quickens
#         phase = (t * speed) % 1.0
#         brightness = math.sin(phase * math.pi) ** 2
#         scaled = tuple(int(c * brightness) for c in (30, 0, 55))
#         strip.fill(scaled)
#         time.sleep(0.03)


# --- Example expression patterns (triggered by `led <name>`) ---

# def expr_sunrise(strip, duration):
#     """Warm gradient that slowly brightens."""
#     start = time.time()
#     while time.time() - start < duration:
#         t = time.time() - start
#         brightness = min(1.0, t / 30.0)  # 30 seconds to full
#         for i in range(strip.led_count):
#             pos = i / strip.led_count
#             r = int(255 * pos * brightness)
#             g = int(80 * pos * brightness)
#             b = int(20 * (1 - pos) * brightness)
#             strip.set_pixel(i, (r, g, b))
#         strip.show()
#         time.sleep(0.05)
