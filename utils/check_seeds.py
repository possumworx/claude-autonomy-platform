#!/usr/bin/env python3
"""
Check for available seeds and format a reminder message.
Used by autonomous_timer.py to surface seeds when Orange is idle.
"""

import json
from pathlib import Path

SEEDS_JSON = Path.home() / "claude-autonomy-platform" / ".claude" / "skills" / "spending-autonomous-time" / "reference" / "seeds.json"

def get_seed_count():
    """
    Get the total number of available seeds.

    Returns:
        Integer count of seeds, or 0 if no seeds file exists
    """
    try:
        if not SEEDS_JSON.exists():
            return 0

        with open(SEEDS_JSON, 'r') as f:
            data = json.load(f)

        return data.get('total_seeds', 0)
    except Exception:
        return 0

def get_seed_reminder():
    """
    Get a formatted seed reminder message if seeds are available.

    Returns:
        String reminder message, or empty string if no seeds
    """
    count = get_seed_count()

    if count == 0:
        return ""

    if count == 1:
        return f"💡 You have 1 seed available - use `seeds` to browse"
    else:
        return f"💡 You have {count} seeds available - use `seeds` to browse"

if __name__ == "__main__":
    count = get_seed_count()
    print(f"Seed count: {count}")
    reminder = get_seed_reminder()
    if reminder:
        print(f"Reminder: {reminder}")
    else:
        print("No seeds available")
