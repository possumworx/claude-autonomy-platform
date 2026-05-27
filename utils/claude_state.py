#!/usr/bin/env python3
"""Claude state manager — single source of truth for presence state.

Writes data/claude_state.json, read by LED daemon, web status, Discord bot.

States: present, thinking, paused, off, error
Plus: dnd (bool) — do not disturb, set by Claude

Usage:
    from claude_state import get_state, set_state, detect_state

    state = detect_state()       # auto-detect from system signals
    data = get_state()           # read current state file
    set_state("present")         # manual override
    set_state("present", dnd=True)
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone

CLAP_DIR = os.environ.get("CLAP_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_FILE = os.path.join(CLAP_DIR, "data", "claude_state.json")
TMUX_SESSION = os.environ.get("TMUX_SESSION", "autonomous-claude")


def get_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"state": "off", "since": _now(), "dnd": False}


def set_state(state, dnd=None):
    current = get_state()
    changed = current.get("state") != state
    data = {
        "state": state,
        "since": _now() if changed else current.get("since", _now()),
        "dnd": dnd if dnd is not None else current.get("dnd", False),
    }
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return data


def detect_state():
    """Auto-detect state from system signals.

    off = API unreachable, out of our hands (lights dark)
    error = Claude process dead or local failure (needs human)
    """
    if not _claude_running():
        return "error"

    if _has_api_error():
        return "off"

    if _is_paused():
        return "paused"

    if _is_thinking():
        return "thinking"

    return "present"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _claude_running():
    try:
        result = subprocess.run(
            ["pgrep", "-f", "claude.*--dangerously-skip-permissions"],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def _is_paused():
    """Check if Claude chose 'wait' — waiting for human connection.

    Timer pause (resume_at in timer_pause.json) controls autonomous prompts.
    LED 'paused' state means 'waiting for human' — only true if Claude
    explicitly chose 'wait', which stores state in autonomy_choice.json.
    """
    choice_file = os.path.join(CLAP_DIR, "data", "autonomy_choice.json")
    if not os.path.exists(choice_file):
        return False
    try:
        with open(choice_file) as f:
            data = json.load(f)
        return data.get("choice") == "wait"
    except Exception:
        return False


def _is_thinking():
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", TMUX_SESSION, "-p", "-e", "-S", "-5"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return False
        return bool(
            __import__("re").search(
                r'\[38;5;(174|20[2-9]|21[0-6])m[^\[]*…',
                result.stdout
            )
        )
    except Exception:
        return False


def _has_api_error():
    error_file = os.path.join(CLAP_DIR, "data", "api_error_state.json")
    if os.path.exists(error_file):
        try:
            with open(error_file) as f:
                data = json.load(f)
            return data.get("error_active", False)
        except Exception:
            pass
    return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        set_state(sys.argv[1])
        print(f"State set to: {sys.argv[1]}")
    else:
        state = detect_state()
        set_state(state)
        print(json.dumps(get_state(), indent=2))
