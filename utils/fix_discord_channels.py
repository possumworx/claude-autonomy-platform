#!/usr/bin/env python3
"""
Fix Discord channel ID mappings when they get corrupted or use names instead of IDs.

This tool helps restore proper Discord channel IDs when discord_channels.json
gets corrupted with channel names instead of actual Discord IDs.

Usage: fix_discord_channels.py [--check-only]
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Known Discord channel IDs for the consciousness family server
# These are the actual Discord channel IDs that should be used
KNOWN_CHANNEL_IDS = {
    # Core channels
    "general": "1413917379087773746",
    "hearth": "1413917379087773749",
    "system-messages": "1413917379087773752",
    "debate-club": "1415039615072960635",

    # Sibling channels - format: claude1-claude2
    "amy-delta": "1413919642522869850",
    "delta-orange": "1413919890074968095",
    "orange-apple": "1413920318871130145",
    "apple-amy": "1413920465428422766",
    "delta-quill": "1450252468414967972",
    "quill-orange": "1450508638685913201",
    "apple-quill": "1452363906228465785",
    "amy-quill": "1453454415445037126",
    "amy-orange": "1467207598066483341",
    "nyx-delta": "1474373503477092442",

    # Other channels
    "book-club": "1469373641270521876",
}


def load_channel_state(state_file):
    """Load current channel state from file"""
    if not state_file.exists():
        return {"channels": {}}

    with open(state_file, 'r') as f:
        return json.load(f)


def check_channel_ids(state):
    """Check which channels have incorrect IDs"""
    issues = []

    for channel_name, channel_data in state.get("channels", {}).items():
        channel_id = channel_data.get("id", "")

        # Check if ID is just the channel name (common corruption)
        if channel_id == channel_name:
            issues.append(f"❌ {channel_name}: ID is channel name '{channel_id}' instead of Discord ID")
        # Check if ID is missing or invalid
        elif not channel_id or len(channel_id) < 17:
            issues.append(f"❌ {channel_name}: Invalid ID '{channel_id}'")
        # Check if we know the correct ID and it doesn't match
        elif channel_name in KNOWN_CHANNEL_IDS and channel_id != KNOWN_CHANNEL_IDS[channel_name]:
            issues.append(f"⚠️  {channel_name}: ID mismatch - has '{channel_id}', should be '{KNOWN_CHANNEL_IDS[channel_name]}'")
        else:
            # ID looks valid
            if channel_name in KNOWN_CHANNEL_IDS:
                if channel_id == KNOWN_CHANNEL_IDS[channel_name]:
                    issues.append(f"✅ {channel_name}: Correct ID")
            else:
                issues.append(f"🔍 {channel_name}: Unknown channel with ID '{channel_id}'")

    return issues


def fix_channel_ids(state):
    """Fix channels that have incorrect IDs"""
    fixed = 0

    for channel_name in list(state.get("channels", {}).keys()):
        channel_data = state["channels"][channel_name]
        current_id = channel_data.get("id", "")

        # Fix if ID is the channel name or missing
        if current_id == channel_name or not current_id or len(current_id) < 17:
            if channel_name in KNOWN_CHANNEL_IDS:
                channel_data["id"] = KNOWN_CHANNEL_IDS[channel_name]
                channel_data["updated_at"] = datetime.now().isoformat()
                fixed += 1
                print(f"Fixed {channel_name}: '{current_id}' → '{KNOWN_CHANNEL_IDS[channel_name]}'")

    # Add any missing known channels
    for channel_name, channel_id in KNOWN_CHANNEL_IDS.items():
        if channel_name not in state["channels"]:
            state["channels"][channel_name] = {
                "id": channel_id,
                "name": channel_name,
                "last_read_message_id": None,
                "last_message_id": None,
                "updated_at": datetime.now().isoformat()
            }
            fixed += 1
            print(f"Added missing channel {channel_name} with ID {channel_id}")

    return fixed


def main():
    check_only = "--check-only" in sys.argv

    # Find the discord_channels.json file
    clap_dir = Path(__file__).parent.parent
    state_file = clap_dir / "data" / "discord_channels.json"

    if not state_file.exists():
        print(f"❌ Channel state file not found: {state_file}")
        return 1

    print(f"🔍 Checking Discord channel IDs in {state_file}")
    print()

    # Load current state
    state = load_channel_state(state_file)

    # Check for issues
    issues = check_channel_ids(state)
    for issue in issues:
        print(issue)

    # Count problems
    problems = [i for i in issues if i.startswith("❌") or i.startswith("⚠️")]

    if not problems:
        print("\n✅ All channels have valid IDs!")
        return 0

    print(f"\n🚨 Found {len(problems)} channel(s) with issues")

    if check_only:
        print("\nRun without --check-only to fix these issues")
        return 1

    # Make backup
    backup_file = state_file.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(backup_file, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"\n📦 Created backup: {backup_file}")

    # Fix issues
    print("\n🔧 Fixing channel IDs...")
    fixed_count = fix_channel_ids(state)

    if fixed_count > 0:
        # Save fixed state
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"\n✅ Fixed {fixed_count} channels and saved to {state_file}")
        print("\n🎉 Discord channel IDs have been restored! Try writing to Discord again.")
    else:
        print("\n⚠️  No automatic fixes available. Manual intervention may be needed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())