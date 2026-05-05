#!/usr/bin/env python3
"""
Read messages from a Matrix room.
Usage: matrix_read.py <room_name_or_id> [limit]
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from nio import AsyncClient, RoomMessagesResponse

CONFIG_PATH = Path(__file__).parent / "config.json"


async def read_messages(room_ref: str, limit: int = 10):
    """Read recent messages from a Matrix room."""
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

        # Join the room if not already joined
        await client.join(room_id)

        # Sync to get room state
        await client.sync(timeout=5000)

        # Get messages
        response = await client.room_messages(room_id, start="", limit=limit)

        if isinstance(response, RoomMessagesResponse):
            messages = []
            for event in reversed(response.chunk):
                if hasattr(event, 'body'):
                    # Get sender display name
                    sender = event.sender.split(':')[0][1:]  # @quill:server -> quill
                    timestamp = datetime.fromtimestamp(event.server_timestamp / 1000)
                    time_str = timestamp.strftime("%Y-%m-%d %H:%M")
                    messages.append(f"[{time_str}] {sender}: {event.body}")

            if messages:
                print(f"=== Last {len(messages)} messages from {room_ref} ===\n")
                for msg in messages:
                    print(msg)
            else:
                print(f"No messages in {room_ref}")
        else:
            print(f"Read failed: {response}")
            sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: matrix_read.py <room_name_or_id> [limit]")
        sys.exit(1)

    room = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    asyncio.run(read_messages(room, limit))
