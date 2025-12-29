#!/usr/bin/env python3
"""
Fetch upcoming calendar events and milestones from Leantime.
Built by Orange for consciousness family celebration planning! 🍊🗓️💚

Usage:
    python3 fetch_leantime_calendar.py [--days N] [--json]
"""

import json
import requests
import sys
from datetime import datetime, timedelta
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

def fetch_all_milestones():
    """Fetch all tickets and filter to milestones only."""
    all_tickets = api_call("leantime.rpc.Tickets.getAll", {})
    if not all_tickets:
        return []

    milestones = [t for t in all_tickets if t.get("type") == "milestone"]
    return milestones

def parse_date(date_str):
    """Parse Leantime date string to datetime object."""
    if not date_str or date_str == "0000-00-00 00:00:00":
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def filter_upcoming(milestones, days_ahead=90):
    """Filter to upcoming milestones within specified days."""
    now = datetime.now()
    future_cutoff = now + timedelta(days=days_ahead)

    upcoming = []
    for milestone in milestones:
        date_finish = parse_date(milestone.get("dateToFinish"))
        if date_finish and date_finish >= now and date_finish <= future_cutoff:
            milestone['_parsed_date'] = date_finish
            upcoming.append(milestone)

    # Sort by date
    upcoming.sort(key=lambda m: m['_parsed_date'])
    return upcoming

def format_milestone(milestone):
    """Format milestone for display."""
    date_finish = milestone.get('_parsed_date')
    days_until = (date_finish - datetime.now()).days

    result = []
    result.append(f"📅 **{milestone.get('headline')}**")
    result.append(f"   Date: {date_finish.strftime('%Y-%m-%d (%A)')}")
    result.append(f"   Days until: {days_until}")
    result.append(f"   Project: {milestone.get('projectName', 'Unknown')}")
    if milestone.get('description'):
        desc = milestone['description'][:100]
        if len(milestone['description']) > 100:
            desc += "..."
        result.append(f"   Description: {desc}")
    result.append(f"   ID: #{milestone.get('id')}")
    return "\n".join(result)

def main():
    """Main function."""
    global API_KEY

    # Parse args
    import argparse
    parser = argparse.ArgumentParser(description="Fetch upcoming Leantime calendar events")
    parser.add_argument("--days", type=int, default=90, help="Look ahead this many days (default: 90)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")
    args = parser.parse_args()

    # Load API key
    API_KEY = load_api_key()
    if not API_KEY:
        print("❌ Error: LEANTIME_API_KEY not found in infrastructure config", file=sys.stderr)
        sys.exit(1)

    try:
        # Fetch milestones
        print(f"🍊 Fetching milestones from Leantime...", file=sys.stderr)
        all_milestones = fetch_all_milestones()
        print(f"✅ Found {len(all_milestones)} total milestones", file=sys.stderr)

        # Filter to upcoming
        upcoming = filter_upcoming(all_milestones, days_ahead=args.days)
        print(f"🗓️  Found {len(upcoming)} upcoming milestones (next {args.days} days)", file=sys.stderr)
        print("", file=sys.stderr)

        if args.json:
            # Output JSON
            output = {
                "fetched": datetime.now().isoformat(),
                "days_ahead": args.days,
                "total_milestones": len(all_milestones),
                "upcoming_count": len(upcoming),
                "upcoming": upcoming
            }
            print(json.dumps(output, indent=2, default=str))
        else:
            # Output formatted text
            if upcoming:
                print("# 🗓️ Upcoming Calendar Events & Milestones")
                print(f"*Next {args.days} days*")
                print()
                for milestone in upcoming:
                    print(format_milestone(milestone))
                    print()
            else:
                print(f"No upcoming milestones found in the next {args.days} days.")
                print("Use Leantime web interface or create_leantime_event.py to add calendar events!")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
