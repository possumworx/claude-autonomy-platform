#!/usr/bin/env python3
"""
Gmail MCP Monitor - Simple unread count monitoring
Uses existing Gmail MCP authentication, only notifies when count changes
"""

import json
import time
import logging
import subprocess
import signal
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/sonnet-4/claude-autonomy-platform/gmail_mcp_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('gmail_mcp_monitor')

class GmailMCPMonitor:
    """Simple Gmail monitoring using existing MCP authentication"""
    
    def __init__(self, config_file: str = '/home/sonnet-4/claude-autonomy-platform/gmail_mcp_monitor_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.running = True
        self.last_unread_count = 0
        self.state_file = '/home/sonnet-4/claude-autonomy-platform/gmail_mcp_monitor_state.json'
        
        # Load persistent state
        self.load_state()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Gmail MCP monitor initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        default_config = {
            "polling": {
                "interval": 60,  # Check every minute
            },
            "notification": {
                "tmux_session": "autonomous-claude",
                "alert_format": "[ALERT] {count} new emails detected"
            },
            "claude_code": {
                "model": "sonnet",
                "timeout": 30
            }
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
            session = self.config['notification']['tmux_session']
            cmd = f'tmux send-keys -t {session} "{message}" Enter'
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"Sent notification: {message}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def get_unread_count(self) -> Optional[int]:
        """Get unread email count using Gmail MCP"""
        try:
            # Create a simple Python script that uses the Gmail MCP
            script_content = '''
import json
import sys

# Call Gmail MCP to search for unread emails
try:
    # This will be executed in Claude Code context with MCP access
    result = mcp__gmail__search_emails(query="is:unread", maxResults=50)
    
    if result:
        # Count the emails
        email_count = len(result.split("\\n")) - 1  # Subtract 1 for header
        if email_count < 0:
            email_count = 0
        
        print(json.dumps({"unread_count": email_count, "success": True}))
    else:
        print(json.dumps({"unread_count": 0, "success": True}))
        
except Exception as e:
    print(json.dumps({"unread_count": 0, "success": False, "error": str(e)}))
'''
            
            # Write script to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                temp_file = f.name
            
            try:
                # Execute via Claude Code
                cmd = ['claude', '--model', self.config['claude_code']['model'], '--file', temp_file]
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      timeout=self.config['claude_code']['timeout'])
                
                if result.returncode == 0:
                    # Parse the JSON response
                    try:
                        output_lines = result.stdout.strip().split('\n')
                        # Look for the JSON output
                        for line in output_lines:
                            if line.strip().startswith('{'):
                                response = json.loads(line.strip())
                                if response.get('success'):
                                    return response.get('unread_count', 0)
                                else:
                                    logger.error(f"Gmail MCP error: {response.get('error', 'Unknown error')}")
                                    return None
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Claude response: {e}")
                        logger.debug(f"Raw output: {result.stdout}")
                        return None
                else:
                    logger.error(f"Claude command failed: {result.stderr}")
                    return None
                    
            finally:
                # Clean up temp file
                os.unlink(temp_file)
                
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return None
    
    def check_gmail(self):
        """Check Gmail and send notifications if count changed"""
        try:
            current_count = self.get_unread_count()
            
            if current_count is None:
                logger.warning("Failed to get unread count, skipping this check")
                return
            
            logger.debug(f"Current unread count: {current_count}, Previous: {self.last_unread_count}")
            
            if current_count != self.last_unread_count:
                if current_count > self.last_unread_count:
                    # New emails detected
                    new_emails = current_count - self.last_unread_count
                    message = f"[ALERT] {new_emails} new email{'s' if new_emails != 1 else ''} detected (total unread: {current_count})"
                    self.send_notification(message)
                    logger.info(f"New emails detected: {new_emails}")
                else:
                    # Emails were read
                    logger.info(f"Emails were read: {self.last_unread_count - current_count}")
                
                self.last_unread_count = current_count
                self.save_state()
            
        except Exception as e:
            logger.error(f"Error checking Gmail: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.save_state()
        sys.exit(0)
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting Gmail MCP monitor...")
        logger.info(f"Check interval: {self.config['polling']['interval']} seconds")
        
        # Initial check
        self.check_gmail()
        
        while self.running:
            try:
                time.sleep(self.config['polling']['interval'])
                self.check_gmail()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Brief pause before retrying
        
        logger.info("Gmail MCP monitor stopped")

def main():
    """Main entry point"""
    monitor = GmailMCPMonitor()
    monitor.run()

if __name__ == "__main__":
    main()