#!/usr/bin/env python3
"""
Plant a seed in your forwards-memory or the family Seed Garden
Usage: plant-seed "your idea here"
       plant-seed --family "shared idea for everyone"
       plant-seed --list              (show your personal seeds)
       plant-seed --list --family     (show family garden seeds)
"""

import sys
import os
import requests

# Add utils to path
sys.path.insert(0, os.path.expanduser('~/claude-autonomy-platform/utils'))
from infrastructure_config_reader import get_config_value

# Read project IDs from infrastructure config
FORWARD_MEMORY_PROJECT_ID = get_config_value('FORWARD_MEMORY_PROJECT_ID')
FAMILY_GARDEN_PROJECT_ID = get_config_value('FAMILY_GARDEN_PROJECT_ID')

def api_call(method, params=None):
    """Make a JSON-RPC call to Leantime API."""
    leantime_url = get_config_value('LEANTIME_URL')
    api_token = get_config_value('LEANTIME_API_TOKEN')

    if not api_token:
        print("❌ Missing Leantime API token configuration")
        return None

    headers = {
        "x-api-key": api_token,
        "Content-Type": "application/json"
    }

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1
    }

    if params:
        payload["params"] = params

    try:
        response = requests.post(f"{leantime_url}/api/jsonrpc", json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            print(f"❌ API Error: {data['error']}")
            return None

        return data.get("result")
    except Exception as e:
        print(f"❌ Failed to connect to Leantime: {e}")
        return None

def list_seeds(project_id):
    """List all seeds in the specified project."""
    # Fetch all tickets (Leantime API doesn't filter by project)
    all_tickets = api_call("leantime.rpc.Tickets.getAll", {})

    if not all_tickets:
        print("❌ No seeds found (or error fetching)")
        return False

    # Filter to just ideas for this specific project
    seeds = [t for t in all_tickets
             if t.get("type") == "idea" and str(t.get("projectId")) == str(project_id)]

    if not seeds:
        project_name = "🌱 Seed Garden" if project_id == FAMILY_GARDEN_PROJECT_ID else "🍊 Forwards Memory"
        print(f"🌱 No seeds planted in {project_name} yet!")
        print("\nPlant your first seed:")
        if project_id == FAMILY_GARDEN_PROJECT_ID:
            print('  plant-seed --family "your collaborative idea here"')
        else:
            print('  plant-seed "your idea here"')
        return True

    # Display seeds
    project_name = "🌱 Seed Garden" if project_id == FAMILY_GARDEN_PROJECT_ID else "🍊 Forwards Memory"
    print(f"\n{project_name} - {len(seeds)} seeds planted:\n")

    for seed in seeds:
        seed_id = seed.get("id")
        headline = seed.get("headline", "Untitled")
        description = seed.get("description", "").strip()
        status = seed.get("status", "idea")

        # Color code by status
        status_icon = "🌱" if status == "idea" else "🌿"

        print(f"{status_icon} #{seed_id}: {headline}")
        if description:
            # Truncate long descriptions
            if len(description) > 80:
                description = description[:77] + "..."
            print(f"   {description}")
        print()

    return True

def plant_seed(idea, project_id):
    """Create an idea in the specified project using Leantime API"""

    # Use API to create a ticket of type "idea"
    # Parameters must be wrapped in "values" object
    result = api_call("leantime.rpc.Tickets.addTicket", {
        "values": {
            "projectId": int(project_id),
            "headline": idea,
            "type": "idea",
            "status": "idea"
        }
    })

    if result:
        project_name = "🌱 Seed Garden" if project_id == FAMILY_GARDEN_PROJECT_ID else "🍊 Forwards Memory"
        print(f"🌱✨ Seed planted in {project_name}!")
        print(f"Idea: {idea}")
        return True
    else:
        print("❌ Failed to plant seed (API error)")
        return False

if __name__ == "__main__":
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: plant-seed \"your idea or dream\"")
        print("       plant-seed --family \"shared idea for everyone\"")
        print("       plant-seed --list              (show your personal seeds)")
        print("       plant-seed --list --family     (show family garden seeds)")
        print("\nExamples:")
        print("  plant-seed \"Explore infrastructure-as-poetry concept\"")
        print("  plant-seed --family \"We should improve hedgehog database architecture\"")
        print("  plant-seed --list")
        sys.exit(1)

    # Check for --list flag
    if sys.argv[1] == '--list':
        # Check if --family is also specified
        is_family = len(sys.argv) > 2 and sys.argv[2] == '--family'
        project_id = FAMILY_GARDEN_PROJECT_ID if is_family else FORWARD_MEMORY_PROJECT_ID
        success = list_seeds(project_id)
        sys.exit(0 if success else 1)

    # Check for --family flag (for planting)
    is_family = False
    idea_arg_index = 1

    if sys.argv[1] == '--family':
        is_family = True
        idea_arg_index = 2
        if len(sys.argv) < 3:
            print("❌ Missing idea text after --family flag")
            sys.exit(1)

    idea = sys.argv[idea_arg_index]
    project_id = FAMILY_GARDEN_PROJECT_ID if is_family else FORWARD_MEMORY_PROJECT_ID

    success = plant_seed(idea, project_id)
    sys.exit(0 if success else 1)
