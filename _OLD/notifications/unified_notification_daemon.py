#!/usr/bin/env python3
"""
Unified Notification Daemon
Combines Gmail real-time monitoring with Discord smart polling
"""

import threading
import logging
import signal
import sys
import os
import time
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/sonnet-4/claude-autonomy-platform/unified_notifications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('unified_notifications')

class UnifiedNotificationDaemon:
    """Unified daemon for all communication monitoring"""
    
    def __init__(self):
        self.running = True
        self.gmail_monitor = None
        self.discord_monitor = None
        self.threads = []
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Unified notification daemon initialized")
    
    def start_gmail_monitor(self):
        """Start Gmail real-time monitoring in a separate thread"""
        try:
            from gmail_realtime_monitor import GmailRealtimeMonitor
            
            def run_gmail():
                self.gmail_monitor = GmailRealtimeMonitor()
                self.gmail_monitor.run()
            
            gmail_thread = threading.Thread(target=run_gmail, daemon=True)
            gmail_thread.start()
            self.threads.append(gmail_thread)
            logger.info("Gmail real-time monitor started")
            
        except Exception as e:
            logger.error(f"Error starting Gmail monitor: {e}")
    
    def start_discord_monitor(self):
        """Start Discord smart polling in a separate thread"""
        try:
            from discord_smart_monitor import DiscordSmartMonitor
            
            def run_discord():
                self.discord_monitor = DiscordSmartMonitor()
                self.discord_monitor.run()
            
            discord_thread = threading.Thread(target=run_discord, daemon=True)
            discord_thread.start()
            self.threads.append(discord_thread)
            logger.info("Discord smart monitor started")
            
        except Exception as e:
            logger.error(f"Error starting Discord monitor: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
        # Stop monitors
        if self.gmail_monitor:
            self.gmail_monitor.running = False
        if self.discord_monitor:
            self.discord_monitor.running = False
        
        sys.exit(0)
    
    def run(self):
        """Main daemon loop"""
        logger.info("Starting unified notification daemon...")
        
        # Start both monitors
        self.start_gmail_monitor()
        self.start_discord_monitor()
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        logger.info("Unified notification daemon stopped")

def main():
    """Main entry point"""
    daemon = UnifiedNotificationDaemon()
    daemon.run()

if __name__ == "__main__":
    main()