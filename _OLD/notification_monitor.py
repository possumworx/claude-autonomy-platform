#!/usr/bin/env python3

"""
Notification Monitor Service
Checks Discord (30s) and Gmail (5m) for new messages
Triggers autonomous turns when new messages arrive
"""

import asyncio
import json
import time
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import subprocess
import signal

# Add the project directory to the path for imports
project_dir = Path(__file__).parent
discord_mcp_dir = project_dir / "discord-mcp" / "src"
sys.path.insert(0, str(discord_mcp_dir))

from discord_mcp.client import create_client_state, get_channel_messages
from discord_mcp.messages import read_recent_messages

class NotificationMonitor:
    def __init__(self):
        self.state_file = project_dir / "notification_state.json"
        self.log_file = project_dir / "logs" / "notification_monitor.log"
        self.running = False
        
        # Create logs directory
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Discord configuration
        self.discord_state = None
        self.amy_user_id = "1393168234173169795"
        
        # Gmail last check timestamp
        self.last_gmail_check = 0
        
        # Discord message tracking
        self.last_discord_message_id = ""
        self.unread_message_count = 0
        self.last_checked_message_id = ""  # Last message actually checked by Claude
        
        # MCP state monitoring for reset detection (replaces log parsing)
        self.mcp_state_file = Path.home() / ".discord_mcp_state.json"
        self.last_mcp_log_check = 0
        
        # Load previous state
        self.load_state()
        
    def log(self, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def load_state(self):
        """Load previous notification state"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    state = json.load(f)
                    self.last_gmail_check = state.get("last_gmail_check", 0)
                    self.last_discord_message_id = state.get("last_discord_message_id", "")
                    self.unread_message_count = state.get("unread_message_count", 0)
                    self.last_checked_message_id = state.get("last_checked_message_id", "")
                    self.last_mcp_log_check = state.get("last_mcp_log_check", 0)
                    self.log("Loaded previous state")
            except Exception as e:
                self.log(f"Error loading state: {e}")
        else:
            self.last_discord_message_id = ""
            self.unread_message_count = 0
            self.last_checked_message_id = ""
            self.last_mcp_log_check = 0
    
    def save_state(self):
        """Save current notification state"""
        state = {
            "last_gmail_check": self.last_gmail_check,
            "last_discord_message_id": self.last_discord_message_id,
            "unread_message_count": self.unread_message_count,
            "last_checked_message_id": self.last_checked_message_id,
            "last_mcp_log_check": self.last_mcp_log_check,
            "last_updated": time.time()
        }
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.log(f"Error saving state: {e}")
    
    async def init_discord(self):
        """Initialize Discord MCP client"""
        email = os.getenv("DISCORD_EMAIL")
        password = os.getenv("DISCORD_PASSWORD") 
        
        if not email or not password:
            self.log("ERROR: DISCORD_EMAIL and DISCORD_PASSWORD must be set")
            return False
            
        self.discord_state = create_client_state(email, password, headless=True)
        self.log("Discord MCP client initialized")
        return True
    
    async def check_discord_messages(self) -> bool:
        """Check for new Discord messages. Returns True if new messages found."""
        try:
            # Check DMs with Amy
            self.discord_state, messages = await read_recent_messages(
                self.discord_state,
                server_id="@me",
                channel_id=self.amy_user_id,
                hours_back=24,  # Check longer period for unread counting
                max_messages=10
            )
            
            if messages:
                # Get the most recent message
                latest_message = messages[0]  # Messages are ordered newest first
                
                # Check if this message is newer than our last processed one
                if latest_message.id != self.last_discord_message_id:
                    self.log(f"Found new Discord message: {latest_message.id}")
                    # Update our tracking
                    self.last_discord_message_id = latest_message.id
                    
                    # Count unread messages (messages newer than last checked, excluding my own)
                    if self.last_checked_message_id:
                        # Count messages that are newer than the last one Claude actually checked
                        unread_count = 0
                        for msg in messages:
                            if msg.id == self.last_checked_message_id:
                                break
                            # Only count messages from Amy (not my own messages)
                            if msg.author_name == "Amy":
                                unread_count += 1
                        self.unread_message_count = unread_count
                    else:
                        # If Claude has never checked messages, count all recent messages from Amy
                        self.unread_message_count = len([msg for msg in messages if msg.author_name == "Amy"])
                    
                    self.log(f"Unread message count: {self.unread_message_count}")
                    return True
            
            return False
            
        except Exception as e:
            self.log(f"Error checking Discord: {e}")
            return False
    
    def check_gmail_messages(self) -> bool:
        """Check for new Gmail messages. Returns True if new messages found."""
        try:
            # Simple check using Claude Code MCP tools would go here
            # For MVP, we'll implement this after Discord is working
            current_time = time.time()
            
            # Only check Gmail every 5 minutes
            if current_time - self.last_gmail_check < 300:  # 5 minutes
                return False
                
            self.last_gmail_check = current_time
            self.log("Gmail check - implementation pending")
            return False
            
        except Exception as e:
            self.log(f"Error checking Gmail: {e}")
            return False
    
    def trigger_autonomous_turn(self, message_type: str, count: int = 1, is_reminder: bool = False):
        """Trigger an autonomous turn by sending message to tmux"""
        try:
            if is_reminder:
                if count == 1:
                    prompt = f"You have 1 unread {message_type} message"
                else:
                    prompt = f"You have {count} unread {message_type} messages"
            else:
                if count == 1:
                    prompt = f"You have a new {message_type} message"
                else:
                    prompt = f"You have {count} new {message_type} messages"
            
            # Send prompt to autonomous-claude tmux session
            subprocess.run(["tmux", "send-keys", "-t", "autonomous-claude", prompt], check=True)
            subprocess.run(["tmux", "send-keys", "-t", "autonomous-claude", "Enter"], check=True)
            
            self.log(f"Triggered autonomous turn: {prompt}")
            
        except Exception as e:
            self.log(f"Error triggering autonomous turn: {e}")
    
    def check_for_unread_reminders(self):
        """Check if we should send reminders about unread messages"""
        if self.unread_message_count > 0:
            self.trigger_autonomous_turn("Discord", self.unread_message_count, is_reminder=True)
    
    def mark_messages_as_read(self, latest_message_id: str):
        """Mark messages as read - call this when Claude checks Discord"""
        self.last_checked_message_id = latest_message_id
        self.unread_message_count = 0
        self.save_state()
        self.log(f"Marked messages as read up to: {latest_message_id}")
    
    def check_mcp_state_for_reset(self):
        """Check MCP state file for Discord read_messages calls to reset counter"""
        self.log(f"Checking MCP state for reset - unread count: {self.unread_message_count}")
        try:
            if not self.mcp_state_file.exists():
                self.log(f"MCP state file does not exist: {self.mcp_state_file}")
                return
            
            # Read the MCP state file
            with open(self.mcp_state_file, 'r') as f:
                mcp_state = json.load(f)
            
            # Get the last checked message ID from the MCP server
            last_checked_messages = mcp_state.get("last_checked_messages", {})
            amy_channel_key = f"@me-{self.amy_user_id}"
            
            mcp_last_checked = last_checked_messages.get(amy_channel_key)
            
            if mcp_last_checked and mcp_last_checked != self.last_checked_message_id:
                self.log(f"✅ MCP state shows messages were checked: {self.last_checked_message_id} -> {mcp_last_checked}")
                
                # Reset the unread count and update our baseline
                self.last_checked_message_id = mcp_last_checked
                self.unread_message_count = 0
                self.save_state()
                
                self.log("Reset unread count to 0 based on MCP state")
            else:
                self.log(f"No MCP state change detected: {mcp_last_checked}")
            
        except Exception as e:
            self.log(f"Error checking MCP state: {e}")
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        self.log("Starting notification monitoring")
        self.running = True
        
        # Initialize Discord
        if not await self.init_discord():
            return
        
        discord_check_interval = 30  # 30 seconds
        reminder_interval = 300  # 5 minutes for recurring reminders
        last_discord_check = 0
        last_reminder_check = 0
        last_mcp_check = 0  # Track MCP log checking separately
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check Discord every 30 seconds
                if current_time - last_discord_check >= discord_check_interval:
                    last_discord_check = current_time
                    
                    has_discord_messages = await self.check_discord_messages()
                    if has_discord_messages:
                        self.trigger_autonomous_turn("Discord", self.unread_message_count)
                
                # Check MCP logs for reset detection every 30 seconds
                if current_time - last_mcp_check >= discord_check_interval:
                    last_mcp_check = current_time
                    self.check_mcp_state_for_reset()
                
                # Check for recurring reminders every 5 minutes
                if current_time - last_reminder_check >= reminder_interval:
                    last_reminder_check = current_time
                    self.check_for_unread_reminders()
                
                # Check Gmail (handled internally with 5-minute timing)
                has_gmail_messages = self.check_gmail_messages()
                if has_gmail_messages:
                    self.trigger_autonomous_turn("Gmail")
                
                # Save state periodically
                self.save_state()
                
                # Sleep for 10 seconds before next iteration
                await asyncio.sleep(10)
                
            except KeyboardInterrupt:
                self.log("Received shutdown signal")
                break
            except Exception as e:
                self.log(f"Error in monitor loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error
        
        self.log("Notification monitoring stopped")
    
    def stop(self):
        """Stop the monitoring loop"""
        self.running = False

async def main():
    monitor = NotificationMonitor()
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        monitor.log(f"Received signal {signum}")
        monitor.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await monitor.monitor_loop()
    finally:
        monitor.save_state()

if __name__ == "__main__":
    asyncio.run(main())