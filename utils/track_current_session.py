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
    project_dir = Path.home() / '.config/Claude/projects/-home-delta-claude-autonomy-platform'

    if not project_dir.exists():
        print(f"❌ Project directory not found: {project_dir}")
        return None

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
    data_dir = Path.home() / 'claude-autonomy-platform/data'
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