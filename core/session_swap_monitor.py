#!/usr/bin/env python3
"""
Session Swap Monitor Service
Watches for new_session.txt to be set to TRUE, then runs session swap script
Also monitors /tmp/amy-to-delta.fifo for incoming messages from Amy
"""

import time
import os
import subprocess
from pathlib import Path
from datetime import datetime
import select
import stat

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
FIFO_PATH = "/tmp/amy-to-delta.fifo"
TMUX_SESSION = "autonomous-claude"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    with open(LOG_PATH, "a") as f:
        f.write(log_entry + "\n")

def check_fifo():
    """Check if FIFO has data and send to tmux if it does"""
    try:
        # Check if FIFO exists and is a named pipe
        if not os.path.exists(FIFO_PATH):
            return
        
        if not stat.S_ISFIFO(os.stat(FIFO_PATH).st_mode):
            return
        
        # Non-blocking read from FIFO
        try:
            with open(FIFO_PATH, 'r', os.O_NONBLOCK) as fifo:
                # Use select to check if data is available
                readable, _, _ = select.select([fifo], [], [], 0)
                if readable:
                    message = fifo.read().strip()
                    if message:
                        log(f"Received tellclaude message: {message}")
                        # Send to tmux
                        subprocess.run(['tmux', 'send-keys', '-t', TMUX_SESSION, message], 
                                     capture_output=True)
                        subprocess.run(['tmux', 'send-keys', '-t', TMUX_SESSION, 'Enter'], 
                                     capture_output=True)
        except (IOError, OSError):
            # FIFO not ready or no data
            pass
    except Exception as e:
        log(f"Error checking FIFO: {e}")

def ping_healthcheck():
    """Ping healthchecks.io to signal service is alive"""
    try:
        ping_url = get_config_value('SESSION_SWAP_PING', 'https://hc-ping.com/116e5fcc-35e7-4d85-bd10-5688c114816c')
        result = subprocess.run([
            'curl', '-fsS', '-m', '10', '--retry', '3', '-o', '/dev/null',
            ping_url
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
            
            # Check for tellclaude messages
            check_fifo()
            
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
                                              timeout=60)
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