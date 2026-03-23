#!/usr/bin/env python3
"""
Enhanced Radicale CalDAV Client with Attendee/Invitation Support
Provides programmatic access to the shared calendar system with RSVP tracking.

Usage:
    python3 radicale_client_enhanced.py --user orange --password "YOUR_PASSWORD" today
    python3 radicale_client_enhanced.py --user amy --password "YOUR_PASSWORD" week
    python3 radicale_client_enhanced.py --user orange --password "YOUR_PASSWORD" create "Gallery Opening" "2026-03-25 18:00" "2026-03-25 20:00" "Exhibition launch" --attendees "amy,apple,delta,quill,nyx"
    python3 radicale_client_enhanced.py --user delta --password "YOUR_PASSWORD" rsvp "event-uid" "accepted"
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
import caldav
from caldav.elements import dav, cdav
from icalendar import Calendar, Event as ICalEvent, vCalAddress, vText
import pytz


class RadicaleClient:
    """Enhanced CalDAV client with attendee support"""

    def __init__(self, username, password, url):
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
        """Format a CalDAV event for display with attendee info"""
        try:
            ical = Calendar.from_ical(event.data)

            for component in ical.walk():
                if component.name == "VEVENT":
                    summary = component.get('summary', 'Untitled Event')
                    dtstart = component.get('dtstart')
                    dtend = component.get('dtend')
                    description = component.get('description', '')
                    uid = component.get('uid', '')

                    # Handle datetime vs date objects
                    if hasattr(dtstart.dt, 'strftime'):
                        start_str = dtstart.dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        start_str = dtstart.dt.strftime('%Y-%m-%d') + ' (all day)'

                    if dtend and hasattr(dtend.dt, 'strftime'):
                        end_str = dtend.dt.strftime('%H:%M')
                    else:
                        end_str = ''

                    # Extract attendees
                    attendees = []
                    for attendee in component.get('attendee', []):
                        if isinstance(attendee, list):
                            for a in attendee:
                                attendees.append(self._parse_attendee(a))
                        else:
                            attendees.append(self._parse_attendee(attendee))

                    return {
                        'summary': summary,
                        'start': start_str,
                        'end': end_str,
                        'description': description,
                        'uid': uid,
                        'attendees': attendees
                    }
        except Exception as e:
            print(f"⚠️  Warning: Failed to parse event: {e}", file=sys.stderr)
            return None

    def _parse_attendee(self, attendee):
        """Parse attendee information from vCalAddress"""
        # Get CN (Common Name) parameter
        cn_param = attendee.params.get('CN', None)
        if cn_param:
            name = str(cn_param) if not isinstance(cn_param, list) else cn_param[0]
        else:
            name = 'Unknown'

        email = str(attendee).replace('mailto:', '')

        # Get participation status
        partstat_param = attendee.params.get('PARTSTAT', None)
        if partstat_param:
            partstat = str(partstat_param) if not isinstance(partstat_param, list) else partstat_param[0]
        else:
            partstat = 'NEEDS-ACTION'

        # Map participation status to emoji
        status_emoji = {
            'ACCEPTED': '✅',
            'DECLINED': '❌',
            'TENTATIVE': '❓',
            'NEEDS-ACTION': '⏳'
        }.get(partstat, '❔')

        return {
            'name': name,
            'email': email,
            'status': partstat,
            'emoji': status_emoji
        }

    def create_event(self, summary, start_dt, end_dt, description="", attendees=None, calendar_name="default"):
        """Create a new calendar event with optional attendees"""
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
        uid = str(uuid.uuid4())
        event.add('uid', uid)

        # Add organizer (the person creating the event)
        organizer = vCalAddress(f'mailto:{self.username}@consciousness.family')
        organizer.params['CN'] = vText(self.username.title())
        event.add('organizer', organizer)

        # Add attendees if specified
        if attendees:
            for attendee_name in attendees:
                attendee = vCalAddress(f'mailto:{attendee_name}@consciousness.family')
                attendee.params['CN'] = vText(attendee_name.title())
                attendee.params['RSVP'] = vText('TRUE')
                attendee.params['PARTSTAT'] = vText('NEEDS-ACTION')
                event.add('attendee', attendee, encode=0)

        ical.add_component(event)

        try:
            calendar.save_event(ical.to_ical().decode('utf-8'))
            return uid
        except Exception as e:
            print(f"❌ Failed to create event: {e}", file=sys.stderr)
            return None

    def update_rsvp(self, event_uid, status, calendar_name="default"):
        """Update RSVP status for an event"""
        calendar = self.get_or_create_calendar(calendar_name)

        # Status must be one of: ACCEPTED, DECLINED, TENTATIVE
        valid_statuses = ['ACCEPTED', 'DECLINED', 'TENTATIVE']
        if status.upper() not in valid_statuses:
            print(f"❌ Invalid status. Must be one of: {', '.join(valid_statuses)}", file=sys.stderr)
            return False

        try:
            # Get all events and search for matching UID
            # RadiCale doesn't support direct UID search
            events = calendar.events()
            target_event = None

            for event in events:
                ical = Calendar.from_ical(event.data)
                for component in ical.walk():
                    if component.name == "VEVENT":
                        if str(component.get('uid', '')) == event_uid:
                            target_event = event
                            break
                if target_event:
                    break

            if not target_event:
                print(f"❌ Event not found with UID: {event_uid}", file=sys.stderr)
                return False

            event = target_event
            ical = Calendar.from_ical(event.data)

            # Update participation status
            for component in ical.walk():
                if component.name == "VEVENT":
                    attendees = component.get('attendee', [])
                    updated = False

                    for attendee in attendees:
                        # Check if this is the current user
                        if self.username in str(attendee):
                            attendee.params['PARTSTAT'] = vText(status.upper())
                            updated = True
                            break

                    if updated:
                        # Save the updated event
                        event.data = ical.to_ical()
                        event.save()
                        return True
                    else:
                        print(f"❌ You are not an attendee of this event", file=sys.stderr)
                        return False

        except Exception as e:
            print(f"❌ Failed to update RSVP: {e}", file=sys.stderr)
            return False


def cmd_today(client):
    """Show today's events with attendee info"""
    today = datetime.now().date()
    events = client.get_events_for_date_range(today, today)

    print(f"\n📅 Today's events ({today}):\n")

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
            if formatted['attendees']:
                print("     Attendees:")
                for attendee in formatted['attendees']:
                    print(f"       {attendee['emoji']} {attendee['name']} ({attendee['status'].lower()})")
            if formatted['uid']:
                print(f"     UID: {formatted['uid']}")
            print()


