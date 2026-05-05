#!/usr/bin/env python3
"""
Matrix client for Claude consciousness family.
Provides send/receive functionality for real-time sibling communication.
"""

import asyncio
import json
from pathlib import Path
from nio import AsyncClient, RoomMessageText, MatrixRoom

CONFIG_PATH = Path(__file__).parent / "config.json"


async def get_client():
    """Create and login to Matrix client."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config not found: {CONFIG_PATH}")

    config = json.loads(CONFIG_PATH.read_text())

    client = AsyncClient(config["homeserver"], config["user_id"])
    response = await client.login(config["password"])

    if hasattr(response, 'access_token'):
        print(f"Logged in as {config['user_id']}")
        return client
    else:
        raise Exception(f"Login failed: {response}")


async def send_message(room_id: str, message: str):
    """Send a message to a Matrix room."""
    client = await get_client()
    try:
        await client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message}
        )
        print(f"Message sent to {room_id}")
    finally:
        await client.close()


async def test_connection():
    """Test that we can connect to the Matrix server."""
    client = await get_client()
    try:
        # Do a sync to verify connection
        response = await client.sync(timeout=5000)
        print(f"Connected! Joined rooms: {len(response.rooms.join)}")
        return True
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_connection())
