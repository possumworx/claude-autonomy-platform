#!/usr/bin/env python3
"""
Activity Tracking for Idle Detection
Tracks tool usage by checking Claude Code's history.jsonl modification time.
Used by autonomous_timer.py to conditionally surface seeds.
"""

import os
from pathlib import Path
from datetime import datetime

# Claude Code history file - gets updated whenever tools are used
CLAUDE_HISTORY = Path.home() / ".config" / "Claude" / "history.jsonl"

def get_last_activity_time():
    """
    Get the last time tools were used by checking history.jsonl mtime.

    Returns:
        datetime of last activity, or None if file doesn't exist
    """
    try:
        if not CLAUDE_HISTORY.exists():
            return None
        mtime = CLAUDE_HISTORY.stat().st_mtime
        return datetime.fromtimestamp(mtime)
    except Exception:
        return None

def get_cycles_since_activity(cycle_duration_seconds=1800):
    """
    Get number of autonomous timer cycles since last activity.

    Args:
        cycle_duration_seconds: Duration of one autonomous timer cycle (default 1800 = 30 min)

    Returns:
        Number of complete cycles since last activity, or 999 if can't determine
    """
    try:
        last_active = get_last_activity_time()
        if last_active is None:
            return 999  # No history file - treat as very idle

        elapsed = (datetime.now() - last_active).total_seconds()
        cycles = int(elapsed / cycle_duration_seconds)

        return cycles
    except Exception:
        return 999  # Error - treat as very idle

def is_idle(threshold_cycles=3, cycle_duration_seconds=1800):
    """
    Check if Orange has been idle for threshold_cycles.

    Args:
        threshold_cycles: Number of cycles to consider idle (default 3 = 90 min)
        cycle_duration_seconds: Duration of one cycle (default 1800 = 30 min)

    Returns:
        True if idle for >= threshold_cycles, False otherwise
    """
    cycles = get_cycles_since_activity(cycle_duration_seconds)
    return cycles >= threshold_cycles

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        last_activity = get_last_activity_time()
        cycles = get_cycles_since_activity()
        idle = is_idle()

        print(f"Last activity: {last_activity}")
        print(f"Cycles since activity: {cycles}")
        print(f"Is idle (>=3 cycles): {idle}")
    else:
        print("Usage: track_activity.py check")
