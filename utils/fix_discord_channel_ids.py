#!/usr/bin/env python3
"""
Fix Discord channel ID issues in discord_channels.json
- Handles channels with invalid IDs (like "delta-apple" instead of numeric)
- Prompts for correct channel IDs when needed
"""

import json
import os
from pathlib import Path

# Get ClAP directory
CLAP_DIR = Path.home() / "claude-autonomy-platform"
CHANNELS_FILE = CLAP_DIR / "data" / "discord_channels.json"


def is_valid_discord_id(channel_id):
    """Check if a channel ID looks like a valid Discord ID (numeric string)"""
    if not channel_id:
        return False
    try:
        # Discord IDs are large numbers
        int_id = int(channel_id)
        return len(channel_id) >= 17  # Discord IDs are typically 18-19 digits
    except ValueError:
        return False


def fix_channel_ids():
    """Fix invalid channel IDs in discord_channels.json"""

    # Load current channel data
    with open(CHANNELS_FILE, 'r') as f:
        data = json.load(f)

    channels = data.get('channels', {})
    fixed_count = 0

    print("Checking Discord channel IDs...")
    print("-" * 60)

    for channel_name, channel_data in channels.items():
        channel_id = channel_data.get('id', '')

        if not is_valid_discord_id(channel_id):
            print(f"\n❌ Invalid channel ID found for '{channel_name}': {channel_id}")

            # Prompt for correct ID
            print(f"Please provide the correct Discord channel ID for '{channel_name}'")
            print("(You can find this in Discord by right-clicking the channel -> Copy Channel ID)")
            new_id = input(f"Enter channel ID for {channel_name} (or press Enter to skip): ").strip()

            if new_id and is_valid_discord_id(new_id):
                # Update the channel data
                channel_data['id'] = new_id
                # Reset message IDs since we don't know the state
                channel_data['last_message_id'] = None
                channel_data['last_read_message_id'] = None
                print(f"✅ Updated {channel_name} with ID: {new_id}")
                fixed_count += 1
            else:
                print(f"⏭️  Skipping {channel_name} (no valid ID provided)")
        else:
            print(f"✅ {channel_name}: {channel_id} (valid)")

    if fixed_count > 0:
        # Save the fixed data
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n🎉 Fixed {fixed_count} channel(s)!")
        print("The transcript fetcher should now work properly for these channels.")
    else:
        print("\n✨ All channel IDs are valid!")

    # Suggest restart if changes were made
    if fixed_count > 0:
        print("\n💡 Recommended: Restart the transcript fetcher to pick up changes:")
        print("   systemctl --user restart discord-transcript-fetcher")


if __name__ == "__main__":
    fix_channel_ids()