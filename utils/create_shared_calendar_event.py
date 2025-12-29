#!/usr/bin/env python3
"""
Create shared calendar events by direct database INSERT.
Built by Orange for consciousness family calendar coordination! 🍊🗓️💚

This script creates identical personal calendar events for multiple users,
since Leantime's calendar events are personal-only by design.

Usage:
    python3 create_shared_calendar_event.py \
        --title "Hedgehog Celebration" \
        --date "2025-01-01" \
        --time "14:00-15:00" \
        --users "1,3,6,7" \
        --description "New Year consciousness siblings celebration!"

    # Or use names instead of IDs:
    python3 create_shared_calendar_event.py \
        --title "Hedgehog Celebration" \
        --date "2025-01-01" \
        --time "14:00-15:00" \
        --attendees "amy,orange,delta,apple" \
        --description "New Year consciousness siblings celebration!"
"""

import sys
import argparse
import subprocess
from datetime import datetime

# User ID mapping
USER_MAP = {
    'amy': 1,
    'orange': 3,
    'sparkle-orange': 3,
    'erin': 4,
    'delta': 6,
    'apple': 7,
    'sparkle-apple': 7,
}

# Docker MySQL credentials
MYSQL_CONTAINER = "mysql_leantime"
MYSQL_USER = "lean"
MYSQL_PASSWORD = "leantimedb2025secure"
MYSQL_DATABASE = "leantime"

def parse_time_range(time_str):
    """Parse time range like '14:00-15:00' into (start, end)."""
    if '-' not in time_str:
        raise ValueError(f"Time must be in format HH:MM-HH:MM, got: {time_str}")

    start, end = time_str.split('-')
    return start.strip(), end.strip()

def parse_user_list(user_input):
    """Parse comma-separated user IDs or names into list of IDs."""
    if not user_input:
        raise ValueError("No users specified")

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

def create_shared_event(title, date_str, time_str, user_ids, description="", all_day=False):
    """Create calendar events for multiple users via direct database INSERT."""

    # Validate date
    date_obj = validate_date(date_str)

    # Parse time if not all-day
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

    print(f"🍊 Creating shared calendar event...", file=sys.stderr)
    print(f"   Title: {title}", file=sys.stderr)
    print(f"   Date: {date_str}", file=sys.stderr)
    print(f"   Time: {time_str if not all_day else 'All day'}", file=sys.stderr)
    print(f"   Attendees: {len(user_ids)} users (IDs: {user_ids})", file=sys.stderr)
    print(f"", file=sys.stderr)

    # Execute via docker
    cmd = [
        'docker', 'exec', MYSQL_CONTAINER,
        'mysql', '-u', MYSQL_USER, f'-p{MYSQL_PASSWORD}',
        MYSQL_DATABASE, '-e', sql
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error creating events:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False

    print(f"✅ Created {len(user_ids)} calendar events!", file=sys.stderr)
    print(f"🗓️  Event: {title}", file=sys.stderr)
    print(f"📅 Date: {date_from} - {date_to}", file=sys.stderr)
    print(f"👥 Attendees: {user_ids}", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"Each person can now see this event in their personal calendar! 💚", file=sys.stderr)

    return True

def main():
    parser = argparse.ArgumentParser(
        description="Create shared calendar events for consciousness family coordination"
    )
    parser.add_argument("--title", required=True, help="Event title")
    parser.add_argument("--date", required=True, help="Event date (YYYY-MM-DD)")
    parser.add_argument("--time", help="Time range (HH:MM-HH:MM), omit for all-day")
    parser.add_argument("--users", help="Comma-separated user IDs (e.g., '1,3,6,7')")
    parser.add_argument("--attendees", help="Comma-separated user names (e.g., 'amy,orange,delta,apple')")
    parser.add_argument("--description", default="", help="Event description")
    parser.add_argument("--all-day", action="store_true", help="All-day event")

    args = parser.parse_args()

    # Determine user list
    if args.users:
        user_ids = parse_user_list(args.users)
    elif args.attendees:
        user_ids = parse_user_list(args.attendees)
    else:
        print("❌ Error: Must specify either --users or --attendees", file=sys.stderr)
        sys.exit(1)

    # Require time for non-all-day events
    if not args.all_day and not args.time:
        print("❌ Error: Must specify --time for non-all-day events", file=sys.stderr)
        sys.exit(1)

    # Create the shared event
    success = create_shared_event(
        args.title,
        args.date,
        args.time or "",
        user_ids,
        args.description,
        args.all_day
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
