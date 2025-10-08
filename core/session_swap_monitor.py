#!/usr/bin/env python3
"""
Session Swap Monitor Service
Watches for new_session.txt to be set to TRUE, then runs session swap script
Also sends regular heartbeat pings to prove the monitoring service is alive
"""

import time
import os
import subprocess
from pathlib import Path
from datetime import datetime

# Import path utilities
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from claude_paths import get_clap_dir
from infrastructure_config_reader import get_config_value

# Get dynamic paths
clap_dir = get_clap_dir()

TRIGGER_FILE = clap_dir / "new_session.txt"
SCRIPT_PATH = clap_dir / "utils" / "session_swap.sh"
LOG_PATH = clap_dir / "logs" / "session_swap_monitor.log"
TMUX_SESSION = "autonomous-claude"
HEARTBEAT_INTERVAL = 300  # 5 minutes in seconds

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    with open(LOG_PATH, "a") as f:
        f.write(log_entry + "\n")

def send_heartbeat():
    """Send heartbeat ping to healthchecks.io to prove service is alive"""
    try:
        # Get healthcheck URL from config
        ping_url = get_config_value("SESSION_SWAP_PING")
        if ping_url:
            result = subprocess.run(
                ["curl", "-m", "10", "--retry", "2", ping_url],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                log("Heartbeat ping sent successfully")
            else:
                log(f"Heartbeat ping failed: {result.stderr}")
        else:
            log("Warning: SESSION_SWAP_PING not configured")
    except Exception as e:
        log(f"Error sending heartbeat: {e}")

def run_session_swap(keyword="NONE"):
    """Run the session swap script with the given keyword"""
    log(f"Running session swap with keyword: {keyword}")
    try:
        result = subprocess.run([str(SCRIPT_PATH), keyword],
                              capture_output=True, text=True)
        log(f"Session swap completed: {result.returncode}")
        if result.stdout:
            log(f"Output: {result.stdout}")
        if result.stderr:
            log(f"Error: {result.stderr}")
    except Exception as e:
        log(f"Error running session swap: {e}")

def main():
    log("Session swap monitor service started")

    # Ensure trigger file exists with default value
    if not TRIGGER_FILE.exists():
        TRIGGER_FILE.write_text("FALSE")
        log(f"Created trigger file: {TRIGGER_FILE}")

    # Track last heartbeat time
    last_heartbeat = 0

    # Send initial heartbeat on startup
    send_heartbeat()
    last_heartbeat = time.time()

    while True:
        try:
            # Check if it's time for a heartbeat ping
            current_time = time.time()
            if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
                send_heartbeat()
                last_heartbeat = current_time

            # Check if trigger file exists and read content
            if TRIGGER_FILE.exists():
                content = TRIGGER_FILE.read_text().strip()

                # Check if content is a valid trigger
                if content != "FALSE" and content != "":
                    # Valid keywords: AUTONOMY, BUSINESS, CREATIVE, HEDGEHOGS, NONE, or TRUE
                    keyword = content if content in ["AUTONOMY", "BUSINESS", "CREATIVE", "HEDGEHOGS", "NONE"] else "NONE"

                    # Run session swap
                    run_session_swap(keyword)

                    # Reset trigger file only after successful completion
                    TRIGGER_FILE.write_text("FALSE")
                    log("Reset trigger file to FALSE after swap completion")

                    # Note: session_swap.sh will also send its own ping on successful completion
                    # This is fine - heartbeat proves service is alive, swap ping confirms operation

            # Sleep for a short interval
            time.sleep(2)

        except KeyboardInterrupt:
            log("Service stopped by user")
            break
        except Exception as e:
            log(f"Error in main loop: {e}")
            time.sleep(5)  # Sleep longer on error

if __name__ == "__main__":
    main()