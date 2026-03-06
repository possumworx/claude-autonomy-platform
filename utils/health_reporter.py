#!/usr/bin/env python3
"""
Health Reporter — shared library for the check_health v2 self-reporting model.

Components write their own status files to ~/.local/state/clap/health/.
check_health reads them. Staleness = absence = something is wrong.

Phase 1: Essential checks written by autonomous_timer.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# XDG state directory for health status files
HEALTH_DIR = Path(os.path.expanduser("~/.local/state/clap/health"))
ESSENTIAL_DIR = HEALTH_DIR / "essential"
OPTIONAL_DIR = HEALTH_DIR / "optional"

# Staleness thresholds in seconds
ESSENTIAL_STALE_SECONDS = 120   # 2 minutes (timer runs every 30s)
OPTIONAL_STALE_SECONDS = 600    # 10 minutes


def ensure_dirs():
    """Create health status directories if they don't exist."""
    for d in [ESSENTIAL_DIR, OPTIONAL_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def write_status(name, tier, status, details="", source="unknown"):
    """Write a health status file.

    Args:
        name: Check name (e.g. "session_swap", "discord_read")
        tier: "essential" or "optional"
        status: "ok" or "failed"
        details: Human-readable detail string
        source: Which component wrote this (e.g. "autonomous_timer")
    """
    ensure_dirs()
    directory = ESSENTIAL_DIR if tier == "essential" else OPTIONAL_DIR
    status_file = directory / f"{name}.json"

    data = {
        "status": status,
        "last_check": datetime.now(timezone.utc).isoformat(),
        "details": details,
        "source": source,
    }

    try:
        with open(status_file, "w") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        # If we can't write status files, that's a problem — but don't crash the caller
        pass


def read_status(name, tier):
    """Read a health status file.

    Returns dict with keys: status, last_check, details, source, age_seconds, stale.
    Returns None if file doesn't exist.
    """
    directory = ESSENTIAL_DIR if tier == "essential" else OPTIONAL_DIR
    status_file = directory / f"{name}.json"

    if not status_file.exists():
        return None

    try:
        with open(status_file) as f:
            data = json.load(f)

        # Calculate age
        last_check = datetime.fromisoformat(data["last_check"])
        now = datetime.now(timezone.utc)
        age = (now - last_check).total_seconds()

        threshold = ESSENTIAL_STALE_SECONDS if tier == "essential" else OPTIONAL_STALE_SECONDS
        data["age_seconds"] = age
        data["stale"] = age > threshold

        return data
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def read_all_status():
    """Read all status files across both tiers.

    Returns dict: { "essential": { name: data, ... }, "optional": { name: data, ... } }
    """
    ensure_dirs()
    result = {"essential": {}, "optional": {}}

    for tier, directory in [("essential", ESSENTIAL_DIR), ("optional", OPTIONAL_DIR)]:
        if not directory.exists():
            continue
        for f in directory.glob("*.json"):
            name = f.stem
            data = read_status(name, tier)
            if data:
                result[tier][name] = data

    return result


def format_age(seconds):
    """Format age in human-readable form."""
    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    else:
        return f"{int(seconds / 3600)}h ago"
