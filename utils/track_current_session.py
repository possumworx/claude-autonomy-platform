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
        # Increased from 10.0 to 15.0 to handle "Perusing..." delay
        time.sleep(15.0)
        
        # Capture the pane content BEFORE closing menu
        result = subprocess.run(
            ['tmux', 'capture-pane', '-t', 'autonomous-claude', '-p'],
            check=True,
            capture_output=True,
            text=True
        )
        
        output = result.stdout

        # Send multiple Escape presses to ensure menu closes
        # In case Claude Code isn't immediately ready to accept input,
        # one of these will catch it when it is ready. Extra presses are harmless.
        for i in range(3):
            subprocess.run(
                ['tmux', 'send-keys', '-t', 'autonomous-claude', 'Escape'],
                check=True,
                capture_output=True
            )
            time.sleep(1.0)

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

def log_retry_attempt(attempt_num):
    """Log retry attempt to file for monitoring"""
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    log_dir = repo_root / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / 'session_id_retry.log'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(log_file, 'a') as f:
        f.write(f"{timestamp} - Session ID extraction failed (attempt #{attempt_num})\n")

    print(f"📝 Logged retry attempt #{attempt_num} to {log_file}")

def main():
    """Main function to track current session with infinite retry"""
    print("🔍 Getting current Claude session from /status...")

    attempt = 1
    while True:
        print(f"🔄 Attempt #{attempt}")
        session_id = get_session_id_from_tmux()

        if session_id:
            print(f"✅ Success! Found session: {session_id} (attempt #{attempt})")
            save_session_id(session_id)
            return 0

        print(f"❌ Failed to get session ID (attempt #{attempt})")
        print(f"⏳ Retrying in 30 seconds...")

        # Log failure to file for monitoring
        log_retry_attempt(attempt)

        time.sleep(30.0)
        attempt += 1

if __name__ == "__main__":
    exit(main())
