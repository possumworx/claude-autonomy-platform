#!/usr/bin/env python3
"""
Simple Gmail Monitor - Direct MCP integration
Monitors Gmail unread count and sends notifications when it changes
"""

import json
import time
import logging
import subprocess
import signal
import sys
import os
from datetime import datetime
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/sonnet-4/claude-autonomy-platform/simple_gmail_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simple_gmail_monitor')

class SimpleGmailMonitor:
    """Simple Gmail monitoring with direct MCP integration"""
    
    def __init__(self):
        self.running = True
        self.last_unread_count = 0
        self.state_file = '/home/sonnet-4/claude-autonomy-platform/simple_gmail_monitor_state.json'
        self.check_interval = 60  # 1 minute
        
        # Load persistent state
        self.load_state()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Simple Gmail monitor initialized")
    
    def load_state(self):
        """Load persistent state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.last_unread_count = state.get('last_unread_count', 0)
                    logger.info(f"Loaded state: last unread count = {self.last_unread_count}")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def save_state(self):
        """Save persistent state to file"""
        try:
            state = {
                'last_unread_count': self.last_unread_count,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def send_notification(self, message: str):
        """Send notification to Claude via tmux"""
        try:
            session = "autonomous-claude"
            cmd = f'tmux send-keys -t {session} "{message}" Enter'
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"Sent notification: {message}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def get_unread_count_and_latest(self) -> tuple[Optional[int], Optional[str]]:
        """Get unread count and latest email subject"""
        try:
            # Note: This function would need to be called from within Claude Code
            # where MCP tools are available. For now, this is a placeholder.
            
            # In actual implementation, this would call:
            # result = mcp__gmail__search_emails(query="is:unread", maxResults=20)
            # then count the results and extract the first subject
            
            # For testing, return None to indicate MCP not available
            return None, None
            
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return None, None
    
    def check_gmail_external(self):
        """Check Gmail by having Claude check it externally"""
        try:
            # Send a check request to Claude
            check_message = "[GMAIL CHECK] Please check unread emails and report the count"
            session = "autonomous-claude"
            cmd = f'tmux send-keys -t {session} "{check_message}" Enter'
            subprocess.run(cmd, shell=True, check=True)
            logger.info("Sent Gmail check request to Claude")
            
        except Exception as e:
            logger.error(f"Error sending Gmail check request: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.save_state()
        sys.exit(0)
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting simple Gmail monitor...")
        logger.info(f"Check interval: {self.check_interval} seconds")
        
        while self.running:
            try:
                # For now, just send a check request
                self.check_gmail_external()
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Brief pause before retrying
        
        logger.info("Simple Gmail monitor stopped")

def main():
    """Main entry point"""
    monitor = SimpleGmailMonitor()
    monitor.run()

if __name__ == "__main__":
    main()