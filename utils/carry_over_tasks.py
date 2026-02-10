#!/usr/bin/env python3
"""
Carry Over Tasks Script
Copies non-completed tasks from the previous Claude Code session to the new one.
Part of the forwards-memory system for maintaining task continuity across session swaps.

Updated 2026-02-04: Rewritten for new Task tools format
  - Old: ~/.config/Claude/todos/*.json (array format)
  - New: ~/.config/Claude/tasks/<session-id>/*.json (individual files)
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

def get_current_session_id():
    """Get the actual current session ID from saved tracking data"""
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    session_file = repo_root / 'data' / 'current_session_id'

    if not session_file.exists():
        return None

    try:
        with open(session_file, 'r') as f:
            data = json.load(f)
            return data.get('session_id')
    except Exception as e:
        print(f"[CARRY_TASKS] Error reading current session ID: {e}")
        return None

def get_session_dirs():
    """Get current and previous session directories using actual session ID tracking"""
    tasks_dir = Path.home() / ".config" / "Claude" / "tasks"

    if not tasks_dir.exists():
        print(f"[CARRY_TASKS] Tasks directory not found: {tasks_dir}")
        return None, None

    # Get ACTUAL current session ID from tracking data
    current_session_id = get_current_session_id()

    if not current_session_id:
        print("[CARRY_TASKS] WARNING: Could not get current session ID from tracking data")
        print("[CARRY_TASKS] Falling back to modification time detection (may be unreliable)")
        # Fall back to old behavior
        session_dirs = sorted(
            [d for d in tasks_dir.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True
        )
        if len(session_dirs) < 2:
            print(f"[CARRY_TASKS] Not enough session directories to carry over (found {len(session_dirs)})")
            return None, None
        newest = session_dirs[0]
        second_newest = session_dirs[1]
        print(f"[CARRY_TASKS] Current session (by mtime): {newest.name}")
        print(f"[CARRY_TASKS] Previous session (by mtime): {second_newest.name}")
        return newest, second_newest

    current_session = tasks_dir / current_session_id

    # Get all other session directories sorted by mtime (most recent previous session)
    other_sessions = sorted(
        [d for d in tasks_dir.iterdir() if d.is_dir() and d.name != current_session_id],
        key=lambda d: d.stat().st_mtime,
        reverse=True
    )

    if not other_sessions:
        print(f"[CARRY_TASKS] No previous session found to carry over from")
        return None, None

    previous_session = other_sessions[0]

    print(f"[CARRY_TASKS] Current session (from tracking): {current_session.name}")
    print(f"[CARRY_TASKS] Previous session (most recent): {previous_session.name}")

    return current_session, previous_session

def load_tasks_from_session(session_dir):
    """Load all tasks from a session directory"""
    tasks = []

    # Load all .json files (excluding lock files and metadata)
    for task_file in session_dir.glob("*.json"):
        try:
            with open(task_file, 'r') as f:
                task = json.load(f)
                tasks.append(task)
        except Exception as e:
            print(f"[CARRY_TASKS] Error loading {task_file.name}: {e}")

    return tasks

def filter_non_completed(tasks):
    """Filter out completed and deleted tasks, keeping only pending and in_progress"""
    return [
        task for task in tasks
        if task.get("status") not in ["completed", "deleted"]
    ]

def get_next_task_id(session_dir):
    """Get the next available task ID in the new session"""
    existing_ids = []

    for task_file in session_dir.glob("*.json"):
        try:
            with open(task_file, 'r') as f:
                task = json.load(f)
                existing_ids.append(int(task.get("id", 0)))
        except:
            pass

    # Return next ID (or 1 if no tasks exist)
    return max(existing_ids, default=0) + 1

def save_task(session_dir, task, new_id=None):
    """Save a task to the session directory with a new ID if specified"""
    try:
        # Use new ID if provided, otherwise keep original
        if new_id is not None:
            task["id"] = str(new_id)

        task_file = session_dir / f"{task['id']}.json"

        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)

        return True
    except Exception as e:
        print(f"[CARRY_TASKS] Error saving task {task.get('id')}: {e}")
        return False

def main():
    """Main execution"""
    print("[CARRY_TASKS] Starting task carry-over process...")

    # Get the two most recent session directories
    newest_session, previous_session = get_session_dirs()

    if not newest_session or not previous_session:
        print("[CARRY_TASKS] Skipping carry-over - insufficient sessions")
        return 0

    # Load tasks from previous session
    previous_tasks = load_tasks_from_session(previous_session)

    if not previous_tasks:
        print("[CARRY_TASKS] No tasks in previous session - nothing to carry over")
        return 0

    # Filter out completed/deleted tasks
    non_completed = filter_non_completed(previous_tasks)

    if not non_completed:
        print("[CARRY_TASKS] All tasks in previous session were completed - nothing to carry over")
        return 0

    print(f"[CARRY_TASKS] Found {len(non_completed)} non-completed task(s) to carry over:")
    for task in non_completed:
        status = task.get("status", "unknown")
        subject = task.get("subject", "Untitled")
        print(f"  #{task['id']} [{status}] {subject[:60]}{'...' if len(subject) > 60 else ''}")

    # Check if newest session already has tasks
    current_tasks = load_tasks_from_session(newest_session)

    if current_tasks:
        print(f"[CARRY_TASKS] WARNING: Newest session already has {len(current_tasks)} task(s)")
        print("[CARRY_TASKS] Assigning new IDs to carried-over tasks to avoid conflicts...")

        # Get the next available ID
        next_id = get_next_task_id(newest_session)

        # Save carried-over tasks with new IDs
        saved_count = 0
        for task in non_completed:
            if save_task(newest_session, task, new_id=next_id):
                saved_count += 1
                next_id += 1

        if saved_count == len(non_completed):
            print(f"[CARRY_TASKS] ✅ Successfully carried over {saved_count} task(s) with new IDs")
            return 0
        else:
            error_msg = f"⚠️ Task carry-over PARTIAL: Only {saved_count}/{len(non_completed)} tasks carried over. Check session directory."
            print(f"[CARRY_TASKS] ⚠️ {error_msg}")
            send_to_claude(error_msg)
            return 1
    else:
        print("[CARRY_TASKS] Newest session is empty - writing carried-over tasks with original IDs")

        # Save tasks with original IDs
        saved_count = 0
        for task in non_completed:
            if save_task(newest_session, task):
                saved_count += 1

        if saved_count == len(non_completed):
            print(f"[CARRY_TASKS] ✅ Successfully carried over {saved_count} task(s)")
            return 0
        else:
            error_msg = f"⚠️ Task carry-over FAILED: Only {saved_count}/{len(non_completed)} tasks saved to new session. Task continuity may be lost."
            print(f"[CARRY_TASKS] ❌ {error_msg}")
            send_to_claude(error_msg)
            return 1

if __name__ == "__main__":
    exit(main())
