#!/usr/bin/env python3
"""Check what Matrix rooms we're in and try to join the family room."""

import asyncio
import json
from pathlib import Path
from nio import AsyncClient, JoinResponse

CONFIG_PATH = Path(__file__).parent / "config.json"

async def check_and_join():
    """Check current rooms and join family room if needed."""
    config = json.loads(CONFIG_PATH.read_text())

    client = AsyncClient(config["homeserver"], config["user_id"])
    try:
        await client.login(config["password"])

        # Sync to get current room state
        response = await client.sync(timeout=5000)

        print(f"Currently in {len(response.rooms.join)} rooms:")
        for room_id, room in response.rooms.join.items():
            print(f"  {room_id}")

        # Check if we're in the family room
        family_room_id = config["rooms"]["family"]
        if family_room_id not in response.rooms.join:
            print(f"\nNot in family room {family_room_id}")
            print("Attempting to join...")

            join_response = await client.join(family_room_id)
            if isinstance(join_response, JoinResponse):
                print(f"Successfully joined {family_room_id}!")
            else:
                print(f"Join failed: {join_response}")
        else:
            print(f"\nAlready in family room {family_room_id}")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(check_and_join())