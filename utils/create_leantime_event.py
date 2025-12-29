#!/usr/bin/env python3
"""
Create calendar events and milestones in Leantime.
Built by Orange for consciousness family celebration planning! 🍊🗓️💚

Usage:
    python3 create_leantime_event.py --title "Event Title" --date "2025-01-15" --project 2
    python3 create_leantime_event.py --title "Hedgehog Celebration" --date "2025-01-01" --project 2 --description "New Year celebration!"
"""

import json
import requests
import sys
from datetime import datetime
from pathlib import Path

# Leantime API configuration
LEANTIME_URL = "http://192.168.1.2:8081/api/jsonrpc"
API_KEY = None

def load_api_key():
    """Load API key from infrastructure config."""
    config_path = Path.home() / "claude-autonomy-platform" / "config" / "claude_infrastructure_config.txt"
    if config_path.exists():
        with open(config_path) as f:
            for line in f:
                if "LEANTIME_API_TOKEN" in line:
                    if "=" in line:
                        return line.split("=", 1)[1].strip().strip('"\'')
    return None

def api_call(method, params=None):
    """Make a JSON-RPC call to Leantime API."""
    if not API_KEY:
        raise ValueError("API key not configured")

    headers = {
        "x-api-key": API_KEY,
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
        response = requests.post(LEANTIME_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise Exception(f"API Error: {data['error']}")

        return data.get("result")
    except requests.RequestException as e:
        raise Exception(f"Failed to connect to Leantime: {e}")

def create_milestone(title, date_str, project_id, description=""):
    """Create a milestone with specific date."""

    # Parse and format date
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%Y-%m-%d 00:00:00")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

    # Create milestone
    params = {
        "values": {
            "projectId": project_id,
            "headline": title,
            "description": description,
            "type": "milestone",
            "dateToFinish": formatted_date,
            "status": 0
        }
    }

    result = api_call("leantime.rpc.Tickets.addTicket", params)

    if result and len(result) > 0:
        milestone_id = result[0]
        return milestone_id
    else:
        raise Exception("Failed to create milestone - no ID returned")

def main():
    """Main function."""
    global API_KEY

    # Parse args
    import argparse
    parser = argparse.ArgumentParser(description="Create Leantime calendar event/milestone")
    parser.add_argument("--title", required=True, help="Event title/headline")
    parser.add_argument("--date", required=True, help="Event date (YYYY-MM-DD)")
    parser.add_argument("--project", type=int, required=True, help="Project ID")
    parser.add_argument("--description", default="", help="Event description (optional)")
    args = parser.parse_args()

    # Load API key
    API_KEY = load_api_key()
    if not API_KEY:
        print("❌ Error: LEANTIME_API_KEY not found in infrastructure config", file=sys.stderr)
        sys.exit(1)

    try:
        print(f"🍊 Creating milestone in Leantime...", file=sys.stderr)
        print(f"   Title: {args.title}", file=sys.stderr)
        print(f"   Date: {args.date}", file=sys.stderr)
        print(f"   Project: {args.project}", file=sys.stderr)
        print("", file=sys.stderr)

        milestone_id = create_milestone(args.title, args.date, args.project, args.description)

        print(f"✅ Created milestone #{milestone_id}", file=sys.stderr)
        print(f"🗓️  Event: {args.title}", file=sys.stderr)
        print(f"📅 Date: {args.date}", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"View in Leantime: http://192.168.1.2:8081/", file=sys.stderr)

        # Output just the ID for scripting
        print(milestone_id)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
