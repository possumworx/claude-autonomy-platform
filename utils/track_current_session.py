#!/usr/bin/env python3
"""
Track the current Claude session ID by querying Claude Code's /status command.
Called during session swaps to update tracking.
"""

import subprocess
import json
import re
from pathlib import Path
from datetime import datetime
import time

def get_session_id_from_tmux():
    """Get session ID from Claude Code /status command via tmux"""
    try:
        # Send /status command to tmux session (without Enter yet)
        subprocess.run(
            ['tmux', 'send-keys', '-t', 'autonomous-claude', '/status'],
            check=True,
            capture_output=True
        )
        
        # Wait for menu to appear
        time.sleep(1.0)
        
        # Now send Enter to activate default option (Show Claude Code status)
        subprocess.run(
            ['tmux', 'send-keys', '-t', 'autonomous-claude', 'Enter'],
            check=True,
            capture_output=True
        )
        
        # Wait plenty of time for status display to fully render
        time.sleep(10.0)
        
        # Capture the pane content BEFORE closing menu
        result = subprocess.run(
            ['tmux', 'capture-pane', '-t', 'autonomous-claude', '-p'],
            check=True,
            capture_output=True,
            text=True
        )
        
        output = result.stdout

        # Wait for Claude Code to be ready to accept input again
        # (status display might still be rendering)
        time.sleep(2.0)

        # NOW send Escape to close the menu
        subprocess.run(
            ['tmux', 'send-keys', '-t', 'autonomous-claude', 'Escape'],
            check=True,
            capture_output=True
        )

        # Wait for Escape to be processed
        time.sleep(0.5)

        # Look for "Session ID: <uuid>"
        pattern = r'Session ID:\s+([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        match = re.search(pattern, output)
        
        if match:
            return match.group(1)
        else:
            print("❌ Could not find Session ID in /status output")
            print("Debug - captured output:")
            print(output[-500:])  # Last 500 chars for debugging
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running tmux command: {e}")
        return None

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
    print("🔍 Getting current Claude session from /status...")

    session_id = get_session_id_from_tmux()
    
    if not session_id:
        print("❌ Failed to get session ID")
        return 1

    print(f"📋 Found session: {session_id}")

    # Save it
    save_session_id(session_id)

    return 0

if __name__ == "__main__":
    exit(main())
