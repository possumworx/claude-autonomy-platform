#!/usr/bin/env python3
"""
Unified Discord messaging - handles both channels and DMs transparently
Uses routing config to determine whether to use bot (channels) or plugin MCP (DMs)
"""

import sys
import json
import subprocess
from pathlib import Path

# Add current directory to path for discord_tools
sys.path.insert(0, str(Path(__file__).parent))
from discord_tools import get_discord_tools

# Path to routing configuration
ROUTING_CONFIG = Path.home() / "claude-autonomy-platform" / "config" / "discord_routing.json"

def load_routing_config():
    """Load the routing configuration"""
    try:
        if ROUTING_CONFIG.exists():
            with open(ROUTING_CONFIG, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load routing config: {e}")
    return {"routes": {}}

def send_via_bot_dm(chat_id: str, message: str) -> dict:
    """Send a DM using the bot (DMs are just channels in Discord)"""
    tools = get_discord_tools()
    # Use the chat_id directly as a channel_id
    # We bypass resolve_channel since we already have the ID
    import requests
    url = f"https://discord.com/api/v10/channels/{chat_id}/messages"
    data = {"content": message}

    response = requests.post(url, headers=tools.headers, json=data)

    if response.status_code == 200:
        return {"success": True, "data": response.json()}
    else:
        error_text = response.text
        try:
            error_json = response.json()
            error_text = error_json.get('message', response.text)
        except:
            pass
        return {"success": False, "error": f"Discord API error: {error_text}"}

def main():
    if len(sys.argv) < 3:
        print("Usage: write_channel <recipient> <message>")
        print("Example: write_channel amy 'Hello Amy!'")
        print("Example: write_channel hearth 'Good morning everyone'")
        return 1

    recipient = sys.argv[1]
    message = ' '.join(sys.argv[2:])

    # Load routing configuration
    routing = load_routing_config()
    routes = routing.get("routes", {})

    # Check if recipient has a configured route
    if recipient in routes:
        route = routes[recipient]
        route_type = route.get("type", "channel")

        if route_type == "dm":
            # Send via plugin MCP
            chat_id = route.get("chat_id")
            if not chat_id:
                print(f"❌ Error: No chat_id configured for {recipient}")
                return 1

            print(f"📨 Sending DM to {recipient}...")
            result = send_via_bot_dm(chat_id, message)

            if result["success"]:
                print(f"✅ DM sent to {recipient}")
            else:
                print(f"❌ Error: {result['error']}")
                return 1

        elif route_type == "channel":
            # Send via existing bot using configured channel name
            channel_name = route.get("name", recipient)
            tools = get_discord_tools()
            result = tools.send_message(channel_name, message)

            if result["success"]:
                print(f"✅ Message sent to #{channel_name}")
                message_data = result["data"]
                if "id" in message_data:
                    print(f"Message ID: {message_data['id']}")
            else:
                print(f"❌ Error: {result['error']}")
                return 1
    else:
        # No routing config - fall back to treating as channel name
        tools = get_discord_tools()
        result = tools.send_message(recipient, message)

        if result["success"]:
            print(f"✅ Message sent to #{recipient}")
            message_data = result["data"]
            if "id" in message_data:
                print(f"Message ID: {message_data['id']}")
        else:
            print(f"❌ Error: {result['error']}")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)