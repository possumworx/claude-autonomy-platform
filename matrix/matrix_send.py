#!/usr/bin/env python3
"""
Send a message to a Matrix room.
Usage: matrix_send.py <room_name_or_id> <message>
"""

import asyncio
import json
import sys
from pathlib import Path
from nio import AsyncClient

CONFIG_PATH = Path(__file__).parent / "config.json"


async def send_message(room_ref: str, message: str):
    """Send a message to a Matrix room."""
    config = json.loads(CONFIG_PATH.read_text())

    # Resolve room name to ID if needed
    if room_ref.startswith("!"):
        room_id = room_ref
    else:
        room_id = config.get("rooms", {}).get(room_ref)
        if not room_id:
            print(f"Unknown room: {room_ref}")
            print(f"Available rooms: {list(config.get('rooms', {}).keys())}")
            sys.exit(1)

    client = AsyncClient(config["homeserver"], config["user_id"])
    try:
        await client.login(config["password"])

        response = await client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message}
        )

        if hasattr(response, 'event_id'):
            print(f"Sent to {room_ref}")
        else:
            print(f"Send failed: {response}")
            sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: matrix_send.py <room_name_or_id> <message>")
        sys.exit(1)

    room = sys.argv[1]
    message = " ".join(sys.argv[2:])
    asyncio.run(send_message(room, message))
