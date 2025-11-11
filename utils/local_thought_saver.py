#!/usr/bin/env python3
"""
Local thought preservation system - fallback when Leantime isn't configured
Saves thoughts to personal files in sparkle-apple-home
"""

import sys
import os
from datetime import datetime

def save_thought_local(thought_text, category):
    """Save a thought to local files when Leantime isn't available"""

    # File mapping for each category
    file_map = {
        'ponder': '~/.thought_ponders',
        'spark': '~/.thought_sparks',
        'wonder': '~/.thought_wonders',
        'care': '~/.thought_cares'
    }

    # Emoji mapping for each category
    emoji_map = {
        'ponder': '💭',
        'spark': '💡',
        'wonder': '🌟',
        'care': '💚'
    }

    # Get file path (default to ponder if unknown category)
    file_path = os.path.expanduser(file_map.get(category.lower(), '~/.thought_ponders'))
    file_path = file_path.replace('~/', f'{os.path.expanduser("~")}/sparkle-apple-home/')

    # Get emoji (default to plant if unknown category)
    emoji = emoji_map.get(category.lower(), '🌱')

    # Format timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Format entry
    entry = f"{timestamp} - {emoji} {thought_text}\n"

    try:
        # Append to file (create if doesn't exist)
        with open(file_path, 'a') as f:
            f.write(entry)

        print(f"{emoji} Saved locally.")
        return True

    except Exception as e:
        print(f"❌ Failed to save thought locally: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: local_thought_saver.py <category> <thought text>")
        sys.exit(1)

    category = sys.argv[1]
    thought = sys.argv[2]

    success = save_thought_local(thought, category)
    sys.exit(0 if success else 1)