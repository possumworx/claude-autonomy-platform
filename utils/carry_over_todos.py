#!/usr/bin/env python3
"""
Carry Over Todos Script
Copies non-completed todos from the previous Claude Code session to the new one.
Part of the forwards-memory system for maintaining task continuity across session swaps.
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime

def send_to_claude(message):
    """Send a message to Claude session using send_to_claude.py"""
    try:
        script_path = Path(__file__).parent / "send_to_claude.py"
        subprocess.run([str(script_path), message], check=False)
    except Exception:
        pass  # Silently fail if send_to_claude isn't available

def get_todo_files():
    """Get the two most recent todo files, sorted by modification time"""
    todos_dir = Path.home() / ".config" / "Claude" / "todos"

    if not todos_dir.exists():
        print(f"[CARRY_TODOS] Todos directory not found: {todos_dir}")
        return None, None

    # Get all .json files, sorted by modification time (newest first)
    json_files = sorted(
        todos_dir.glob("*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    if len(json_files) < 2:
        print(f"[CARRY_TODOS] Not enough todo files to carry over (found {len(json_files)})")
        return None, None

    newest = json_files[0]
    second_newest = json_files[1]

    print(f"[CARRY_TODOS] Newest todo file: {newest.name}")
    print(f"[CARRY_TODOS] Previous todo file: {second_newest.name}")

    return newest, second_newest

def load_todos(file_path):
    """Load todos from a JSON file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            if not content or content == "[]":
                return []
            return json.loads(content)
    except Exception as e:
        print(f"[CARRY_TODOS] Error loading {file_path.name}: {e}")
        return []

def save_todos(file_path, todos):
    """Save todos to a JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(todos, f, indent=2)
        return True
    except Exception as e:
        print(f"[CARRY_TODOS] Error saving to {file_path.name}: {e}")
        return False

def filter_non_completed(todos):
    """Filter out completed todos, keeping only pending and in_progress"""
    return [
        todo for todo in todos
        if todo.get("status") != "completed"
    ]

def main():
    """Main execution"""
    print("[CARRY_TODOS] Starting todo carry-over process...")

    # Get the two most recent todo files
    newest_file, previous_file = get_todo_files()

    if not newest_file or not previous_file:
        print("[CARRY_TODOS] Skipping carry-over - insufficient files")
        return

    # Load todos from previous session
    previous_todos = load_todos(previous_file)

    if not previous_todos:
        print("[CARRY_TODOS] No todos in previous session - nothing to carry over")
        return

    # Filter out completed todos
    non_completed = filter_non_completed(previous_todos)

    if not non_completed:
        print("[CARRY_TODOS] All todos in previous session were completed - nothing to carry over")
        return

    print(f"[CARRY_TODOS] Found {len(non_completed)} non-completed todo(s) to carry over:")
    for i, todo in enumerate(non_completed, 1):
        status = todo.get("status", "unknown")
        content = todo.get("content", "")
        print(f"  {i}. [{status}] {content[:60]}{'...' if len(content) > 60 else ''}")

    # Check current state of newest file
    current_todos = load_todos(newest_file)

    if current_todos:
        print(f"[CARRY_TODOS] WARNING: Newest file already has {len(current_todos)} todo(s)")
        print("[CARRY_TODOS] Merging with carried-over todos...")
        # Merge: carried-over todos first, then any existing ones
        merged_todos = non_completed + current_todos
    else:
        print("[CARRY_TODOS] Newest file is empty - writing carried-over todos")
        merged_todos = non_completed

    # Save to newest file
    if save_todos(newest_file, merged_todos):
        print(f"[CARRY_TODOS] ✅ Successfully carried over {len(non_completed)} todo(s)")
    else:
        error_msg = f"⚠️ Todo carry-over FAILED: Could not save {len(non_completed)} todo(s) to new session. Task continuity may be lost."
        print(f"[CARRY_TODOS] ❌ {error_msg}")
        send_to_claude(error_msg)
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
