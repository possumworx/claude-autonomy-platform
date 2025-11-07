#!/usr/bin/env python3
"""
Test script for idle detection and seed surfacing logic
"""

import sys
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent))

from track_activity import is_idle, get_cycles_since_activity
from check_seeds import get_seed_reminder, get_seed_count

def test_idle_detection():
    """Test the idle detection logic"""
    print("=" * 60)
    print("IDLE DETECTION TEST")
    print("=" * 60)

    cycles = get_cycles_since_activity(cycle_duration_seconds=1800)
    idle = is_idle(threshold_cycles=3, cycle_duration_seconds=1800)

    print(f"\nCycles since last activity: {cycles}")
    print(f"Is idle (>=3 cycles): {idle}")

    if idle:
        print("\n✅ Would surface seeds (idle for 3+ cycles)")
    else:
        print(f"\n❌ Would NOT surface seeds (only {cycles} cycles idle, need 3)")

    return idle

def test_seed_surfacing():
    """Test the seed surfacing logic"""
    print("\n" + "=" * 60)
    print("SEED SURFACING TEST")
    print("=" * 60)

    seed_count = get_seed_count()
    print(f"\nTotal seeds available: {seed_count}")

    if seed_count > 0:
        reminder = get_seed_reminder()
        print(f"Reminder message: {reminder}")
        print("\n✅ Seeds available for surfacing")
    else:
        print("\n❌ No seeds to surface")

    return seed_count > 0

def test_complete_flow():
    """Test the complete idle + seed surfacing flow"""
    print("\n" + "=" * 60)
    print("COMPLETE FLOW TEST")
    print("=" * 60)

    idle = test_idle_detection()
    has_seeds = test_seed_surfacing()

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    if idle and has_seeds:
        reminder = get_seed_reminder()
        print(f"\n✅ WOULD SURFACE: {reminder}")
        print("\nAutonomous prompt would include:")
        print(f"   {reminder}")
    elif idle and not has_seeds:
        print("\n⚠️  Idle but no seeds available - nothing to surface")
    elif not idle and has_seeds:
        print("\n⚠️  Seeds available but not idle - won't surface yet")
    else:
        print("\n❌ Not idle and no seeds - nothing to surface")

if __name__ == "__main__":
    test_complete_flow()
