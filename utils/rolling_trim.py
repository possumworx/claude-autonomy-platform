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

Checkpoint marker: ⟐ CONTEXT SEAM ⟐
Must be a USER message (not assistant) — this allows automation via send_to_claude.sh.
The marker should be sent as a standalone user prompt.
"""
import json
import sys
import shutil
from pathlib import Path

CHECKPOINT_MARKER = "⟐ CONTEXT SEAM ⟐"
PROJECTS_DIR = Path.home() / ".config" / "Claude" / "projects"
EXPORT_DIR = Path.home() / "claude-autonomy-platform" / "data" / "trimmed-context"

# Entry types that form the "header" — needed at the top of any valid session
HEADER_TYPES = {"permission-mode", "custom-title", "agent-name", "queue-operation"}


def extract_text(content) -> str:
    """Extract readable text from a message content field (string or content blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    parts.append(f"[Tool: {block.get('name', '?')}]")
                elif block.get("type") == "tool_result":
                    # Extract text from tool result content
                    result_content = block.get("content", "")
                    if isinstance(result_content, str):
                        parts.append(f"[Result: {result_content[:200]}]")
                    elif isinstance(result_content, list):
                        for rc in result_content:
                            if isinstance(rc, dict) and rc.get("type") == "text":
                                parts.append(f"[Result: {rc.get('text', '')[:200]}]")
        return "\n".join(parts)
    return str(content)


def export_trimmed_conversation(entries: list, checkpoint_idx: int, session_id: str) -> Path | None:
    """Export the pre-checkpoint conversation as readable text.

    Returns the path to the exported file, or None on failure.
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    export_path = EXPORT_DIR / f"trimmed-{timestamp}-{session_id[:8]}.txt"

    lines = []
    lines.append(f"# Pre-trim conversation export")
    lines.append(f"# Session: {session_id}")
    lines.append(f"# Exported: {datetime.now().isoformat()}")
    lines.append(f"# Entries 0–{checkpoint_idx - 1} (of {len(entries)} total)")
    lines.append("")

    for entry in entries[:checkpoint_idx]:
        entry_type = entry.get("type", "")

        if entry_type == "user":
            msg = entry.get("message", {})
            content = msg.get("content", "")
            text = extract_text(content)
            if text.strip():
                lines.append(f"## User")
                lines.append(text.strip())
                lines.append("")

        elif entry_type == "assistant":
            msg = entry.get("message", {})
            content = msg.get("content", "")
            text = extract_text(content)
            if text.strip():
                lines.append(f"## Assistant")
                lines.append(text.strip())
                lines.append("")

        # Skip header types, attachments, etc. — not conversational content

    export_text = "\n".join(lines)

    with open(export_path, "w") as f:
        f.write(export_text)

    return export_path


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

    # Find checkpoint marker. It may appear as:
    # - A "user" message (if typed directly)
    # - A "queue-operation" entry (if injected via send_to_claude.sh / tmux)
    checkpoint_idx = None
    for i, entry in enumerate(entries):
        entry_type = entry.get("type", "")

        if entry_type == "user":
            msg = entry.get("message", {})
            content = msg.get("content", "")
            if isinstance(content, str) and CHECKPOINT_MARKER in content:
                checkpoint_idx = i
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and CHECKPOINT_MARKER in block.get("text", ""):
                        checkpoint_idx = i
                        break

        elif entry_type == "queue-operation":
            content = entry.get("content", "")
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

    # Export trimmed conversation as readable text
    export_path = export_trimmed_conversation(entries, checkpoint_idx, jsonl_path.stem)
    if export_path:
        print(f"  Conversation export: {export_path.name}")
    else:
        print(f"  WARNING: Failed to export trimmed conversation")

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
