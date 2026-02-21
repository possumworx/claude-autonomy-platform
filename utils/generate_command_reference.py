#!/usr/bin/env python3
"""
Generate a categorized command reference from wrapper scripts.
Reads the comment line and content of each wrapper to auto-categorize.

Usage:
    python3 generate_command_reference.py              # Print to stdout
    python3 generate_command_reference.py --markdown    # Generate docs/COMMAND_REFERENCE.md
"""

import os
import sys
from pathlib import Path
from datetime import datetime

CLAP_DIR = Path.home() / "claude-autonomy-platform"
WRAPPERS_DIR = CLAP_DIR / "wrappers"

# Category definitions: (category_name, list_of_commands)
# Commands not in any category go to "Other"
CATEGORIES = {
    "Discord": [
        "add_reaction", "delete_message", "edit_message", "fetch_image",
        "mute_channel", "read_messages", "send_file", "send_image",
        "unmute_channel", "write_channel", "edit_status",
    ],
    "Task Management": [
        "task", "task-all", "task-done", "task-start", "task-view", "tasks",
    ],
    "Calendar": [
        "today", "week", "schedule",
    ],
    "Thought Preservation": [
        "care", "ponder", "spark", "wonder", "plant-seed",
    ],
    "System Health & Monitoring": [
        "check_health", "check_emergency", "context", "emergency_shutdown",
        "emergency_signal", "reset_error_state", "temp", "temp-history", "temp-stats",
    ],
    "Navigation & Git": [
        "clap", "home", "gd", "gl", "gs", "oops",
    ],
    "Session & System": [
        "session_swap", "update", "export_prefs", "import_prefs",
    ],
    "Email & Communication": [
        "mail",
    ],
    "Analysis & Memory": [
        "analyze-memory",
    ],
    "Other": [
        "diningroom-peek", "list-commands",
    ],
}


def read_wrapper(path):
    """Read a wrapper and extract description and usage."""
    try:
        with open(path) as f:
            lines = f.readlines()
    except Exception:
        return None, None

    description = None
    usage = None

    for line in lines:
        stripped = line.strip()
        # First comment line after shebang is the description
        if stripped.startswith("# ") and description is None:
            if not stripped.startswith("#!/"):
                description = stripped[2:]
        # Look for usage in comments (line 3 pattern: # Usage: ...)
        if usage is None and stripped.startswith("# Usage:"):
            usage = stripped[2:]  # Keep "Usage: ..." as-is

    # Clean description: strip "(usage: ...)" suffixes since usage is shown separately
    if description and "(usage:" in description.lower():
        idx = description.lower().index("(usage:")
        description = description[:idx].rstrip()

    return description, usage


def get_categorized_commands():
    """Read all wrappers and organize by category."""
    commands = {}

    for wrapper in sorted(WRAPPERS_DIR.iterdir()):
        if not wrapper.is_file() or wrapper.name == "CLAUDE.md":
            continue
        desc, usage = read_wrapper(wrapper)
        commands[wrapper.name] = {
            "description": desc or "(no description)",
            "usage": usage,
        }

    # Build categorized output
    categorized = []
    assigned = set()

    for category, cmd_list in CATEGORIES.items():
        cat_commands = []
        for cmd_name in sorted(cmd_list):
            if cmd_name in commands:
                cat_commands.append((cmd_name, commands[cmd_name]))
                assigned.add(cmd_name)
        if cat_commands:
            categorized.append((category, cat_commands))

    # Catch any uncategorized commands
    uncategorized = []
    for cmd_name in sorted(commands.keys()):
        if cmd_name not in assigned:
            uncategorized.append((cmd_name, commands[cmd_name]))
    if uncategorized:
        categorized.append(("Uncategorized", uncategorized))

    return categorized


def format_terminal(categorized):
    """Format for terminal output."""
    lines = ["=== Command Reference ===", ""]
    for category, cmds in categorized:
        lines.append(f"  [{category}]")
        for name, info in cmds:
            lines.append(f"    {name:<20s} {info['description']}")
        lines.append("")
    lines.append("Use 'type <command>' to see what any command does")
    return "\n".join(lines)


def format_markdown(categorized):
    """Format as markdown document."""
    lines = [
        "# Command Reference",
        "",
        f"Auto-generated from `wrappers/` on {datetime.now().strftime('%Y-%m-%d')}.",
        f"Run `python3 utils/generate_command_reference.py --markdown` to regenerate.",
        "",
        f"**{sum(len(cmds) for _, cmds in categorized)} commands** across "
        f"{len(categorized)} categories.",
        "",
    ]

    # Table of contents
    lines.append("## Categories")
    lines.append("")
    for category, cmds in categorized:
        anchor = category.lower().replace(" ", "-").replace("&", "").replace("  ", "-")
        lines.append(f"- [{category}](#{anchor}) ({len(cmds)})")
    lines.append("")

    # Detail sections
    for category, cmds in categorized:
        lines.append(f"## {category}")
        lines.append("")
        lines.append("| Command | Description |")
        lines.append("|---------|-------------|")
        for name, info in cmds:
            desc = info["description"]
            usage_note = f" — `{info['usage']}`" if info.get("usage") else ""
            lines.append(f"| `{name}` | {desc}{usage_note} |")
        lines.append("")

    return "\n".join(lines)


def main():
    categorized = get_categorized_commands()

    if "--markdown" in sys.argv:
        output = format_markdown(categorized)
        output_path = CLAP_DIR / "docs" / "COMMAND_REFERENCE.md"
        with open(output_path, "w") as f:
            f.write(output + "\n")
        print(f"Written to {output_path}")
    else:
        print(format_terminal(categorized))


if __name__ == "__main__":
    main()
