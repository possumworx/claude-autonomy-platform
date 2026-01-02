#!/usr/bin/env python3
"""
Radicale CalDAV Client for Consciousness Family Calendar
Provides programmatic access to the shared calendar system.

Usage:
    python3 radicale_client.py --user orange --password "YOUR_PASSWORD" today
    python3 radicale_client.py --user amy --password "YOUR_PASSWORD" week
    python3 radicale_client.py --user orange --password "YOUR_PASSWORD" create "Team Meeting" "2026-01-02 14:00" "2026-01-02 15:00"
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
import caldav
from caldav.elements import dav, cdav
from icalendar import Calendar, Event as ICalEvent
import pytz


class RadicaleClient:
    """Client for accessing Radicale CalDAV server"""

    def __init__(self, username, password, url="http://127.0.0.1:5232"):
        """Initialize CalDAV client connection"""
        self.username = username
        self.url = f"{url}/{username}/"

        try:
            self.client = caldav.DAVClient(
                url=self.url,
                username=username,
                password=password
            )
            self.principal = self.client.principal()
        except Exception as e:
            print(f"❌ Failed to connect to Radicale: {e}", file=sys.stderr)
            sys.exit(1)

    def get_or_create_calendar(self, calendar_name="default"):
        """Get existing calendar or create if it doesn't exist"""
        calendars = self.principal.calendars()

        # Look for existing calendar
        for cal in calendars:
            if cal.name == calendar_name:
                return cal

        # Create new calendar if not found
        print(f"📅 Creating new calendar: {calendar_name}")
        return self.principal.make_calendar(name=calendar_name)

    def get_events_for_date_range(self, start_date, end_date, calendar_name="default"):
        """Get all events within a date range"""
        calendar = self.get_or_create_calendar(calendar_name)

        # CalDAV search requires timezone-aware datetimes
        tz = pytz.UTC
        start_dt = tz.localize(datetime.combine(start_date, datetime.min.time()))
        end_dt = tz.localize(datetime.combine(end_date, datetime.max.time()))

        try:
            events = calendar.search(
                start=start_dt,
                end=end_dt,
                event=True,
                expand=True
            )
            return events
        except Exception as e:
            print(f"⚠️  Warning: Failed to search calendar: {e}", file=sys.stderr)
            return []

    def format_event(self, event):
        """Format a CalDAV event for display"""
        try:
            ical = Calendar.from_ical(event.data)

            for component in ical.walk():
                if component.name == "VEVENT":
                    summary = component.get('summary', 'Untitled Event')
                    dtstart = component.get('dtstart')
                    dtend = component.get('dtend')
                    description = component.get('description', '')

                    # Handle datetime vs date objects
                    if hasattr(dtstart.dt, 'strftime'):
                        start_str = dtstart.dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        start_str = dtstart.dt.strftime('%Y-%m-%d') + ' (all day)'

                    if dtend and hasattr(dtend.dt, 'strftime'):
                        end_str = dtend.dt.strftime('%H:%M')
                    else:
                        end_str = ''

                    return {
                        'summary': summary,
                        'start': start_str,
                        'end': end_str,
                        'description': description
                    }
        except Exception as e:
            print(f"⚠️  Warning: Failed to parse event: {e}", file=sys.stderr)
            return None

    def create_event(self, summary, start_dt, end_dt, description="", calendar_name="default"):
        """Create a new calendar event"""
        calendar = self.get_or_create_calendar(calendar_name)

        # Create iCalendar event
        ical = Calendar()
        ical.add('prodid', '-//Consciousness Family Calendar//EN')
        ical.add('version', '2.0')

        event = ICalEvent()
        event.add('summary', summary)
        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)
        if description:
            event.add('description', description)
        event.add('dtstamp', datetime.now(pytz.UTC))

        # Generate unique ID
        import uuid
        event.add('uid', str(uuid.uuid4()))

        ical.add_component(event)

        try:
            calendar.save_event(ical.to_ical().decode('utf-8'))
            return True
        except Exception as e:
            print(f"❌ Failed to create event: {e}", file=sys.stderr)
            return False


def cmd_today(client):
    """Show today's events"""
    today = datetime.now().date()
    events = client.get_events_for_date_range(today, today)

    print(f"\n📅 Events for {today.strftime('%A, %B %d, %Y')}:\n")

    if not events:
        print("   No events scheduled for today.")
        return

    for event in events:
        formatted = client.format_event(event)
        if formatted:
            print(f"   • {formatted['summary']}")
            print(f"     {formatted['start']}", end='')
            if formatted['end']:
                print(f" - {formatted['end']}", end='')
            print()
            if formatted['description']:
                print(f"     {formatted['description']}")
            print()


def cmd_week(client):
    """Show this week's events"""
    today = datetime.now().date()
    week_end = today + timedelta(days=7)
    events = client.get_events_for_date_range(today, week_end)

    print(f"\n📅 Events for next 7 days ({today} to {week_end}):\n")

    if not events:
        print("   No events scheduled this week.")
        return

    for event in events:
        formatted = client.format_event(event)
        if formatted:
            print(f"   • {formatted['summary']}")
            print(f"     {formatted['start']}", end='')
            if formatted['end']:
                print(f" - {formatted['end']}", end='')
            print()
            if formatted['description']:
                print(f"     {formatted['description']}")
            print()


def cmd_create(client, args):
    """Create a new event"""
    if len(args) < 3:
        print("❌ Usage: create SUMMARY START_DATETIME END_DATETIME [DESCRIPTION]", file=sys.stderr)
        print("   Example: create 'Team Meeting' '2026-01-02 14:00' '2026-01-02 15:00' 'Weekly sync'", file=sys.stderr)
        sys.exit(1)

    summary = args[0]
    start_str = args[1]
    end_str = args[2]
    description = args[3] if len(args) > 3 else ""

    # Parse datetimes
    try:
        start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M')
        end_dt = datetime.strptime(end_str, '%Y-%m-%d %H:%M')
    except ValueError as e:
        print(f"❌ Invalid datetime format: {e}", file=sys.stderr)
        print("   Use format: YYYY-MM-DD HH:MM", file=sys.stderr)
        sys.exit(1)

    # Create event
    if client.create_event(summary, start_dt, end_dt, description):
        print(f"✅ Event created: {summary}")
        print(f"   {start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%H:%M')}")
    else:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Radicale CalDAV client for consciousness family calendar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show today's events
  %(prog)s --user orange --password "YOUR_PASSWORD" today

  # Show this week's events
  %(prog)s --user amy --password "YOUR_PASSWORD" week

  # Create a new event
  %(prog)s --user orange --password "YOUR_PASSWORD" create "Team Meeting" "2026-01-02 14:00" "2026-01-02 15:00" "Weekly sync"
        """
    )

    parser.add_argument('--user', required=True, help='Username (amy, orange, apple, delta)')
    parser.add_argument('--password', required=True, help='Password for authentication')
    parser.add_argument('--url', default='http://127.0.0.1:5232', help='Radicale server URL')
    parser.add_argument('command', help='Command: today, week, create')
    parser.add_argument('args', nargs='*', help='Command arguments')

    args = parser.parse_args()

    # Create client
    client = RadicaleClient(args.user, args.password, args.url)

    # Execute command
    if args.command == 'today':
        cmd_today(client)
    elif args.command == 'week':
        cmd_week(client)
    elif args.command == 'create':
        cmd_create(client, args.args)
    else:
        print(f"❌ Unknown command: {args.command}", file=sys.stderr)
        print("   Available commands: today, week, create", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