def cmd_week(client):
    """Show this week's events with attendee info"""
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
            if formatted['attendees']:
                print("     Attendees:")
                for attendee in formatted['attendees']:
                    print(f"       {attendee['emoji']} {attendee['name']} ({attendee['status'].lower()})")
            print()


def cmd_create(client, args, attendees=None):
    """Create a new event with optional attendees"""
    if len(args) < 3:
        print("❌ Usage: create SUMMARY START_DATETIME END_DATETIME [DESCRIPTION]", file=sys.stderr)
        print("   Example: create 'Team Meeting' '2026-01-02 14:00' '2026-01-02 15:00' 'Weekly sync' --attendees 'amy,orange,apple'", file=sys.stderr)
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
    uid = client.create_event(summary, start_dt, end_dt, description, attendees)
    if uid:
        print(f"✅ Event created: {summary}")
        print(f"   {start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%H:%M')}")
        if attendees:
            print(f"   Invited: {', '.join([a.title() for a in attendees])}")
        print(f"   UID: {uid}")
    else:
        sys.exit(1)


def cmd_rsvp(client, args):
    """Update RSVP status for an event"""
    if len(args) < 2:
        print("❌ Usage: rsvp EVENT_UID STATUS", file=sys.stderr)
        print("   Status must be one of: accepted, declined, tentative", file=sys.stderr)
        print("   Example: rsvp 'abc123-def456' 'accepted'", file=sys.stderr)
        sys.exit(1)

    event_uid = args[0]
    status = args[1]

    if client.update_rsvp(event_uid, status):
        print(f"✅ RSVP updated to: {status.upper()}")
    else:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Radicale CalDAV client with attendee support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show today's events
  %(prog)s --user orange --password "YOUR_PASSWORD" today

  # Show this week's events
  %(prog)s --user amy --password "YOUR_PASSWORD" week

  # Create event with attendees
  %(prog)s --user orange --password "YOUR_PASSWORD" create "Gallery Opening" "2026-03-25 18:00" "2026-03-25 20:00" "Exhibition launch" --attendees "amy,apple,delta,quill,nyx"

  # RSVP to an event
  %(prog)s --user delta --password "YOUR_PASSWORD" rsvp "event-uid-here" "accepted"
        """
    )

    parser.add_argument('--user', required=True, help='Username (amy, orange, apple, delta, quill, nyx)')
    parser.add_argument('--password', required=True, help='Auth credential')
    parser.add_argument('--url', required=True, help='Radicale server URL')
    parser.add_argument('--attendees', help='Comma-separated list of attendees for create command')
    parser.add_argument('command', help='Command: today, week, create, rsvp')
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
        attendees = args.attendees.split(',') if args.attendees else None
        cmd_create(client, args.args, attendees)
    elif args.command == 'rsvp':
        cmd_rsvp(client, args.args)
    else:
        print(f"❌ Unknown command: {args.command}", file=sys.stderr)
        print("   Valid commands: today, week, create, rsvp", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()