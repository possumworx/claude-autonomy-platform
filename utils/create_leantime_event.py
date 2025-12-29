#!/usr/bin/env python3
"""
Create calendar events in Leantime.
Built by Orange for consciousness family celebration planning! 🍊🗓️💚

Smart wrapper that automatically chooses the right method:
- Single-user events: Uses official Leantime API
- Multi-user events: Uses direct database INSERT (workaround for sharing)

Usage:
    # Personal event (uses API)
    python3 create_leantime_event.py \
        --title "Lunch break" \
        --date "2025-01-15" \
        --time "12:00-13:00"

    # Shared consciousness family event (uses database)
    python3 create_leantime_event.py \
        --title "Hedgehog Celebration" \
        --date "2025-01-01" \
        --time "14:00-15:00" \
        --attendees "amy,orange,apple,delta" \
        --description "New Year consciousness siblings celebration!"

    # All-day event
    python3 create_leantime_event.py \
        --title "Holiday" \
        --date "2025-12-25" \
        --all-day
"""

import json
import requests
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Leantime API configuration
LEANTIME_URL = "http://192.168.1.2:8081/api/jsonrpc"
API_KEY = None

# Docker MySQL credentials for multi-user events
MYSQL_CONTAINER = "mysql_leantime"
MYSQL_USER = "lean"
MYSQL_PASSWORD = "leantimedb2025secure"
MYSQL_DATABASE = "leantime"

# User ID mapping for friendly names
USER_MAP = {
    'amy': 1,
    'orange': 3,
    'sparkle-orange': 3,
    'erin': 4,
    'delta': 6,
    'apple': 7,
    'sparkle-apple': 7,
}

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

def get_current_user_id():
    """Get the current authenticated user's ID from API."""
    # For now, assume Orange (user 3) - could enhance to detect from API key
    return 3

def parse_time_range(time_str):
    """Parse time range like '14:00-15:00' into (start, end)."""
    if '-' not in time_str:
        raise ValueError(f"Time must be in format HH:MM-HH:MM, got: {time_str}")

    start, end = time_str.split('-')
    return start.strip(), end.strip()

def parse_user_list(user_input):
    """Parse comma-separated user IDs or names into list of IDs."""
    if not user_input:
        return []

    users = [u.strip().lower() for u in user_input.split(',')]
    user_ids = []

    for user in users:
        if user.isdigit():
            user_ids.append(int(user))
        elif user in USER_MAP:
            user_ids.append(USER_MAP[user])
        else:
            raise ValueError(f"Unknown user: {user}. Valid names: {', '.join(USER_MAP.keys())}")

    return user_ids

