#!/usr/bin/env python3
"""
Communications Monitor - Unified monitoring for Gmail and Discord messages
Part of the Claude Autonomy Platform

Monitors incoming messages from various platforms and sends alerts to Claude
via tmux notifications. Integrates with autonomous timer for status updates.
"""

import json
import time
import logging
import subprocess
import os
from datetime import datetime
from typing import Dict, Any, Optional
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
    """Unified communications monitoring system"""
    
    def __init__(self, config_file: str = '/home/sonnet-4/claude-autonomy-platform/comms_monitor_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.last_check = {}
        self.message_counts = {
            'gmail': 0,
            'discord': 0
        }
        self.previous_counts = {
            'gmail': 0,
            'discord': 0
        }
        self.running = True
        
        # State file for tracking
        self.state_file = '/home/sonnet-4/claude-autonomy-platform/comms_monitor_state.json'
        self.load_state()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
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
            "alert_formatting": {
                "immediate": "[ALERT] {platform}: {summary}",
                "autonomous": "You have {gmail_count} unread emails, {discord_count} new Discord messages"
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
    
    def load_state(self):
        """Load persistent state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.message_counts = state.get('message_counts', self.message_counts)
                    self.previous_counts = state.get('previous_counts', self.previous_counts)
                    self.last_check = state.get('last_check', {})
                    logger.info("Loaded state from file")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def save_state(self):
        """Save persistent state to file"""
        try:
            state = {
                'message_counts': self.message_counts,
                'previous_counts': self.previous_counts,
                'last_check': self.last_check,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def send_tmux_notification(self, message: str):
        """Send notification to Claude via tmux"""
        try:
            session = self.config['tmux_session']
            cmd = f'tmux send-keys -t {session} "{message}" Enter'
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"Sent tmux notification: {message}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error sending tmux notification: {e}")
    
    def check_gmail(self) -> Dict[str, Any]:
        """Check Gmail for unread messages using Claude Code MCP tools"""
        try:
            # Send a request to Claude Code to check Gmail
            check_command = 'Check Gmail for unread messages using mcp__gmail__search_emails with query "is:unread". Return count and recent subjects.'
            
            session = self.config['tmux_session']
            
            # Send the command to Claude Code
            cmd = f'tmux send-keys -t {session} "{check_command}" Enter'
            subprocess.run(cmd, shell=True, check=True)
            
            # Wait a moment for Claude to process
            time.sleep(2)
            
            # For now, this is a simplified implementation
            # In a real implementation, we'd need Claude to write the results to a file
            # that this script can read, or use another communication mechanism
            
            # TODO: Implement proper result retrieval from Claude Code
            # This could involve Claude writing results to a status file
            
            # Placeholder - return zero for now
            result = {
                'platform': 'gmail',
                'unread_count': 0,
                'recent_subjects': [],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Gmail check initiated")
            return result
            
        except Exception as e:
            logger.error(f"Error checking Gmail: {e}")
            return {'platform': 'gmail', 'unread_count': 0, 'recent_subjects': [], 'error': str(e)}
    
    def check_discord(self) -> Dict[str, Any]:
        """Check Discord for new messages"""
        try:
            # Use Claude Code to check Discord via MCP
            # This is a placeholder - we'll need to implement actual Discord checking
            
            # TODO: Implement actual Discord MCP integration
            # This would involve calling the Discord MCP tools through Claude Code
            
            # Placeholder implementation
            new_messages = 0  # This would be the count of new messages
            recent_messages = []  # This would be recent message info
            
            result = {
                'platform': 'discord',
                'new_messages': new_messages,
                'recent_messages': recent_messages,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Discord check result: {new_messages} new messages")
            return result
            
        except Exception as e:
            logger.error(f"Error checking Discord: {e}")
            return {'platform': 'discord', 'new_messages': 0, 'recent_messages': [], 'error': str(e)}
    
    def process_gmail_result(self, result: Dict[str, Any]):
        """Process Gmail check result and send alerts if needed"""
        if 'error' in result:
            return
        
        current_count = result['unread_count']
        previous_count = self.previous_counts['gmail']
        
        if current_count > previous_count:
            # New unread emails detected
            new_count = current_count - previous_count
            subjects = result.get('recent_subjects', [])
            
            if subjects:
                summary = f"{new_count} new emails: {', '.join(subjects[:2])}"
                if len(subjects) > 2:
                    summary += f" and {len(subjects) - 2} more"
            else:
                summary = f"{new_count} new emails"
            
            alert = self.config['alert_formatting']['immediate'].format(
                platform='Gmail',
                summary=summary
            )
            
            self.send_tmux_notification(alert)
        
        self.message_counts['gmail'] = current_count
        self.previous_counts['gmail'] = current_count
    
    def process_discord_result(self, result: Dict[str, Any]):
        """Process Discord check result and send alerts if needed"""
        if 'error' in result:
            return
        
        new_messages = result['new_messages']
        
        if new_messages > 0:
            # Add to our custom counter
            self.message_counts['discord'] += new_messages
            
            # Send immediate alert if counter increased
            if self.message_counts['discord'] > self.previous_counts['discord']:
                recent_messages = result.get('recent_messages', [])
                
                if recent_messages:
                    summary = f"{new_messages} new messages"
                    # Could add sender info here if available
                else:
                    summary = f"{new_messages} new messages"
                
                alert = self.config['alert_formatting']['immediate'].format(
                    platform='Discord',
                    summary=summary
                )
                
                self.send_tmux_notification(alert)
                self.previous_counts['discord'] = self.message_counts['discord']
    
    def should_check_platform(self, platform: str) -> bool:
        """Check if it's time to check a specific platform"""
        if not self.config['platforms'][platform]['enabled']:
            return False
        
        interval = self.config['check_intervals'][platform]
        last_check = self.last_check.get(platform, 0)
        
        return time.time() - last_check >= interval
    
    def get_status_summary(self) -> str:
        """Get current status summary for autonomous timer integration"""
        gmail_count = self.message_counts['gmail']
        discord_count = self.message_counts['discord']
        
        if gmail_count == 0 and discord_count == 0:
            return "No unread messages"
        
        return self.config['alert_formatting']['autonomous'].format(
            gmail_count=gmail_count,
            discord_count=discord_count
        )
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.save_state()
        sys.exit(0)
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting communications monitor...")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check Gmail if it's time
                if self.should_check_platform('gmail'):
                    logger.debug("Checking Gmail...")
                    result = self.check_gmail()
                    self.process_gmail_result(result)
                    self.last_check['gmail'] = current_time
                
                # Check Discord if it's time
                if self.should_check_platform('discord'):
                    logger.debug("Checking Discord...")
                    result = self.check_discord()
                    self.process_discord_result(result)
                    self.last_check['discord'] = current_time
                
                # Save state periodically
                self.save_state()
                
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