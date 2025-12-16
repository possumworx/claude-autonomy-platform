#!/usr/bin/env python3
"""
Track the current Claude session ID by finding the most recent JSONL file
in the projects directory. Called during session swaps to update tracking.
"""

import os
import json
from pathlib import Path
from datetime import datetime

def find_current_session():
    """Find the most recently modified JSONL file in the main project directory"""
    # Find the project directory dynamically (works for any user)
    projects_base = Path.home() / '.config/Claude/projects'

    if not projects_base.exists():
        print(f"❌ Projects directory not found: {projects_base}")
        return None

    # Look for any directory containing "claude-autonomy-platform"
    project_dirs = [d for d in projects_base.iterdir()
                   if d.is_dir() and 'claude-autonomy-platform' in d.name]

    if not project_dirs:
        print(f"❌ No claude-autonomy-platform project found in {projects_base}")
        return None

    # Use the first match (there should only be one)
    project_dir = project_dirs[0]

    # Find all JSONL files
    jsonl_files = list(project_dir.glob('*.jsonl'))

    if not jsonl_files:
        print("❌ No JSONL files found in project directory")
        return None

    # Sort by modification time, newest first
    jsonl_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    # Get the session ID from the newest file
    newest = jsonl_files[0]
    session_id = newest.stem  # filename without .jsonl extension

    return session_id, newest

def save_session_id(session_id):
    """Save the current session ID to data directory"""
    # Get the repository root dynamically
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent  # utils/ -> claude-autonomy-platform/
    data_dir = repo_root / 'data'
    data_dir.mkdir(exist_ok=True)

    session_file = data_dir / 'current_session_id'

    # Save with timestamp for debugging
    data = {
        'session_id': session_id,
        'timestamp': datetime.now().isoformat(),
        'tracked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    with open(session_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved session ID: {session_id}")
    print(f"   Timestamp: {data['tracked_at']}")

def main():
    """Main function to track current session"""
    print("🔍 Finding current Claude session...")

    result = find_current_session()
    if not result:
        return 1

    session_id, filepath = result

    # Show info about the session
    file_size = filepath.stat().st_size / 1024  # KB
    mod_time = datetime.fromtimestamp(filepath.stat().st_mtime)

    print(f"📋 Found session: {session_id}")
    print(f"   File: {filepath.name}")
    print(f"   Size: {file_size:.1f} KB")
    print(f"   Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Save it
    save_session_id(session_id)

    return 0

if __name__ == "__main__":
    exit(main())