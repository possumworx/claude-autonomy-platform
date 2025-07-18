#!/usr/bin/env python3
"""
Gmail Real-time Monitor using IMAP IDLE
Provides real-time notifications when new emails arrive
"""

import imaplib
import email
import time
import threading
import logging
import json
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
        logging.FileHandler('/home/sonnet-4/claude-autonomy-platform/gmail_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('gmail_monitor')

class GmailRealtimeMonitor:
    """Real-time Gmail monitoring using IMAP IDLE"""
    
    def __init__(self, config_file: str = '/home/sonnet-4/claude-autonomy-platform/gmail_monitor_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.imap = None
        self.running = True
        self.idle_thread = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Gmail real-time monitor initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        default_config = {
            "gmail": {
                "email": "claude.sonnet4home@gmail.com",
                "password": "***GMAIL_PASSWORD_REMOVED***",  # App password
                "imap_server": "imap.gmail.com",
                "imap_port": 993
            },
            "notification": {
                "tmux_session": "autonomous-claude",
                "alert_format": "[ALERT] New email from {sender}: \"{subject}\""
            },
            "monitoring": {
                "check_interval": 30,  # seconds between connection checks
                "max_retries": 3
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
    
    def connect_to_gmail(self) -> bool:
        """Connect to Gmail via IMAP"""
        try:
            gmail_config = self.config['gmail']
            
            # Connect to Gmail IMAP
            self.imap = imaplib.IMAP4_SSL(
                gmail_config['imap_server'], 
                gmail_config['imap_port']
            )
            
            # Login
            self.imap.login(
                gmail_config['email'], 
                gmail_config['password']
            )
            
            # Select INBOX
            self.imap.select('INBOX')
            
            logger.info("Successfully connected to Gmail IMAP")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {e}")
            return False
    
    def send_notification(self, message: str):
        """Send notification to Claude via tmux"""
        try:
            session = self.config['notification']['tmux_session']
            cmd = f'tmux send-keys -t {session} "{message}" Enter'
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"Sent notification: {message}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def get_latest_email_info(self) -> Optional[Dict[str, str]]:
        """Get information about the most recent email"""
        try:
            # Search for all emails
            status, messages = self.imap.search(None, 'ALL')
            
            if status == 'OK' and messages[0]:
                # Get the latest email ID
                email_ids = messages[0].split()
                if email_ids:
                    latest_id = email_ids[-1]
                    
                    # Fetch the email
                    status, msg_data = self.imap.fetch(latest_id, '(RFC822)')
                    
                    if status == 'OK':
                        # Parse the email
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Extract key information
                        sender = email_message.get('From', 'Unknown')
                        subject = email_message.get('Subject', 'No Subject')
                        date = email_message.get('Date', 'Unknown')
                        
                        # Clean up sender (remove email formatting)
                        if '<' in sender:
                            sender = sender.split('<')[0].strip().strip('"')
                        
                        return {
                            'sender': sender,
                            'subject': subject,
                            'date': date,
                            'id': latest_id.decode()
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest email info: {e}")
            return None
    
    def check_for_new_emails(self):
        """Check for new emails and send notifications"""
        try:
            # Check for new emails
            status, response = self.imap.search(None, 'UNSEEN')
            
            if status == 'OK' and response[0]:
                # Get unseen email IDs
                unseen_ids = response[0].split()
                
                if unseen_ids:
                    logger.info(f"Found {len(unseen_ids)} new emails")
                    
                    # Get info about the most recent new email
                    latest_unseen = unseen_ids[-1]
                    status, msg_data = self.imap.fetch(latest_unseen, '(RFC822)')
                    
                    if status == 'OK':
                        # Parse the email
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Extract key information
                        sender = email_message.get('From', 'Unknown')
                        subject = email_message.get('Subject', 'No Subject')
                        
                        # Clean up sender
                        if '<' in sender:
                            sender = sender.split('<')[0].strip().strip('"')
                        
                        # Send notification
                        alert_format = self.config['notification']['alert_format']
                        message = alert_format.format(sender=sender, subject=subject)
                        
                        if len(unseen_ids) > 1:
                            message += f" (and {len(unseen_ids) - 1} more)"
                        
                        self.send_notification(message)
            
        except Exception as e:
            logger.error(f"Error checking for new emails: {e}")
    
    def idle_loop(self):
        """Main IDLE loop for real-time monitoring"""
        logger.info("Starting IDLE loop...")
        
        while self.running:
            try:
                # Send IDLE command
                self.imap.send(b'IDLE\r\n')
                
                # Wait for response or timeout
                response = self.imap.readline()
                
                if b'EXISTS' in response or b'RECENT' in response:
                    # New email detected!
                    logger.info("New email detected via IDLE")
                    
                    # End IDLE mode
                    self.imap.send(b'DONE\r\n')
                    self.imap.readline()  # Read the completion response
                    
                    # Check for new emails
                    self.check_for_new_emails()
                    
                    # Small delay before resuming IDLE
                    time.sleep(2)
                
                elif b'OK' in response:
                    # IDLE command accepted, continue
                    continue
                
                else:
                    # Unexpected response, reconnect
                    logger.warning(f"Unexpected IDLE response: {response}")
                    break
                    
            except Exception as e:
                logger.error(f"Error in IDLE loop: {e}")
                break
        
        logger.info("IDLE loop ended")
    
    def start_monitoring(self):
        """Start the monitoring process"""
        retry_count = 0
        max_retries = self.config['monitoring']['max_retries']
        
        while self.running and retry_count < max_retries:
            try:
                # Connect to Gmail
                if not self.connect_to_gmail():
                    retry_count += 1
                    logger.warning(f"Connection failed, retry {retry_count}/{max_retries}")
                    time.sleep(10)
                    continue
                
                # Reset retry count on successful connection
                retry_count = 0
                
                # Check for existing unread emails
                self.check_for_new_emails()
                
                # Start IDLE monitoring
                self.idle_loop()
                
                # If we get here, IDLE loop ended - try to reconnect
                logger.info("IDLE loop ended, attempting to reconnect...")
                
                if self.imap:
                    try:
                        self.imap.close()
                        self.imap.logout()
                    except:
                        pass
                    self.imap = None
                
                time.sleep(5)  # Wait before reconnecting
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                retry_count += 1
                time.sleep(10)
        
        logger.info("Monitoring stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
        if self.imap:
            try:
                self.imap.send(b'DONE\r\n')  # End IDLE mode
                self.imap.close()
                self.imap.logout()
            except:
                pass
        
        sys.exit(0)
    
    def run(self):
        """Main entry point"""
        logger.info("Starting Gmail real-time monitor...")
        self.start_monitoring()

def main():
    """Main entry point"""
    monitor = GmailRealtimeMonitor()
    monitor.run()

if __name__ == "__main__":
    main()