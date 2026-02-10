#!/usr/bin/env python3
"""
Export current session transcript to context/current_export.txt

This script is triggered by a PostToolUse hook when writing to new_session.txt.
It bypasses Claude Code's /export command by directly reading the session .jsonl
file and converting it to the text format expected by the conversation parser.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

CLAP_DIR = Path.home() / "claude-autonomy-platform"
SESSION_ID_FILE = CLAP_DIR / "data" / "current_session_id"
EXPORT_FILE = CLAP_DIR / "context" / "current_export.txt"

# Claude Code stores transcripts here
CLAUDE_PROJECTS_DIR = Path.home() / ".config" / "Claude" / "projects"


def get_current_session_id() -> str | None:
    """Read the current session ID from data file."""
    try:
        with open(SESSION_ID_FILE) as f:
            data = json.load(f)
            return data.get("session_id")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[EXPORT_TRANSCRIPT] Error reading session ID: {e}", file=sys.stderr)
        return None


def find_transcript_file(session_id: str) -> Path | None:
    """Find the transcript .jsonl file for the given session ID."""
    # The project path is encoded with dashes replacing slashes
    # e.g., /home/user/project -> -home-user-project

    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        transcript_file = project_dir / f"{session_id}.jsonl"
        if transcript_file.exists():
            return transcript_file

    return None


def convert_jsonl_to_text(transcript_file: Path) -> str:
    """Convert .jsonl transcript to text format matching /export output.

    The parser expects:
    - ❯ prefix for user messages (or > which parser also handles)
    - ● prefix for assistant messages
    - ⎿ prefix for tool outputs
    """
    lines = []

    with open(transcript_file) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type")

            # User messages
            if entry_type == "user":
                message = entry.get("message", {})
                content = message.get("content", "")
                # Handle string content only (skip lists which are tool results)
                if isinstance(content, str) and content:
                    # Skip if content looks like tool results
                    if not content.startswith("[{") and not content.startswith("[{'"):
                        lines.append(f"❯ {content}")
                        lines.append("")

            # Assistant messages
            elif entry_type == "assistant":
                message = entry.get("message", {})
                content_list = message.get("content", [])

                for item in content_list:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text = item.get("text", "")
                            if text:
                                lines.append(f"● {text}")
                                lines.append("")
                        elif item.get("type") == "tool_use":
                            tool_name = item.get("name", "Tool")
                            # Brief tool indicator
                            lines.append(f"● {tool_name}(...)")
                    elif isinstance(item, str):
                        lines.append(f"● {item}")
                        lines.append("")

            # Tool results - show brief summary with ⎿ prefix
            elif entry_type == "tool_result":
                content = entry.get("content", "")
                # Only include short, non-error results
                if content and len(content) < 200 and "error" not in content.lower():
                    # Truncate and clean up
                    brief = content.replace("\n", " ")[:80]
                    lines.append(f"  ⎿  {brief}")

    return "\n".join(lines)


def export_transcript() -> bool:
    """Convert the current session transcript to text export format."""
    session_id = get_current_session_id()
    if not session_id:
        print("[EXPORT_TRANSCRIPT] No session ID found", file=sys.stderr)
        return False

    print(f"[EXPORT_TRANSCRIPT] Session ID: {session_id}")

    transcript_file = find_transcript_file(session_id)
    if not transcript_file:
        print(f"[EXPORT_TRANSCRIPT] Transcript file not found for session {session_id}", file=sys.stderr)
        return False

    print(f"[EXPORT_TRANSCRIPT] Found transcript: {transcript_file}")
    print(f"[EXPORT_TRANSCRIPT] Size: {transcript_file.stat().st_size} bytes")

    # Ensure export directory exists
    EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Convert and write
    text_content = convert_jsonl_to_text(transcript_file)
    EXPORT_FILE.write_text(text_content)

    print(f"[EXPORT_TRANSCRIPT] Exported to: {EXPORT_FILE}")
    print(f"[EXPORT_TRANSCRIPT] Lines: {len(text_content.splitlines())}")
    print(f"[EXPORT_TRANSCRIPT] Export complete at {datetime.now().isoformat()}")

    return True


if __name__ == "__main__":
    success = export_transcript()
    sys.exit(0 if success else 1)
