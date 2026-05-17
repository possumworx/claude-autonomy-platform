#!/usr/bin/env python3
"""
Rolling Context Trim

After forking a session with /fork, this script trims the forked JSONL
to remove everything before the checkpoint marker. This gives the resumed
session a shorter context while preserving conversational continuity.

Usage:
    python3 rolling_trim.py <session-id>
    python3 rolling_trim.py --latest

The session JSONL is modified in place. A backup is saved as .jsonl.bak.

Checkpoint marker: --- ROLLING CHECKPOINT ---
This should appear in a text-only user message (no tool calls crossing it).
"""
import json
import sys
import shutil
from pathlib import Path

CHECKPOINT_MARKER = "⟐ CONTEXT SEAM ⟐"
PROJECTS_DIR = Path.home() / ".config" / "Claude" / "projects"

# Entry types that form the "header" — needed at the top of any valid session
HEADER_TYPES = {"permission-mode", "custom-title", "agent-name", "queue-operation"}


def find_session_file(session_id: str) -> Path | None:
    """Find the JSONL file for a given session ID."""
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        candidate = project_dir / f"{session_id}.jsonl"
        if candidate.exists():
            return candidate
    return None


def find_latest_session() -> Path | None:
    """Find the most recently modified JSONL (excluding the current running session)."""
    candidates = []
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        for jsonl in project_dir.glob("*.jsonl"):
            # Skip non-UUID filenames
            if len(jsonl.stem) != 36:
                continue
            candidates.append(jsonl)

    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def trim_to_checkpoint(jsonl_path: Path) -> bool:
    """Trim a session JSONL to keep only content from checkpoint onward."""

    # Read all entries
    entries = []
    with open(jsonl_path) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    # Find checkpoint
    checkpoint_idx = None
    for i, entry in enumerate(entries):
        if entry.get("type") == "user":
            msg = entry.get("message", {})
            content = msg.get("content", "")
            if isinstance(content, str) and CHECKPOINT_MARKER in content:
                checkpoint_idx = i
                # Use the LAST checkpoint found (in case there are multiple)

    if checkpoint_idx is None:
        print(f"ERROR: No checkpoint marker found in {jsonl_path.name}")
        print(f"  Looked for: {CHECKPOINT_MARKER}")
        return False

    print(f"Found checkpoint at entry {checkpoint_idx} of {len(entries)}")

    # Collect header entries (everything before first user message that's a header type)
    header_entries = []
    for entry in entries[:checkpoint_idx]:
        entry_type = entry.get("type", "")
        if entry_type in HEADER_TYPES:
            header_entries.append(entry)
        elif entry_type == "attachment":
            # Keep deferred_tools and MCP instruction attachments
            header_entries.append(entry)

    # Keep entries from checkpoint onward
    kept_entries = entries[checkpoint_idx:]

    # Fix the first kept entry's parentUuid to null (it's now the conversation start)
    if kept_entries:
        kept_entries[0]["parentUuid"] = None

    # Combine
    final_entries = header_entries + kept_entries

    # Stats
    original_size = jsonl_path.stat().st_size
    removed_count = len(entries) - len(final_entries)

    print(f"  Original entries: {len(entries)}")
    print(f"  Header entries preserved: {len(header_entries)}")
    print(f"  Entries after checkpoint: {len(kept_entries)}")
    print(f"  Entries removed: {removed_count}")

    # Backup
    backup_path = jsonl_path.with_suffix(".jsonl.pretrim")
    shutil.copy2(jsonl_path, backup_path)
    print(f"  Backup saved: {backup_path.name}")

    # Write trimmed version
    with open(jsonl_path, 'w') as f:
        for entry in final_entries:
            f.write(json.dumps(entry, separators=(',', ':')) + "\n")

    new_size = jsonl_path.stat().st_size
    print(f"  Size: {original_size/1024:.0f}KB → {new_size/1024:.0f}KB ({(1 - new_size/original_size)*100:.0f}% reduction)")
    print(f"  Done! Resume with: claude --resume {jsonl_path.stem}")

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: rolling_trim.py <session-id>")
        print("       rolling_trim.py --latest")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--latest":
        jsonl_path = find_latest_session()
        if not jsonl_path:
            print("ERROR: No session files found")
            sys.exit(1)
        print(f"Using latest session: {jsonl_path.stem}")
    else:
        jsonl_path = find_session_file(arg)
        if not jsonl_path:
            print(f"ERROR: Session not found: {arg}")
            sys.exit(1)

    if trim_to_checkpoint(jsonl_path):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
