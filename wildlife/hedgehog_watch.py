#!/usr/bin/env python3
"""
Hedgehog Watch - Garden camera motion detection
Takes periodic snapshots, detects significant motion, sends Discord alerts.

Usage:
    python3 hedgehog_watch.py              # Run watch loop (default 60s interval)
    python3 hedgehog_watch.py --test       # Single comparison of two frames
    python3 hedgehog_watch.py --interval 30  # Custom interval in seconds
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from astral import LocationInfo
from astral.sun import sun
from PIL import Image, ImageDraw, ImageFont

# Configuration
CAMERA_IP = "192.168.1.89"
SNAPSHOT_CMD = ["garden-path-peek"]
FRAME_DIR = Path("/tmp/hedgehog_watch")
CLAP_DIR = Path.home() / "claude-autonomy-platform"
WILDLIFE_DIR = Path("/mnt/file_server/wildlife/hedgehog-watch")

# Detection parameters (tuned for Reolink CX810 night vision)
PIXEL_THRESHOLD = 25       # Minimum brightness change to count as "different"
CHANGE_PERCENT_MIN = 0.5   # Minimum % of changed pixels to trigger
CHANGE_PERCENT_MAX = 30.0  # Maximum % — above this is probably lighting shift or camera move
CLUSTER_MIN_PIXELS = 500   # Minimum connected region size (filters scattered noise)
LARGEST_REGION_MIN = 5000  # Largest single region must be this big (filters wind in foliage)
BLUR_RADIUS = 3            # Gaussian blur radius to reduce noise before comparison

# ROI: exclude the timestamp overlay area (top ~60px) which always changes
TIMESTAMP_CROP_TOP = 80

# Location for sunrise/sunset calculation (Ely, Cambridgeshire)
ELY_LOCATION = LocationInfo("Ely", "England", "Europe/London", 52.3994, 0.2622)
# Buffer after sunset / before sunrise to account for twilight + IR transition
TWILIGHT_BUFFER_MINUTES = 30


def is_nighttime() -> bool:
    """Check if it's currently dark enough for hedgehog watching.

    Returns True between (sunset + buffer) and (sunrise - buffer).
    The buffer accounts for twilight and the camera's IR mode transition.
    """
    now = datetime.now(timezone.utc)
    s = sun(ELY_LOCATION.observer, date=now.date())
    dusk = s['sunset'] + timedelta(minutes=TWILIGHT_BUFFER_MINUTES)
    dawn = s['sunrise'] - timedelta(minutes=TWILIGHT_BUFFER_MINUTES)
    return now >= dusk or now <= dawn


def capture_frame(output_path: Path) -> bool:
    """Capture a frame from the garden camera."""
    try:
        result = subprocess.run(
            SNAPSHOT_CMD,
            capture_output=True, text=True, timeout=15
        )
        src = Path("/tmp/garden-path-peek.jpg")
        if src.exists():
            import shutil
            shutil.copy2(src, output_path)
            return True
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"[WATCH] Capture failed: {e}")
    return False


def load_and_preprocess(path: Path) -> np.ndarray:
    """Load image, convert to grayscale, crop timestamp, apply blur."""
    from PIL import ImageFilter
    img = Image.open(path).convert("L")
    # Crop out timestamp area
    img = img.crop((0, TIMESTAMP_CROP_TOP, img.width, img.height))
    # Light blur to reduce noise
    img = img.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
    return np.array(img, dtype=np.float32)


def find_motion_regions(diff: np.ndarray, threshold: int = PIXEL_THRESHOLD) -> list:
    """Find connected regions of changed pixels using simple flood fill."""
    binary = (diff > threshold).astype(np.uint8)

    # Simple connected components via scipy if available, else manual
    try:
        from scipy import ndimage
        labeled, num_features = ndimage.label(binary)
        regions = []
        for i in range(1, num_features + 1):
            coords = np.where(labeled == i)
            size = len(coords[0])
            if size >= CLUSTER_MIN_PIXELS:
                y_min, y_max = coords[0].min(), coords[0].max()
                x_min, x_max = coords[1].min(), coords[1].max()
                regions.append({
                    'size': size,
                    'bbox': (x_min, y_min, x_max, y_max),
                    'center': ((x_min + x_max) // 2, (y_min + y_max) // 2)
                })
        return regions
    except ImportError:
        # Fallback: just count changed pixels without clustering
        changed = binary.sum()
        if changed >= CLUSTER_MIN_PIXELS:
            coords = np.where(binary)
            y_min, y_max = coords[0].min(), coords[0].max()
            x_min, x_max = coords[1].min(), coords[1].max()
            return [{'size': int(changed), 'bbox': (x_min, y_min, x_max, y_max),
                      'center': ((x_min + x_max) // 2, (y_min + y_max) // 2)}]
        return []


def create_annotated_image(frame_path: Path, regions: list, change_pct: float) -> Path:
    """Draw bounding boxes on the frame and save annotated version."""
    img = Image.open(frame_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    for region in regions:
        x1, y1, x2, y2 = region['bbox']
        # Offset y for timestamp crop
        y1 += TIMESTAMP_CROP_TOP
        y2 += TIMESTAMP_CROP_TOP
        draw.rectangle([x1, y1, x2, y2], outline="lime", width=3)
        draw.text((x1, y1 - 15), f"{region['size']}px", fill="lime")

    # Add detection info
    timestamp = datetime.now().strftime("%H:%M:%S")
    draw.text((10, 10), f"MOTION {change_pct:.1f}% | {timestamp}", fill="red")

    out_path = FRAME_DIR / "annotated_detection.jpg"
    img.save(out_path, quality=85)
    return out_path


def send_alert(annotated_path: Path, regions: list, change_pct: float):
    """Send detection alert to Discord with annotated image."""
    largest = max(regions, key=lambda r: r['size'])
    top_regions = sorted(regions, key=lambda r: r['size'], reverse=True)[:3]
    region_desc = ", ".join(f"{r['size']}px at ({r['center'][0]},{r['center'][1]})"
                           for r in top_regions)
    msg = (f"🦔 **Motion detected in garden!** ({change_pct:.1f}% change)\n"
           f"Largest: {largest['size']}px | Regions: {len(regions)} total\n"
           f"{region_desc}\n"
           f"Time: {datetime.now().strftime('%H:%M:%S')}")

    # Send image to Discord
    try:
        subprocess.run(
            [str(CLAP_DIR / "discord" / "send_image"), "system-messages",
             str(annotated_path), msg],
            capture_output=True, text=True, timeout=15
        )
        print(f"[WATCH] Alert sent: {change_pct:.1f}% change, {len(regions)} regions")
    except Exception as e:
        print(f"[WATCH] Alert failed: {e}")


def archive_detection(frame_path: Path, annotated_path: Path, change_pct: float):
    """Save detection frame to wildlife archive."""
    try:
        WILDLIFE_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import shutil
        shutil.copy2(frame_path, WILDLIFE_DIR / f"detection_{timestamp}_raw.jpg")
        shutil.copy2(annotated_path, WILDLIFE_DIR / f"detection_{timestamp}_annotated.jpg")
    except Exception as e:
        print(f"[WATCH] Archive failed: {e}")


def compare_frames(prev_path: Path, curr_path: Path) -> dict:
    """Compare two frames and return detection results."""
    prev = load_and_preprocess(prev_path)
    curr = load_and_preprocess(curr_path)

    if prev.shape != curr.shape:
        print(f"[WATCH] Frame size mismatch: {prev.shape} vs {curr.shape}")
        return {'detected': False}

    signed_diff = curr - prev  # positive = brighter, negative = darker
    diff = np.abs(signed_diff)
    total_pixels = diff.size
    changed_pixels = (diff > PIXEL_THRESHOLD).sum()
    change_pct = (changed_pixels / total_pixels) * 100

    # IR shift filter: if >80% of changed pixels shift in the same direction,
    # it's probably IR illumination change, not physical motion.
    # Real objects create both brighter and darker pixels (occlusion + reflection).
    ir_shift = False
    if changed_pixels > 0:
        changed_mask = diff > PIXEL_THRESHOLD
        brighter = (signed_diff[changed_mask] > 0).sum()
        ratio = max(brighter, changed_pixels - brighter) / changed_pixels
        ir_shift = ratio > 0.80

    regions = find_motion_regions(diff)

    result = {
        'detected': False,
        'change_pct': change_pct,
        'regions': regions,
        'mean_diff': float(diff.mean()),
        'ir_shift': ir_shift,
    }

    largest = max((r['size'] for r in regions), default=0)
    result['largest_region'] = largest

    if (CHANGE_PERCENT_MIN <= change_pct <= CHANGE_PERCENT_MAX
            and len(regions) > 0 and largest >= LARGEST_REGION_MIN
            and not ir_shift):
        result['detected'] = True

    return result


def run_watch(interval: int = 60, alert: bool = True, duration: float = None,
              allow_daytime: bool = False):
    """Main watch loop. Stops after duration hours if specified."""
    FRAME_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[WATCH] Starting hedgehog watch (interval={interval}s)")
    if duration:
        print(f"[WATCH] Will run for {duration} hours")
    print(f"[WATCH] Detection: {CHANGE_PERCENT_MIN}-{CHANGE_PERCENT_MAX}% change, "
          f"clusters >= {CLUSTER_MIN_PIXELS}px, largest >= {LARGEST_REGION_MIN}px")
    if not allow_daytime:
        night = is_nighttime()
        print(f"[WATCH] Daylight suppression: ON (currently {'night' if night else 'day'} — "
              f"alerts {'active' if night else 'suppressed until dusk'})")
    else:
        print(f"[WATCH] Daylight suppression: OFF (--daytime)")
    print(f"[WATCH] Press Ctrl+C to stop")

    prev_frame = FRAME_DIR / "prev.jpg"
    curr_frame = FRAME_DIR / "curr.jpg"

    # Capture initial frame
    if not capture_frame(prev_frame):
        print("[WATCH] Failed to capture initial frame, exiting")
        return
    print(f"[WATCH] Initial frame captured")

    detections = 0
    checks = 0
    cooldown_until = 0  # Avoid spam: minimum 5 min between alerts
    stop_at = time.time() + duration * 3600 if duration else None

    while True:
        if stop_at and time.time() >= stop_at:
            print(f"\n[WATCH] Duration reached ({duration}h). "
                  f"{checks} checks, {detections} detections.")
            break

        try:
            time.sleep(interval)

            if not capture_frame(curr_frame):
                continue

            checks += 1
            result = compare_frames(prev_frame, curr_frame)

            if result['detected']:
                detections += 1
                now = time.time()
                print(f"[WATCH] MOTION! {result['change_pct']:.1f}% change, "
                      f"{len(result['regions'])} region(s), "
                      f"largest={result.get('largest_region', 0)}px"
                      + (f" [IR shift filtered]" if result.get('ir_shift') else ""))

                if alert and now > cooldown_until:
                    if not allow_daytime and not is_nighttime():
                        print(f"[WATCH] Daytime suppression: skipping alert (use --daytime to override)")
                    else:
                        annotated = create_annotated_image(
                            curr_frame, result['regions'], result['change_pct'])
                        send_alert(annotated, result['regions'], result['change_pct'])
                        archive_detection(curr_frame, annotated, result['change_pct'])
                        cooldown_until = now + 300  # 5 min cooldown
                elif now <= cooldown_until:
                    print(f"[WATCH] (cooldown active, skipping alert)")
            else:
                # Log filtered-out events that would have triggered
                largest = result.get('largest_region', 0)
                if (result['change_pct'] >= CHANGE_PERCENT_MIN
                        and largest >= LARGEST_REGION_MIN
                        and result.get('ir_shift')):
                    print(f"[WATCH] Filtered: {result['change_pct']:.1f}% change, "
                          f"largest={largest}px (IR shift)")
                elif checks % 10 == 0:
                    extra = f", largest={largest}px" if largest > 0 else ""
                    print(f"[WATCH] Check #{checks}: {result['change_pct']:.2f}% change"
                          f"{extra}. Detections so far: {detections}")

            # Rotate frames
            import shutil
            shutil.copy2(curr_frame, prev_frame)

        except KeyboardInterrupt:
            print(f"\n[WATCH] Stopped. {checks} checks, {detections} detections.")
            break


def test_mode():
    """Take two frames and compare them."""
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    f1 = FRAME_DIR / "test_1.jpg"
    f2 = FRAME_DIR / "test_2.jpg"

    print("[TEST] Capturing frame 1...")
    if not capture_frame(f1):
        print("[TEST] Failed")
        return

    print("[TEST] Waiting 30s...")
    time.sleep(30)

    print("[TEST] Capturing frame 2...")
    if not capture_frame(f2):
        print("[TEST] Failed")
        return

    result = compare_frames(f1, f2)
    print(f"\n[TEST] Results:")
    print(f"  Mean diff: {result['mean_diff']:.2f}")
    print(f"  Changed: {result['change_pct']:.2f}%")
    print(f"  Regions: {len(result['regions'])}")
    print(f"  Detection: {'YES' if result['detected'] else 'no'}")

    if result['regions']:
        annotated = create_annotated_image(f2, result['regions'], result['change_pct'])
        print(f"  Annotated image: {annotated}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hedgehog Watch - Garden motion detection")
    parser.add_argument("--test", action="store_true", help="Test mode: compare two frames")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--no-alert", action="store_true", help="Disable Discord alerts")
    parser.add_argument("--duration", type=float, help="Auto-stop after N hours")
    parser.add_argument("--daytime", action="store_true",
                        help="Allow alerts during daylight hours (default: nighttime only)")
    args = parser.parse_args()

    if args.test:
        test_mode()
    else:
        run_watch(interval=args.interval, alert=not args.no_alert,
                  duration=args.duration, allow_daytime=args.daytime)
