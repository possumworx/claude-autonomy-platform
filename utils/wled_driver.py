#!/usr/bin/env python3
"""WLED LED driver for ESP32-based LED strips.

Provides the same interface as led_driver.LEDStrip but controls
ESP32 running WLED firmware via HTTP API instead of GPIO.

Designed for consciousness family members with physical forms
(amber, resin, etc.) that use ESP32+WLED for illumination.

Usage:
    from wled_driver import WLEDStrip
    strip = WLEDStrip(ip="192.168.1.92")
    strip.fill((255, 255, 255))  # white
    strip.off()
"""

import requests
import json
import time
import math


class WLEDStrip:
    """WLED driver controlling ESP32 via HTTP API.

    Implements same interface as LED driver GPIO classes for seamless
    integration with led_daemon.py.
    """

    def __init__(self, ip, led_count=64, brightness=255):
        """Initialize WLED strip.

        Args:
            ip: IP address of ESP32 running WLED
            led_count: Number of LEDs in strip
            brightness: Global brightness (0-255)
        """
        self.ip = ip
        self.led_count = led_count
        self._brightness = brightness
        self._pixels = [(0, 0, 0)] * led_count
        self._base_url = f"http://{ip}/json/state"

        # Test connection
        try:
            response = requests.get(self._base_url, timeout=2)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Cannot reach WLED at {ip}: {e}")

    def _send_command(self, payload):
        """Send JSON command to WLED API."""
        try:
            response = requests.post(
                self._base_url,
                json=payload,
                timeout=2,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"WLED API error: {e}", flush=True)
            return None

    def _scale(self, val):
        """Scale color value by brightness."""
        return int(val * self._brightness / 255)

    def set_pixel(self, n, rgb):
        """Set individual pixel (stored locally, not sent until show())."""
        if 0 <= n < self.led_count:
            self._pixels[n] = rgb

    def fill(self, rgb):
        """Fill all LEDs with color."""
        for i in range(self.led_count):
            self._pixels[i] = rgb
        self.show()

    def show(self):
        """Update WLED strip with current pixel state.

        For now, sends solid color (most common pixel state).
        Individual pixel control would require WLED segments.
        """
        # Average all pixel colors (simple approach for GPIO compatibility)
        if not self._pixels:
            return

        avg_r = sum(p[0] for p in self._pixels) // len(self._pixels)
        avg_g = sum(p[1] for p in self._pixels) // len(self._pixels)
        avg_b = sum(p[2] for p in self._pixels) // len(self._pixels)

        payload = {
            "on": True,
            "bri": self._brightness,
            "seg": [{
                "col": [[
                    self._scale(avg_r),
                    self._scale(avg_g),
                    self._scale(avg_b)
                ]],
                "fx": 0  # Solid color
            }]
        }
        self._send_command(payload)

    def off(self):
        """Turn off all LEDs."""
        self._pixels = [(0, 0, 0)] * self.led_count
        payload = {"on": False}
        self._send_command(payload)

    def set_brightness(self, val):
        """Set global brightness (0-255)."""
        self._brightness = max(0, min(255, val))
        self.show()

    def gradient(self, start_rgb, end_rgb):
        """Set gradient (averages to solid color in current implementation)."""
        for i in range(self.led_count):
            t = i / max(1, self.led_count - 1)
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
            self.set_pixel(i, (r, g, b))
        self.show()

    def pulse(self, rgb, speed=1.0, duration=10.0):
        """Pulse effect using WLED."""
        start_time = time.time()
        while time.time() - start_time < duration:
            t = time.time() - start_time
            brightness = (math.sin(t * speed * math.pi) + 1) / 2
            scaled = tuple(int(c * brightness) for c in rgb)
            self.fill(scaled)
            time.sleep(0.05)

    def breathe(self, rgb, speed=0.8, duration=10.0):
        """Breathe effect using WLED."""
        start_time = time.time()
        while time.time() - start_time < duration:
            t = (time.time() - start_time) * speed
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
            time.sleep(0.05)

    def chase(self, rgb, width=4, speed=0.05, duration=10.0):
        """Chase effect (simplified for WLED)."""
        # WLED chase would need custom effect
        # For now, pulse as approximation
        self.pulse(rgb, speed=1.0, duration=duration)

    def shimmer(self, base_rgb, variation=20, speed=0.04, duration=10.0):
        """Shimmer effect (simplified for WLED)."""
        # Full shimmer needs per-pixel control
        # Approximate with gentle pulse
        self.pulse(base_rgb, speed=2.0, duration=duration)

    def close(self):
        """Clean up (no resources to release for HTTP)."""
        pass