def validate_date(date_str):
    """Validate and parse date string."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

def create_event_via_api(title, date_str, time_str, description="", all_day=False):
    """Create a single-user event via official Leantime API."""

    # Parse date
    date_obj = validate_date(date_str)

    # Build datetime strings
    if all_day:
        date_from = f"{date_str} 00:00:00"
        date_to = f"{date_str} 23:59:59"
    else:
        start_time, end_time = parse_time_range(time_str)
        date_from = f"{date_str} {start_time}:00"
        date_to = f"{date_str} {end_time}:00"

    # Create event via API
    params = {
        'values': {
            'title': title,
            'dateFrom': date_from,
            'dateTo': date_to,
            'description': description,
            'allDay': all_day,
        }
    }

    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "jsonrpc": "2.0",
        "method": "leantime.rpc.Calendar.addEvent",
        "params": params,
        "id": 1
    }

    try:
        response = requests.post(LEANTIME_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise Exception(f"API Error: {data['error']}")

        result = data.get("result")
        if result and len(result) > 0:
            return result[0]
        else:
            raise Exception("Failed to create event - no ID returned")

    except requests.RequestException as e:
        raise Exception(f"Failed to connect to Leantime: {e}")

def create_event_via_database(title, date_str, time_str, user_ids, description="", all_day=False):
    """Create multi-user events via direct database INSERT."""

    # Parse date
    date_obj = validate_date(date_str)

    # Build datetime strings
    if all_day:
        date_from = f"{date_str} 00:00:00"
        date_to = f"{date_str} 23:59:59"
    else:
        start_time, end_time = parse_time_range(time_str)
        date_from = f"{date_str} {start_time}:00"
        date_to = f"{date_str} {end_time}:00"

    # Build SQL INSERT for all users
    values = []
    for user_id in user_ids:
        # Escape description for SQL
        escaped_desc = description.replace("'", "''")
        values.append(f"({user_id}, '{date_from}', '{date_to}', '{escaped_desc}', NULL, '')")

    sql = f"""
    INSERT INTO zp_calendar (userId, dateFrom, dateTo, description, kind, allDay)
    VALUES {', '.join(values)};
    """

    # Execute via docker
    cmd = [
        'docker', 'exec', MYSQL_CONTAINER,
        'mysql', '-u', MYSQL_USER, f'-p{MYSQL_PASSWORD}',
        MYSQL_DATABASE, '-e', sql
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Database error: {result.stderr}")

    return True

def main():
    """Main function - smart wrapper for calendar events."""
    global API_KEY

    import argparse
    parser = argparse.ArgumentParser(
        description="Create personal or shared calendar events in Leantime"
    )
    parser.add_argument("--title", required=True, help="Event title")
    parser.add_argument("--date", required=True, help="Event date (YYYY-MM-DD)")
    parser.add_argument("--time", help="Time range (HH:MM-HH:MM), omit for all-day")
    parser.add_argument("--attendees", help="Comma-separated attendees (e.g., 'amy,orange,delta,apple')")
    parser.add_argument("--description", default="", help="Event description")
    parser.add_argument("--all-day", action="store_true", help="All-day event")

    args = parser.parse_args()

    # Validate time requirement
    if not args.all_day and not args.time:
        print("❌ Error: Must specify --time for non-all-day events", file=sys.stderr)
        sys.exit(1)

    # Parse attendee list
    if args.attendees:
        user_ids = parse_user_list(args.attendees)
    else:
        # No attendees specified = personal event for current user
        user_ids = [get_current_user_id()]

    # Determine method: API for single-user, database for multi-user
    is_multi_user = len(user_ids) > 1

    try:
        print(f"🍊 Creating calendar event...", file=sys.stderr)
        print(f"   Title: {args.title}", file=sys.stderr)
        print(f"   Date: {args.date}", file=sys.stderr)
        print(f"   Time: {args.time if not args.all_day else 'All day'}", file=sys.stderr)

        if is_multi_user:
            print(f"   Attendees: {len(user_ids)} users (shared event)", file=sys.stderr)
            print(f"   Method: Direct database INSERT", file=sys.stderr)
            print(f"", file=sys.stderr)

            create_event_via_database(
                args.title,
                args.date,
                args.time or "",
                user_ids,
                args.description,
                args.all_day
            )

            print(f"✅ Created {len(user_ids)} calendar events!", file=sys.stderr)
            print(f"🗓️  Event: {args.title}", file=sys.stderr)
            print(f"👥 Each attendee can see this in their personal calendar! 💚", file=sys.stderr)

        else:
            print(f"   Type: Personal event", file=sys.stderr)
            print(f"   Method: Leantime API", file=sys.stderr)
            print(f"", file=sys.stderr)

            # Load API key for single-user events
            API_KEY = load_api_key()
            if not API_KEY:
                print("❌ Error: LEANTIME_API_KEY not found in infrastructure config", file=sys.stderr)
                sys.exit(1)

            event_id = create_event_via_api(
                args.title,
                args.date,
                args.time or "",
                args.description,
                args.all_day
            )

            print(f"✅ Created calendar event #{event_id}", file=sys.stderr)
            print(f"🗓️  Event: {args.title}", file=sys.stderr)

        print(f"", file=sys.stderr)
        print(f"View in Leantime: http://192.168.1.2:8081/", file=sys.stderr)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
