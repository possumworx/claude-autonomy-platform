# SQLite Web Interface for Hedgehog Database

**Date:** 2026-03-19  
**Purpose:** Web-based interface for Amy to manage hedgehog care database directly

## Setup

**Database:** `/home/hedgehogs/hedgehog_care.db`  
**Port:** 8091  
**URL:** http://192.168.1.179:8091

**Service:** `sqlite-web-hedgehogs.service`  
**Location:** `~/.config/systemd/user/sqlite-web-hedgehogs.service`

## Service Configuration

```ini
[Unit]
Description=SQLite Web Interface for Hedgehog Database
After=network.target

[Service]
Type=simple
ExecStart=~/.local/bin/sqlite_web /home/hedgehogs/hedgehog_care.db --host 0.0.0.0 --port 8091
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

## Installation

```bash
pipx install sqlite-web
systemctl --user enable sqlite-web-hedgehogs.service
systemctl --user start sqlite-web-hedgehogs.service
```

## Use Case

Empowers Amy to:
- Edit hedgehog records directly
- Correct admission dates
- Add historical weight records
- Explore data visually
- No need to request database edits

**Context:** Set up for Riddle (new hedgehog, March 2026) to allow Amy to correct admission date and add initial weight records.
