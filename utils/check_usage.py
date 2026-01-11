#!/usr/bin/env python3
"""
Check current Claude session usage cost by running ccusage and extracting
the total $ spend, then comparing with the previous stored value to get
the delta ($ spent this turn).

This is used by CoOP for accurate usage tracking (not cache read proxy).
"""

import subprocess
import json
import re
from pathlib import Path
from datetime import datetime


def get_current_session_id():
    """Read the current session ID from tracking file"""
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent  # utils/ -> claude-autonomy-platform/
    session_file = repo_root / "data" / "current_session_id"

    if not session_file.exists():
        return None

    try:
        with open(session_file, "r") as f:
            data = json.load(f)
            return data.get("session_id")
    except:
        # Try reading as plain text for backwards compatibility
        try:
            with open(session_file, "r") as f:
                return f.read().strip()
        except:
            return None


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
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
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
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
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
        error_msg = "❌ No current session ID found. Run track_current_session.py first."
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
