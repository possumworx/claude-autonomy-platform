#!/usr/bin/env python3
"""LED strip driver for WS2812B on Raspberry Pi 5 via PIO.

Uses the kernel ws2812-pio-rp1 driver which exposes /dev/leds0.
The device tree overlay must be loaded first:
    sudo dtoverlay ws2812-pio gpio=18 num_leds=64 brightness=40

Pixel data is written as raw GRB bytes to /dev/leds0.
Must run as root (device file permissions).

Usage as library:
    from led_driver import LEDStrip
    strip = LEDStrip()
    strip.fill((0, 0, 128))
    strip.off()

Usage from CLI:
    sudo python3 led_driver.py fill 0 0 128
    sudo python3 led_driver.py off
    sudo python3 led_driver.py test
    sudo python3 led_driver.py gradient 0,0,80 60,0,120
    sudo python3 led_driver.py pulse 0 0 128
    sudo python3 led_driver.py breathe 20 0 60
"""

import sys
import os
import time
import math
import signal

LED_COUNT = 64
LED_DEVICE = "/dev/leds0"
LED_BRIGHTNESS = 255  # software brightness — overlay handles hardware brightness


class LEDStrip:
    def __init__(self, brightness=LED_BRIGHTNESS, led_count=LED_COUNT,
                 device=LED_DEVICE):
        self.led_count = led_count
        self._brightness = brightness
        self._pixels = [(0, 0, 0)] * led_count
        self._device = device

        if not os.path.exists(device):
            raise RuntimeError(
                f"{device} not found. Load overlay first:\n"
                "  sudo dtoverlay ws2812-pio gpio=18 num_leds=64 brightness=40"
            )

    def _scale(self, val):
        return int(val * self._brightness / 255)

    def set_pixel(self, n, rgb):
        if 0 <= n < self.led_count:
            self._pixels[n] = rgb

    def fill(self, rgb):
        for i in range(self.led_count):
            self._pixels[i] = rgb
        self.show()

    def show(self):
        buf = bytearray(self.led_count * 4)
        for i, (r, g, b) in enumerate(self._pixels):
            buf[i * 4] = self._scale(r)
            buf[i * 4 + 1] = self._scale(g)
            buf[i * 4 + 2] = self._scale(b)
            # byte 3 = padding (unused for RGB strips, white for RGBW)
        with open(self._device, "wb") as f:
            f.write(buf)

    def off(self):
        self._pixels = [(0, 0, 0)] * self.led_count
        self.show()

    def set_brightness(self, val):
        self._brightness = max(0, min(255, val))
        self.show()

    def gradient(self, start_rgb, end_rgb):
        for i in range(self.led_count):
            t = i / max(1, self.led_count - 1)
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
            self.set_pixel(i, (r, g, b))
        self.show()

    def pulse(self, rgb, speed=1.0, duration=10.0):
        start = time.time()
        while time.time() - start < duration:
            t = time.time() - start
            brightness = (math.sin(t * speed * math.pi) + 1) / 2
            scaled = tuple(int(c * brightness) for c in rgb)
            self.fill(scaled)
            time.sleep(0.03)
        self.off()

    def breathe(self, rgb, speed=0.8, duration=10.0):
        start = time.time()
        while time.time() - start < duration:
            t = (time.time() - start) * speed
            phase = t % 1.0
            if phase < 0.4:
                brightness = phase / 0.4
            elif phase < 0.5:
                brightness = 1.0
            elif phase < 0.9:
                brightness = 1.0 - (phase - 0.5) / 0.4
            else:
                brightness = 0.0
            scaled = tuple(int(c * brightness) for c in rgb)
            self.fill(scaled)
            time.sleep(0.03)
        self.off()

    def chase(self, rgb, width=4, speed=0.05, duration=10.0):
        start = time.time()
        while time.time() - start < duration:
            for pos in range(self.led_count + width):
                if time.time() - start >= duration:
                    break
                for i in range(self.led_count):
                    dist = abs(i - pos + width // 2)
                    if dist < width:
                        fade = 1.0 - dist / width
                        self.set_pixel(i, tuple(int(c * fade) for c in rgb))
                    else:
                        self.set_pixel(i, (0, 0, 0))
                self.show()
                time.sleep(speed)
        self.off()

    def shimmer(self, base_rgb, variation=20, speed=0.04, duration=10.0):
        import random
        start = time.time()
        leds = [{
            'phase': random.uniform(0, math.pi * 2),
            'speed': random.uniform(0.8, 5.0),
            'var': random.uniform(variation * 0.4, variation * 1.5),
            'phase2': random.uniform(0, math.pi * 2),
            'speed2': random.uniform(0.15, 1.0),
        } for _ in range(self.led_count)]
        while time.time() - start < duration:
            t = time.time() - start
            for i in range(self.led_count):
                led = leds[i]
                w1 = math.sin(t * led['speed'] + led['phase']) * led['var']
                w2 = math.sin(t * led['speed2'] + led['phase2']) * led['var'] * 0.6
                wave = w1 + w2
                if random.random() < 0.005:
                    wave += random.uniform(-40, 70)
                r = max(0, min(255, int(base_rgb[0] + wave * 1.0)))
                g = max(0, min(255, int(base_rgb[1] + wave * 0.1)))
                b = max(0, min(255, int(base_rgb[2] + wave * 0.6)))
                self.set_pixel(i, (r, g, b))
            self.show()
            time.sleep(speed)
        self.off()

    def close(self):
        pass


def _parse_rgb(s):
    parts = s.split(",")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    strip = LEDStrip()

    def cleanup(*_):
        strip.off()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    cmd = sys.argv[1]

    if cmd == "off":
        strip.off()

    elif cmd == "fill":
        r, g, b = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
        strip.fill((r, g, b))

    elif cmd == "gradient":
        start = _parse_rgb(sys.argv[2])
        end = _parse_rgb(sys.argv[3])
        strip.gradient(start, end)

    elif cmd == "pulse":
        rgb = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
        duration = float(sys.argv[5]) if len(sys.argv) > 5 else 10.0
        strip.pulse(rgb, duration=duration)

    elif cmd == "breathe":
        rgb = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
        duration = float(sys.argv[5]) if len(sys.argv) > 5 else 10.0
        strip.breathe(rgb, duration=duration)

    elif cmd == "chase":
        rgb = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
        duration = float(sys.argv[5]) if len(sys.argv) > 5 else 10.0
        strip.chase(rgb, duration=duration)

    elif cmd == "shimmer":
        rgb = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
        duration = float(sys.argv[5]) if len(sys.argv) > 5 else 10.0
        strip.shimmer(rgb, duration=duration)

    elif cmd == "test":
        print("Testing LED strip — 64 LEDs via PIO (/dev/leds0)")
        print("Red...")
        strip.fill((255, 0, 0))
        time.sleep(1)
        print("Green...")
        strip.fill((0, 255, 0))
        time.sleep(1)
        print("Blue...")
        strip.fill((0, 0, 255))
        time.sleep(1)
        print("Deep labradorite blue...")
        strip.fill((10, 0, 60))
        time.sleep(1)
        print("Gradient: deep blue → purple...")
        strip.gradient((0, 0, 80), (60, 0, 120))
        time.sleep(2)
        print("Shimmer...")
        strip.shimmer((10, 0, 50), duration=5)
        print("Off.")
        strip.off()

    elif cmd == "brightness":
        strip.set_brightness(int(sys.argv[2]))

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
