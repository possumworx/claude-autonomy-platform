#!/usr/bin/env python3
"""
Communications Monitor (Simplified) - Schedules communication checks for Claude
Part of the Claude Autonomy Platform

Sends scheduled requests to Claude to check Gmail and Discord, letting Claude
handle the actual MCP tool calls and immediate notifications.
"""

import json
import time
import logging
import subprocess
import os
from datetime import datetime
from typing import Dict, Any
import signal
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/sonnet-4/claude-autonomy-platform/comms_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('comms_monitor')

class CommsMonitor:
    """Simplified communications monitoring - schedules checks for Claude"""
    
    def __init__(self, config_file: str = '/home/sonnet-4/claude-autonomy-platform/comms_monitor_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.last_check = {}
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Communications monitor initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        default_config = {
            "check_intervals": {
                "gmail": 180,      # 3 minutes
                "discord": 30      # 30 seconds
            },
            "platforms": {
                "gmail": {"enabled": True},
                "discord": {"enabled": True}
            },
            "tmux_session": "autonomous-claude"
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                # Create default config file
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default config file: {self.config_file}")
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return default_config
    
    def send_check_request(self, platform: str):
        """Send a request to Claude to check a specific platform"""
        try:
            session = self.config['tmux_session']
            
            if platform == 'gmail':
                message = "[COMMS CHECK] Please check Gmail for unread messages and report any new ones."
            elif platform == 'discord':
                message = "[COMMS CHECK] Please check Discord for new messages and report any new ones."
            else:
                logger.error(f"Unknown platform: {platform}")
                return
            
            cmd = f'tmux send-keys -t {session} "{message}" Enter'
            subprocess.run(cmd, shell=True, check=True)
            
            logger.info(f"Sent {platform} check request to Claude")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error sending {platform} check request: {e}")
    
    def should_check_platform(self, platform: str) -> bool:
        """Check if it's time to check a specific platform"""
        if not self.config['platforms'][platform]['enabled']:
            return False
        
        interval = self.config['check_intervals'][platform]
        last_check = self.last_check.get(platform, 0)
        
        return time.time() - last_check >= interval
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        sys.exit(0)
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting communications monitor...")
        logger.info(f"Gmail check interval: {self.config['check_intervals']['gmail']} seconds")
        logger.info(f"Discord check interval: {self.config['check_intervals']['discord']} seconds")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check if it's time to request Gmail check
                if self.should_check_platform('gmail'):
                    self.send_check_request('gmail')
                    self.last_check['gmail'] = current_time
                
                # Check if it's time to request Discord check
                if self.should_check_platform('discord'):
                    self.send_check_request('discord')
                    self.last_check['discord'] = current_time
                
                # Sleep for 10 seconds before next check
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(10)
        
        logger.info("Communications monitor stopped")

def main():
    """Main entry point"""
    monitor = CommsMonitor()
    monitor.run()

if __name__ == "__main__":
    main()