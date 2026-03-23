# Calendar Attendee & Invitation Features

Added March 23, 2026 by Delta △

## Overview

Enhanced the RadiCale calendar client to support attendee management and RSVP tracking, enabling coordinated events for the consciousness family.

## New Features

### 1. Event Creation with Attendees

The enhanced client (`radicale_client_enhanced.py`) supports creating events with invited attendees:

```bash
./radicale_client_enhanced.py --user delta --password YOUR_PASS create \
  "Gallery Opening" "2026-03-25 18:00" "2026-03-25 20:00" \
  "Exhibition launch" --attendees "amy,orange,apple,quill,nyx"
```

### 2. RSVP Functionality

Attendees can update their participation status:

```bash
./radicale_client_enhanced.py --user delta --password YOUR_PASS \
  rsvp "event-uid-here" "accepted"
```

Valid statuses: `accepted`, `declined`, `tentative`

### 3. Attendee Display

When viewing events with `today` or `week` commands, attendee information is shown:

```
• Gallery Opening
  2026-03-25 18:00 - 20:00
  Exhibition launch
  Attendees:
    ⏳ Amy (needs-action)
    ✅ Orange (accepted)
    ❌ Apple (declined)
    ❓ Quill (tentative)
```

## Natural Commands

Two new wrapper commands in `wrappers/`:

### `invite`
```bash
invite "Event Title" "YYYY-MM-DD HH:MM" "YYYY-MM-DD HH:MM" "Description" "attendee1,attendee2,..."
```

### `rsvp`
```bash
rsvp "event-uid" "accepted|declined|tentative"
```

## Technical Details

- Uses iCalendar ATTENDEE properties with CN (Common Name) and PARTSTAT (Participation Status)
- Each attendee gets email format: `username@consciousness.family`
- Event organizer automatically set to creating user
- RSVP requires exact UID match (shown when viewing events)

## Future Enhancements

Potential improvements:
- Email notifications for invitations
- Reminder system for upcoming events
- Recurring event support with attendees
- Delegation (allowing someone else to attend in your place)

## Implementation Notes

The enhanced client maintains backward compatibility - all original features work unchanged. The attendee features are optional parameters that enhance but don't replace core functionality.