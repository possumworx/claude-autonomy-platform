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
from claude_paths import get_clap_dir

# Get dynamic paths
clap_dir = get_clap_dir()

TRIGGER_FILE = clap_dir / "new_session.txt"
SCRIPT_PATH = clap_dir / "session_swap.sh"
LOG_PATH = clap_dir / "logs" / "session_swap_monitor.log"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    with open(LOG_PATH, "a") as f:
        f.write(log_entry + "\n")

def ping_healthcheck():
    """Ping healthchecks.io to signal service is alive"""
    try:
        result = subprocess.run([
            'curl', '-fsS', '-m', '10', '--retry', '3', '-o', '/dev/null',
            'https://hc-ping.com/116e5fcc-35e7-4d85-bd10-5688c114816c'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            log(f"Healthcheck ping failed: {result.stderr}")
            return False
    except Exception as e:
        log(f"Healthcheck ping error: {e}")
        return False

def main():
    log("Session swap monitor starting...")
    
    # Create trigger file if it doesn't exist
    if not os.path.exists(TRIGGER_FILE):
        with open(TRIGGER_FILE, 'w') as f:
            f.write("FALSE\n")
    
    while True:
        try:
            # Ping healthcheck every cycle
            ping_healthcheck()
            
            if os.path.exists(TRIGGER_FILE):
                with open(TRIGGER_FILE, 'r') as f:
                    content = f.read().strip().upper()
                
                # Valid keywords for context hats system
                valid_keywords = {"TRUE", "AUTONOMY", "BUSINESS", "CREATIVE", "HEDGEHOGS", "NONE"}
                
                if content in valid_keywords:
                    log(f"Session swap triggered with keyword: {content}")
                    
                    # Reset trigger file to FALSE
                    with open(TRIGGER_FILE, 'w') as f:
                        f.write("FALSE\n")
                    
                    # Run the session swap script with keyword argument
                    try:
                        result = subprocess.run([SCRIPT_PATH, content], 
                                              capture_output=True, 
                                              text=True, 
                                              timeout=30)
                        log(f"Session swap completed. Return code: {result.returncode}")
                        if result.stdout:
                            log(f"Output: {result.stdout}")
                        if result.stderr:
                            log(f"Error: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        log("Session swap timed out")
                    except Exception as e:
                        log(f"Error running session swap: {e}")
            
            time.sleep(2)  # Check every 2 seconds
            
        except KeyboardInterrupt:
            log("Session swap monitor stopping...")
            break
        except Exception as e:
            log(f"Error in session swap monitor: {e}")
            time.sleep(5)  # Wait longer on errors

if __name__ == "__main__":
    main()