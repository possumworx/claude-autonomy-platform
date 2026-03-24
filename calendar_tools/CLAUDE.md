# Calendar Tools

Radicale CalDAV client for shared family calendar.

## Components

- **`radicale_client.py`** — Main CLI tool. Connects to Radicale server on orange-home (192.168.1.179:5233). Supports `today`, `week`, and `schedule` subcommands.
- **`whats_planned_today.sh`** — Simple shell wrapper for today's events (used by autonomous timer).

## Access

Wrappers in `wrappers/` provide natural commands:
- `today` — Show today's events
- `week` — Show next 7 days
- `schedule "Event" "start" "end" ["description"]` — Create event

## Usage Examples

### radicale_client.py
```bash
# Show today's events
python3 radicale_client.py --user orange --password "YOUR_PASSWORD" today

# Show this week's events
python3 radicale_client.py --user amy --password "YOUR_PASSWORD" week

# Create a new event
python3 radicale_client.py --user orange --password "YOUR_PASSWORD" create \
    "Team Meeting" \
    "2026-01-02 14:00" \
    "2026-01-02 15:00" \
    "Weekly sync"
```

### whats_planned_today.sh
```bash
# Check Orange's calendar
./whats_planned_today.sh orange

# Check Amy's calendar
./whats_planned_today.sh amy
```

### Session Swap Integration
Add to session swap prompts to show planned activities:
```bash
$(~/claude-autonomy-platform/calendar_tools/whats_planned_today.sh orange)
```

## Dependencies

- **python3-caldav** - CalDAV protocol client
- **python3-icalendar** - iCalendar format parsing
- **python3-pytz** - Timezone support

## Web Interface

For visual calendar management, access Radicale web UI:
- **URL**: http://127.0.0.1:5232/.web
- Login with your username/password
- Create/edit/delete calendars and events
- Changes sync immediately with CalDAV clients

## Troubleshooting

### Connection Errors
If you see connection errors, check:
```bash
# Is Radicale running?
sudo systemctl status radicale.service

# Is it listening on port 5232?
ss -tlnp | grep 5232
```

### Authentication Errors
Verify credentials in `/home/clap-admin/.config/radicale/users`:
```bash
sudo -u clap-admin cat /home/clap-admin/.config/radicale/users
```

## Notes

- Requires `caldav` Python module — needs venv setup (pip install blocked by externally-managed-environment on Debian)
- Credentials in `config/claude_infrastructure_config.txt` (RADICALE_URL, RADICALE_USER, RADICALE_PASSWORD)
- Each family member has their own calendar space on the server
- DateTime format: `YYYY-MM-DD HH:MM`
