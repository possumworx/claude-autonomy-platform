#!/usr/bin/env python3
"""
Test script for emergency alert function
DO NOT RUN unless you want to send a test alert to #system-healthchecks
"""

import sys
from pathlib import Path

# Add the discord directory to path
sys.path.insert(0, str(Path(__file__).parent / "discord"))

from discord_tools import DiscordTools

def test_emergency_alert():
    """Test the emergency alert function with a simulated error"""
    print("Testing emergency alert function...")
    print("This will send a TEST alert to #system-healthchecks")

    try:
        discord = DiscordTools()
        result = discord.send_emergency_alert(
            error_type="TEST_ERROR",
            error_details="This is a test alert from the emergency notification system test script",
            session_context="test-session (sparkle-orange)"
        )

        if result["success"]:
            print("✅ Emergency alert sent successfully!")
            print(f"Message ID: {result['data']['id']}")
        else:
            print("❌ Failed to send emergency alert")
            print(f"Error: {result['error']}")

    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    confirmation = input("This will send a TEST alert to #system-healthchecks. Continue? (yes/no): ")
    if confirmation.lower() == "yes":
        test_emergency_alert()
    else:
        print("Test cancelled.")
