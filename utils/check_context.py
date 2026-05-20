#!/usr/bin/env python3
"""
Check current Claude session context usage from the statusline JSON data.

Reads context window information from data/statusline_data.json (written by
Claude Code's statusline). Uses the pre-calculated used_percentage from
the statusline as the single source of truth.
"""

import json
from pathlib import Path

# Import shared functions
try:
    from utils.check_usage import get_current_session_id, _get_statusline_data
except ImportError:
    from check_usage import get_current_session_id, _get_statusline_data

# Warning thresholds (as percentages 0-100)
YELLOW_THRESHOLD = 70
RED_THRESHOLD = 85


def format_context_display(used_pct, total_input, window_size):
    """Format context usage for display"""
    if used_pct >= RED_THRESHOLD:
        status = "🔴"
    elif used_pct >= YELLOW_THRESHOLD:
        status = "🟡"
    else:
        status = "🟢"

    color = ("critical" if used_pct >= RED_THRESHOLD
             else "warning" if used_pct >= YELLOW_THRESHOLD
             else "good")

    remaining = window_size - total_input
    remaining_pct = 100 - used_pct

    display = f"""
📊 Context Usage Status
═══════════════════════════════
Total: {total_input:,} / {window_size:,} tokens
Usage: {used_pct:.1f}% {status}
Free: {remaining:,} tokens ({remaining_pct:.1f}%)
"""

    return display, color, status


def check_context(return_data=False):
    """Main function to check context usage.

    Reads used_percentage directly from statusline JSON — the same number
    displayed in the Claude Code status bar and used by the rolling swap hook.
    """
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

    context_window = statusline.get("context_window") or {}
    used_pct = context_window.get("used_percentage", 0)
    total_input = context_window.get("total_input_tokens", 0)
    window_size = context_window.get("context_window_size", 200000)

    if return_data:
        return {
            "session_id": session_id,
            "total_tokens": total_input,
            "total_limit": window_size,
            "percentage": used_pct / 100,  # callers expect 0-1 float
            "free_tokens": window_size - total_input,
            "status": ("critical" if used_pct >= RED_THRESHOLD
                       else "warning" if used_pct >= YELLOW_THRESHOLD
                       else "good"),
        }, None

    display, color, status = format_context_display(
        used_pct, total_input, window_size
    )
    print(display)

    return used_pct / 100  # callers expect 0-1 float


def main():
    """Run context check"""
    check_context()


if __name__ == "__main__":
    main()
