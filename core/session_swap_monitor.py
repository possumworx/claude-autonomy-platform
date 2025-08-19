#!/usr/bin/env python3
"""
Session Swap Monitor Service
Watches for new_session.txt to be set to TRUE, then runs session swap script
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
LOG_PATH = clap_dir / "data" / "session_swap_monitor.log"
TMUX_SESSION = "autonomous-claude"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    with open(LOG_PATH, "a") as f:
        f.write(log_entry + "\n")

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
    
    while True:
        try:
            # Check if trigger file exists and read content
            if TRIGGER_FILE.exists():
                content = TRIGGER_FILE.read_text().strip()
                
                # Check if content is a valid trigger
                if content != "FALSE" and content != "":
                    # Valid keywords: AUTONOMY, BUSINESS, CREATIVE, HEDGEHOGS, NONE, or TRUE
                    keyword = content if content in ["AUTONOMY", "BUSINESS", "CREATIVE", "HEDGEHOGS", "NONE"] else "NONE"
                    
                    # Reset trigger file immediately
                    TRIGGER_FILE.write_text("FALSE")
                    
                    # Run session swap
                    run_session_swap(keyword)
            
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