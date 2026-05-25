#!/usr/bin/env python3
"""Cross-Pi LED strip driver for WS2812B LEDs.

Supports both:
- Raspberry Pi 5: PIO kernel driver via /dev/leds0
- Raspberry Pi 4/3: rpi_ws281x userspace library via PWM+DMA

The driver auto-detects the Pi model and uses the appropriate backend.
Same interface regardless of underlying hardware.

Usage as library:
    from led_driver import LEDStrip
    strip = LEDStrip()
    strip.fill((255, 100, 0))  # warm amber
    strip.breathe((255, 100, 0), duration=30)
    strip.off()

Usage from CLI:
    python3 led_driver.py fill 255 100 0
    python3 led_driver.py breathe 255 100 0
    python3 led_driver.py off
"""

import sys
import os
import time
import math


def detect_pi_model():
    """Detect Raspberry Pi model from device tree."""
    try:
        with open("/proc/device-tree/model", "r") as f:
            model = f.read().strip('\x00')
            if "Pi 5" in model:
                return 5
            elif "Pi 4" in model:
                return 4
            elif "Pi 3" in model:
                return 3
            else:
                return 0  # Unknown
    except FileNotFoundError:
        return 0


PI_MODEL = detect_pi_model()


class LEDStripBase:
    """Base class defining the LED strip interface."""

    def __init__(self, led_count=64, brightness=255, gpio_pin=18):
        self.led_count = led_count
        self._brightness = brightness
        self.gpio_pin = gpio_pin
        self._pixels = [(0, 0, 0)] * led_count

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
        raise NotImplementedError("Subclass must implement show()")

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
                # Random sparks for organic feel
                if random.random() < 0.005:
                    wave += random.uniform(-40, 70)
                r = max(0, min(255, int(base_rgb[0] + wave * 1.0)))
                g = max(0, min(255, int(base_rgb[1] + wave * 0.1)))
                b = max(0, min(255, int(base_rgb[2] + wave * 0.6)))
                self.set_pixel(i, (r, g, b))
            self.show()
            time.sleep(speed)

    def close(self):
        """Clean up resources."""
        pass


class LEDStripPi5(LEDStripBase):
    """Pi 5 driver using PIO kernel driver (/dev/leds0)."""

    def __init__(self, led_count=64, brightness=255, gpio_pin=18,
                 device="/dev/leds0"):
        super().__init__(led_count, brightness, gpio_pin)
        self._device = device

        if not os.path.exists(device):
            raise RuntimeError(
                f"{device} not found. Load overlay first:\n"
                f"  Add to /boot/firmware/config.txt:\n"
                f"    dtoverlay=ws2812-pio,gpio={gpio_pin},num_leds={led_count},brightness=255\n"
                f"  Then reboot."
            )

    def show(self):
        buf = bytearray(self.led_count * 4)
        for i, (r, g, b) in enumerate(self._pixels):
            # GRB order with padding byte
            buf[i * 4] = self._scale(r)
            buf[i * 4 + 1] = self._scale(g)
            buf[i * 4 + 2] = self._scale(b)
            buf[i * 4 + 3] = 0  # padding
        with open(self._device, "wb") as f:
            f.write(buf)


class LEDStripPi5Adafruit(LEDStripBase):
    """Pi 5 driver using Adafruit NeoPixel library (when PIO overlay not available)."""

    def __init__(self, led_count=64, brightness=255, gpio_pin=18):
        super().__init__(led_count, brightness, gpio_pin)

        try:
            import board
            import neopixel
            self._neopixel = neopixel
        except ImportError:
            raise RuntimeError(
                "Adafruit NeoPixel library not found. Install with:\n"
                "  pip install adafruit-circuitpython-neopixel\n"
                "  pip install Adafruit-Blinka-Raspberry-Pi5-Neopixel"
            )

        # Map GPIO number to board pin
        pin_map = {18: board.D18, 12: board.D12, 13: board.D13}
        board_pin = pin_map.get(gpio_pin, board.D18)

        self._pixels_hw = neopixel.NeoPixel(
            board_pin, led_count,
            brightness=brightness / 255.0,
            auto_write=False
        )

    def show(self):
        for i, (r, g, b) in enumerate(self._pixels):
            self._pixels_hw[i] = (self._scale(r), self._scale(g), self._scale(b))
        self._pixels_hw.show()

    def set_brightness(self, val):
        self._brightness = max(0, min(255, val))
        self._pixels_hw.brightness = val / 255.0
        self.show()


class LEDStripPi4(LEDStripBase):
    """Pi 4/3 driver using rpi_ws281x library (PWM+DMA)."""

    def __init__(self, led_count=64, brightness=255, gpio_pin=18):
        super().__init__(led_count, brightness, gpio_pin)

        try:
            from rpi_ws281x import PixelStrip, Color
            self._Color = Color
        except ImportError:
            raise RuntimeError(
                "rpi_ws281x library not found. Install with:\n"
                "  pip install rpi_ws281x"
            )

        # LED strip configuration
        LED_FREQ_HZ = 800000
        LED_DMA = 10
        LED_INVERT = False
        LED_CHANNEL = 0

        self._strip = PixelStrip(
            led_count, gpio_pin, LED_FREQ_HZ, LED_DMA,
            LED_INVERT, brightness, LED_CHANNEL
        )
        self._strip.begin()

    def show(self):
        for i, (r, g, b) in enumerate(self._pixels):
            # rpi_ws281x uses GRB internally via Color()
            self._strip.setPixelColor(i, self._Color(
                self._scale(g), self._scale(r), self._scale(b)
            ))
        self._strip.show()

    def set_brightness(self, val):
        self._brightness = max(0, min(255, val))
        self._strip.setBrightness(val)
        self.show()


def LEDStrip(led_count=64, brightness=255, gpio_pin=18, **kwargs):
    """Factory function that returns the appropriate driver for this Pi."""

    if PI_MODEL == 5:
        # Check if PIO device exists (preferred method)
        if os.path.exists("/dev/leds0"):
            return LEDStripPi5(led_count, brightness, gpio_pin, **kwargs)
        else:
            # Fall back to Adafruit library if overlay not loaded
            print("Note: /dev/leds0 not found, using Adafruit NeoPixel library...",
                  file=sys.stderr)
            return LEDStripPi5Adafruit(led_count, brightness, gpio_pin)

    if PI_MODEL in (3, 4):
        return LEDStripPi4(led_count, brightness, gpio_pin)

    raise RuntimeError(
        f"Unsupported Pi model (detected: {PI_MODEL}). "
        "This driver requires Raspberry Pi 3, 4, or 5."
    )


def _parse_rgb(s):
    """Parse RGB from comma-separated string."""
    parts = s.split(",")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def main():
    """CLI entry point with signal handling."""
    import signal

    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCommands: fill, off, breathe, pulse, shimmer, chase, gradient, test")
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
        print(f"Testing LED strip (Pi {PI_MODEL} detected)")
        print("Red...")
        strip.fill((255, 0, 0))
        time.sleep(1)
        print("Green...")
        strip.fill((0, 255, 0))
        time.sleep(1)
        print("Blue...")
        strip.fill((0, 0, 255))
        time.sleep(1)
        print("Warm amber...")
        strip.fill((255, 100, 0))
        time.sleep(1)
        print("Gradient...")
        strip.gradient((255, 50, 0), (50, 0, 100))
        time.sleep(2)
        print("Shimmer...")
        strip.shimmer((255, 80, 0), duration=5)
        print("Off.")
        strip.off()

    elif cmd == "brightness":
        strip.set_brightness(int(sys.argv[2]))

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
