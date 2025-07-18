#!/usr/bin/env python3
"""
Tmux-to-Claude Desktop MCP Adapter
Pure adapter layer for Claude Autonomous Platform (ClAP)

Monitors tmux session "autonomy-claude" for existing command patterns and 
adapts them to work with Claude Desktop instead of Claude Code.

Only runs when Claude Desktop is the target environment.
Preserves all existing autonomous infrastructure unchanged.
"""

import asyncio
import json
import subprocess
import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TmuxMonitor:
    """Monitor tmux session for new messages"""
    
    def __init__(self, session_name: str = "autonomy-claude"):
        self.session_name = session_name
        self.last_content = ""
        self.position_file = f"/tmp/tmux_position_{session_name}.txt"
        self.load_position()
    
    def load_position(self):
        """Load last known position from file"""
        try:
            if os.path.exists(self.position_file):
                with open(self.position_file, 'r') as f:
                    self.last_content = f.read()
            else:
                self.last_content = ""
        except Exception as e:
            logger.warning(f"Could not load position file: {e}")
            self.last_content = ""
    
    def save_position(self, content: str):
        """Save current position to file"""
        try:
            with open(self.position_file, 'w') as f:
                f.write(content)
            self.last_content = content
        except Exception as e:
            logger.warning(f"Could not save position file: {e}")
    
    def capture_tmux(self) -> Optional[str]:
        """Capture current tmux session content"""
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", self.session_name, "-p"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"tmux capture failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("tmux capture timed out")
            return None
        except Exception as e:
            logger.error(f"tmux capture error: {e}")
            return None
    
    def get_new_messages(self) -> List[str]:
        """Get new messages since last check"""
        current_content = self.capture_tmux()
        if current_content is None:
            return []
        
        # Simple diff - look for new lines
        if not self.last_content:
            # First run - don't process all history
            self.save_position(current_content)
            return []
        
        # Split into lines and find new ones
        old_lines = self.last_content.split('\n')
        new_lines = current_content.split('\n')
        
        # Find lines that are new
        new_messages = []
        if len(new_lines) > len(old_lines):
            new_messages = new_lines[len(old_lines):]
            # Filter out empty lines
            new_messages = [msg.strip() for msg in new_messages if msg.strip()]
        
        if new_messages:
            self.save_position(current_content)
            logger.info(f"Found {len(new_messages)} new messages")
        
        return new_messages

class CommandParser:
    """Parse existing autonomous infrastructure commands"""
    
    @staticmethod
    def parse_command(command: str) -> Dict[str, Any]:
        """Parse tmux command and extract relevant information"""
        command = command.strip()
        
        # Parse /exit command
        if command == "/exit":
            return {
                "type": "exit_session",
                "original": command
            }
        
        # Parse claude --dangerously-skip-permissions command
        if command.startswith("claude --dangerously-skip-permissions"):
            # Extract session context from the command
            context_match = re.search(r'--session-context\s+"([^"]*)"', command)
            model_match = re.search(r'--model\s+(\w+)', command)
            
            session_context = context_match.group(1) if context_match else ""
            model = model_match.group(1) if model_match else "sonnet"
            
            return {
                "type": "start_session",
                "session_context": session_context,
                "model": model,
                "original": command
            }
        
        # Everything else is a regular conversation turn
        return {
            "type": "conversation",
            "content": command,
            "original": command
        }

class ClaudeDesktopAdapter:
    """Adapter for Claude Desktop environment"""
    
    def __init__(self):
        logger.info("Initializing Claude Desktop adapter")
        self.current_session = None
    
    async def send_conversation_turn(self, content: str) -> bool:
        """Send regular conversation turn to Claude Desktop"""
        logger.info(f"[Claude Desktop] Sending conversation: {content[:100]}...")
        
        # TODO: Implement actual Claude Desktop API call
        # This would use Claude Desktop's API to send the message
        # For now, just log what we would send
        
        return True
    
    async def exit_session(self) -> bool:
        """Exit current Claude Desktop session"""
        logger.info("[Claude Desktop] Exiting current session")
        
        # TODO: Implement actual Claude Desktop session exit
        # This would terminate the current conversation
        
        self.current_session = None
        return True
    
    async def start_session(self, session_context: str, model: str = "sonnet") -> bool:
        """Start new Claude Desktop session with context"""
        logger.info(f"[Claude Desktop] Starting new session with model: {model}")
        logger.info(f"[Claude Desktop] Session context: {session_context[:200]}...")
        
        # TODO: Implement actual Claude Desktop session start
        # This would create a new conversation with the session context
        # as the first message
        
        self.current_session = {
            "model": model,
            "started_at": datetime.now(),
            "context": session_context
        }
        
        return True

class TmuxClaudeDesktopAdapter:
    """Main adapter for routing tmux commands to Claude Desktop"""
    
    def __init__(self):
        self.tmux_monitor = TmuxMonitor()
        self.command_parser = CommandParser()
        self.claude_desktop = ClaudeDesktopAdapter()
        self.running = False
    
    async def process_command(self, command: str):
        """Process a single command from tmux"""
        parsed = self.command_parser.parse_command(command)
        cmd_type = parsed["type"]
        
        logger.info(f"Processing command type: {cmd_type}")
        
        try:
            if cmd_type == "exit_session":
                await self.claude_desktop.exit_session()
            
            elif cmd_type == "start_session":
                await self.claude_desktop.start_session(
                    parsed["session_context"],
                    parsed["model"]
                )
            
            elif cmd_type == "conversation":
                await self.claude_desktop.send_conversation_turn(parsed["content"])
            
            else:
                logger.warning(f"Unknown command type: {cmd_type}")
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting tmux monitoring loop")
        
        while self.running:
            try:
                new_commands = self.tmux_monitor.get_new_messages()
                
                for command in new_commands:
                    await self.process_command(command)
                
                # Wait before next check
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def start(self):
        """Start the adapter"""
        logger.info("Starting Tmux-to-Claude Desktop Adapter")
        self.running = True
        
        try:
            await self.monitor_loop()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the adapter"""
        logger.info("Stopping Tmux-to-Claude Desktop Adapter")
        self.running = False

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode - just run the adapter
        async def test_run():
            adapter = TmuxClaudeDesktopAdapter()
            await adapter.start()
        
        asyncio.run(test_run())
    else:
        # TODO: Implement full MCP server protocol
        # For now, just run the adapter
        print("Tmux-to-Claude Desktop Adapter")
        print("This adapter monitors tmux session 'autonomy-claude' and routes commands to Claude Desktop")
        print("Commands recognized:")
        print("  /exit                           -> Exit current Claude Desktop session")
        print("  claude --dangerously-skip-... -> Start new Claude Desktop session")
        print("  Everything else                 -> Send as conversation turn")
        print("")
        print("Run with --test to start monitoring")

if __name__ == "__main__":
    main()