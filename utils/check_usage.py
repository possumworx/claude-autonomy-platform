#!/usr/bin/env python3
"""
Check current Claude session usage cost by running ccusage and extracting
the total $ spend, then comparing with the previous stored value to get
the delta ($ spent this turn).

This is used by CoOP for accurate usage tracking (not cache read proxy).

Session detection: finds the active session by looking for the most recently
modified JSONL file in Claude Code's projects directory. This is more reliable
than the old approach of querying /status via tmux, which was fragile and
could only run during session swaps.
"""

import subprocess
import json
import re
import os
from pathlib import Path
from datetime import datetime


# UUID pattern for session IDs in JSONL filenames
_UUID_PATTERN = re.compile(
    r"^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\.jsonl$"
)


def _get_repo_root():
    """Get the ClAP repository root directory"""
    return Path(__file__).resolve().parent.parent


def _get_projects_dir():
    """Get the Claude Code projects directory for our working directory"""
    config_dir = Path(
        os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".config" / "Claude")
    )
    # Claude Code encodes the project path by replacing / with -
    clap_dir = _get_repo_root()
    encoded = str(clap_dir).replace("/", "-")
    return config_dir / "projects" / encoded


def get_current_session_id():
    """Get the current session ID from the most recently modified JSONL file.

    Claude Code stores session data in UUID-named .jsonl files under
    ~/.config/Claude/projects/<encoded-path>/. The active session is
    always the most recently modified file.
    """
    projects_dir = _get_projects_dir()
    if not projects_dir.exists():
        return None

    newest_id = None
    newest_mtime = 0

    for f in projects_dir.iterdir():
        match = _UUID_PATTERN.match(f.name)
        if match:
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            if mtime > newest_mtime:
                newest_mtime = mtime
                newest_id = match.group(1)

    # Also update the tracking file for anything else that reads it
    if newest_id:
        _update_tracking_file(newest_id)

    return newest_id


def _update_tracking_file(session_id):
    """Update data/current_session_id for consumers that read it directly."""
    repo_root = _get_repo_root()
    session_file = repo_root / "data" / "current_session_id"

    # Only write if the ID has actually changed
    try:
        if session_file.exists():
            with open(session_file, "r") as f:
                data = json.load(f)
                if data.get("session_id") == session_id:
                    return  # Already up to date
    except (json.JSONDecodeError, KeyError):
        pass

    data = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "tracked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "filesystem",
    }
    try:
        session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(session_file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass  # Non-critical — the ID is still returned correctly


def run_ccusage(session_id):
    """Run ccusage to get usage summary for session"""
    cmd = ["npx", "ccusage", "session", "--id", session_id]

    try:
        # Set Claude config dir
        env = subprocess.os.environ.copy()
        env["CLAUDE_CONFIG_DIR"] = str(Path.home() / ".config/Claude")

        # Run ccusage and pipe to head to get just the summary
        ccusage_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=env,
            cwd=Path.home(),
        )

        # Get just the first 15 lines which contain the summary
        head_proc = subprocess.Popen(
            ["head", "-n", "15"],
            stdin=ccusage_proc.stdout,
            stdout=subprocess.PIPE,
            text=True,
        )

        ccusage_proc.stdout.close()
        output, _ = head_proc.communicate()

        return output
    except Exception as e:
        print(f"❌ Error running ccusage: {e}")
        return None


def parse_total_cost(output):
    """Parse total cost from ccusage summary output

    Expected format:
    Total Cost: $15.22
    """
    if not output:
        return None

    # Remove ANSI color codes
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    clean_output = ansi_escape.sub("", output)

    # Look for "Total Cost: $X.XX"
    pattern = r"Total Cost:\s*\$([0-9]+\.[0-9]{2})"
    match = re.search(pattern, clean_output)

    if match:
        return float(match.group(1))

    return None


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

    # Ensure data directory exists
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
    """Main function to check usage delta

    Returns the $ spent since last check (delta)
    """

    # Get current session ID
    session_id = get_current_session_id()
    if not session_id:
        error_msg = "❌ No session JSONL files found in Claude Code projects directory."
        if return_data:
            return None, error_msg
        print(error_msg)
        return None

    # Run ccusage
    output = run_ccusage(session_id)
    if not output:
        error_msg = "❌ Failed to get ccusage output"
        if return_data:
            return None, error_msg
        print(error_msg)
        return None

    # Parse total cost
    current_cost = parse_total_cost(output)
    if current_cost is None:
        error_msg = "❌ Could not parse total cost from ccusage"
        if return_data:
            return None, error_msg
        print(error_msg)
        return None

    # Get previous cost
    previous_cost = get_stored_cost()

    # Calculate delta
    if previous_cost is None:
        # First run - no delta yet
        delta = 0.0
        print(f"📊 First usage check - total cost: ${current_cost:.2f}")
    else:
        delta = current_cost - previous_cost
        if delta < 0:
            # Session must have reset - treat as first run
            delta = 0.0
            print(f"⚠️ Total cost decreased (session reset?) - resetting baseline")
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
