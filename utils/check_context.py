#!/usr/bin/env python3
"""
Check current Claude session context usage from the statusline JSON data.

Reads context window information from data/statusline_data.json (written by
Claude Code's statusline) instead of shelling out to ccusage.
"""

import json
from pathlib import Path

# Import shared functions
try:
    from utils.check_usage import get_current_session_id, _get_statusline_data
except ImportError:
    from check_usage import get_current_session_id, _get_statusline_data

# System overhead (system prompt + system tools)
SYSTEM_OVERHEAD = 15600  # tokens

# Warning thresholds
YELLOW_THRESHOLD = 0.70  # 70% = 140k tokens
RED_THRESHOLD = 0.85  # 85% = 170k tokens
TOTAL_CONTEXT = 200000  # 200k token limit


def format_context_display(cache_tokens, total_tokens, percentage):
    """Format context usage for display"""
    if percentage >= RED_THRESHOLD:
        status = "🔴"
    elif percentage >= YELLOW_THRESHOLD:
        status = "🟡"
    else:
        status = "🟢"

    if percentage >= RED_THRESHOLD:
        color = "critical"
    elif percentage >= YELLOW_THRESHOLD:
        color = "warning"
    else:
        color = "good"

    display = f"""
📊 Context Usage Status
═══════════════════════════════
Session tokens: {cache_tokens:,}
System overhead: {SYSTEM_OVERHEAD:,}
───────────────────────────────
Total: {total_tokens:,} / {TOTAL_CONTEXT:,} tokens
Usage: {percentage:.1%} {status}
Free: {TOTAL_CONTEXT - total_tokens:,} tokens ({(1-percentage):.1%})
"""

    return display, color, status


def check_context(return_data=False):
    """Main function to check context usage.

    Reads from statusline JSON instead of shelling out to ccusage.
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

    # Extract context window data (use 'or {}' to handle None values)
    context_window = statusline.get("context_window") or {}
    current_usage = context_window.get("current_usage") or {}

    # Cache read tokens = the main session context size
    cache_tokens = current_usage.get("cache_read_input_tokens", 0)

    # If cache_read is 0, try summing input tokens as fallback
    if cache_tokens == 0:
        cache_tokens = current_usage.get("input_tokens", 0)

    # Calculate total with system overhead
    total_tokens = cache_tokens + SYSTEM_OVERHEAD
    percentage = total_tokens / TOTAL_CONTEXT

    if return_data:
        return {
            "session_id": session_id,
            "cache_tokens": cache_tokens,
            "system_overhead": SYSTEM_OVERHEAD,
            "total_tokens": total_tokens,
            "total_limit": TOTAL_CONTEXT,
            "percentage": percentage,
            "free_tokens": TOTAL_CONTEXT - total_tokens,
            "status": "critical"
            if percentage >= RED_THRESHOLD
            else "warning"
            if percentage >= YELLOW_THRESHOLD
            else "good",
        }, None

    # Display results
    display, color, status = format_context_display(
        cache_tokens, total_tokens, percentage
    )
    print(display)

    return percentage


def main():
    """Run context check"""
    check_context()


if __name__ == "__main__":
    main()
