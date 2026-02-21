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

## Notes

- Requires `caldav` Python module — needs venv setup (pip install blocked by externally-managed-environment on Debian)
- Credentials in `config/claude_infrastructure_config.txt` (RADICALE_URL, RADICALE_USER, RADICALE_PASSWORD)
- Each family member has their own calendar space on the server
- See `README.md` for detailed setup instructions
