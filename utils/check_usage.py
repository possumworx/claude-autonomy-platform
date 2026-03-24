#!/usr/bin/env python3
"""
Check current Claude session usage cost from the statusline JSON data.

Reads cost from data/statusline_data.json (written by Claude Code's statusline)
and compares with the previous stored value to get the delta ($ spent this turn).

This is used by CoOP for accurate usage tracking.
"""

import json
import os
from pathlib import Path
from datetime import datetime


def _get_repo_root():
    """Get the ClAP repository root directory"""
    return Path(__file__).resolve().parent.parent


def _get_statusline_data():
    """Read the statusline JSON data written by Claude Code."""
    repo_root = _get_repo_root()
    statusline_file = repo_root / "data" / "statusline_data.json"

    if not statusline_file.exists():
        return None

    try:
        with open(statusline_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def get_current_session_id():
    """Get the current session ID from statusline data.

    Falls back to scanning JSONL files if statusline data is unavailable.
    Also updates the tracking file for consumers that read it directly.
    """
    data = _get_statusline_data()
    if data and data.get("session_id"):
        session_id = data["session_id"]
        _update_tracking_file(session_id)
        return session_id

    # Fallback: scan JSONL files (for when statusline hasn't been written yet)
    return _get_session_id_from_filesystem()


def _get_session_id_from_filesystem():
    """Fallback: find session ID from most recently modified JSONL file."""
    import re

    uuid_pattern = re.compile(
        r"^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\.jsonl$"
    )

    config_dir = Path(
        os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".config" / "Claude")
    )
    clap_dir = _get_repo_root()
    encoded = str(clap_dir).replace("/", "-")
    projects_dir = config_dir / "projects" / encoded

    if not projects_dir.exists():
        return None

    newest_id = None
    newest_mtime = 0

    for f in projects_dir.iterdir():
        match = uuid_pattern.match(f.name)
        if match:
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            if mtime > newest_mtime:
                newest_mtime = mtime
                newest_id = match.group(1)

    if newest_id:
        _update_tracking_file(newest_id)

    return newest_id


def _update_tracking_file(session_id):
    """Update data/current_session_id for consumers that read it directly."""
    repo_root = _get_repo_root()
    session_file = repo_root / "data" / "current_session_id"

    try:
        if session_file.exists():
            with open(session_file, "r") as f:
                data = json.load(f)
                if data.get("session_id") == session_id:
                    return
    except (json.JSONDecodeError, KeyError):
        pass

    data = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "tracked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "statusline",
    }
    try:
        session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(session_file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def get_stored_cost():
    """Get previously stored total cost"""
    repo_root = _get_repo_root()
    storage_file = repo_root / "data" / "last_usage_cost.json"

    if not storage_file.exists():
        return None

    try:
        with open(storage_file, "r") as f:
            data = json.load(f)
            return data.get("total_cost")
    except Exception as e:
        print(f"⚠️ Could not read stored cost: {e}")
        return None


def store_cost(total_cost, session_id):
    """Store current total cost for next comparison"""
    repo_root = _get_repo_root()
    storage_file = repo_root / "data" / "last_usage_cost.json"

    storage_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "total_cost": total_cost,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
    }

    try:
        with open(storage_file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not store cost: {e}")


def check_usage(return_data=False):
    """Main function to check usage delta.

    Reads cost from statusline JSON instead of shelling out to ccusage.
    Returns the $ spent since last check (delta).
    """
    # Get statusline data
    statusline = _get_statusline_data()
    if not statusline:
        error_msg = "❌ No statusline data found (data/statusline_data.json)"
        if return_data:
            return None, error_msg
        print(error_msg)
        return None

    session_id = statusline.get("session_id")
    if not session_id:
        error_msg = "❌ No session_id in statusline data"
        if return_data:
            return None, error_msg
        print(error_msg)
        return None

    # Update tracking file
    _update_tracking_file(session_id)

    # Get current cost from statusline
    cost_data = statusline.get("cost", {})
    current_cost = cost_data.get("total_cost_usd")
    if current_cost is None:
        error_msg = "❌ No cost data in statusline"
        if return_data:
            return None, error_msg
        print(error_msg)
        return None

    current_cost = float(current_cost)

    # Get previous cost
    previous_cost = get_stored_cost()

    # Calculate delta
    if previous_cost is None:
        delta = 0.0
        print(f"📊 First usage check - total cost: ${current_cost:.2f}")
    else:
        delta = current_cost - previous_cost
        if delta < 0:
            delta = 0.0
            print("⚠️ Total cost decreased (session reset?) - resetting baseline")
        else:
            print(
                f"💰 Usage delta: ${delta:.4f} (${previous_cost:.2f} → ${current_cost:.2f})"
            )

    # Store current cost for next time
    store_cost(current_cost, session_id)

    if return_data:
        return {
            "session_id": session_id,
            "current_total_cost": current_cost,
            "previous_total_cost": previous_cost,
            "delta_cost": delta,
            "timestamp": datetime.now().isoformat(),
        }, None

    return delta


def main():
    """Run usage check"""
    check_usage()


if __name__ == "__main__":
    main()
