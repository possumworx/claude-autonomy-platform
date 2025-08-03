#!/usr/bin/env python3
"""
Conversation Collector
Periodically exports Claude conversations to maintain history for session transitions
"""

import os
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Import path utilities
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from claude_paths import get_claude_paths, get_clap_dir
from infrastructure_config_reader import get_config_value

# Get dynamic paths
claude_home, personal_dir, autonomy_dir = get_claude_paths()
clap_dir = get_clap_dir()

# Paths
EXPORT_DIR = Path("/tmp/claude-exports")
SWAP_CLAUDE_MD_PATH = clap_dir / "context" / "swap_CLAUDE.md"
LOG_PATH = clap_dir / "data" / "conversation_collector.log"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    with open(LOG_PATH, "a") as f:
        f.write(log_entry + "\n")

def is_claude_busy():
    """Check if Claude is currently processing (Percolating/typing)"""
    try:
        # Capture current tmux pane content
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", "autonomous-claude", "-p"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            content = result.stdout
            # Check for signs of active processing
            busy_indicators = ["Percolating", "✽", "✢", "⚡", "typing", "...]"]
            return any(indicator in content for indicator in busy_indicators)
        
        return False
    except:
        return True  # Assume busy if we can't check

def export_current_session():
    """Run claude export via tmux and return the filepath"""
    try:
        # Check if Claude is busy first
        if is_claude_busy():
            log("Claude is busy, skipping export")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"session_{timestamp}.txt"
        export_path = EXPORT_DIR / export_filename
        
        # Send /export command to the Claude session in tmux
        # First check if the session exists
        check_result = subprocess.run(
            ["tmux", "has-session", "-t", "autonomous-claude"],
            capture_output=True
        )
        
        if check_result.returncode != 0:
            log("No autonomous-claude tmux session found")
            return None
        
        # Brief pause to avoid mid-keystroke timing
        time.sleep(0.5)
        
        # Send the export command
        result = subprocess.run(
            ["tmux", "send-keys", "-t", "autonomous-claude", f"/export {export_path}", "Enter"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            log(f"Failed to send export command: {result.stderr}")
            return None
        
        # Wait for export to complete
        for i in range(10):  # Try for up to 10 seconds
            time.sleep(1)
            if export_path.exists():
                log(f"Successfully exported session to {export_path}")
                return export_path
        
        log(f"Export file not found after waiting")
        return None
            
    except Exception as e:
        log(f"Export error: {e}")
        return None

def parse_export_file(filepath, human_name=None):
    """Parse export file and return formatted conversation"""
    # Get human friend name from config if not provided
    if not human_name:
        human_name = get_config_value('HUMAN_FRIEND_NAME', 'Human')
    
    turns = []
    current_speaker = None
    current_content = []
    in_tool_output = False
    
    with open(filepath, 'r') as f:
        for line in f:
            # Skip header lines
            if line.startswith('╭─') or line.startswith('│') or line.startswith('╰─'):
                continue
                
            # New user message
            if line.startswith('>'):
                # Save previous turn if exists
                if current_speaker and current_content:
                    content = '\n'.join(current_content).strip()
                    if content:  # Only add non-empty turns
                        turns.append(f"**{current_speaker}**: {content}")
                
                current_speaker = human_name
                current_content = [line[1:].strip()]
                in_tool_output = False
                
            # New assistant message
            elif line.startswith('●'):
                # Check if this is a tool call
                remaining = line[1:].strip()
                if '(' in remaining and ')' in remaining:
                    # This is a tool call, include it but mark appropriately
                    if current_speaker == "Me" and current_content:
                        # Add to existing content
                        current_content.append(f"[{remaining}]")
                    in_tool_output = False
                else:
                    # Regular message
                    if current_speaker and current_content:
                        content = '\n'.join(current_content).strip()
                        if content:
                            turns.append(f"**{current_speaker}**: {content}")
                    
                    current_speaker = "Me"
                    current_content = [remaining]
                    in_tool_output = False
                    
            # Tool output marker
            elif line.strip().startswith('⎿'):
                in_tool_output = True
                # Add brief note about tool result if it's an error or important
                if 'Error:' in line or 'not found' in line:
                    if current_speaker == "Me":
                        current_content.append(f"  [{line.strip()[1:].strip()}]")
                        
            # Continuation of current message
            elif line.strip() and current_speaker and not in_tool_output:
                # Skip tool-related markers
                if not any(marker in line for marker in ['☐', '☒', '⎿']):
                    current_content.append(line.strip())
    
    # Don't forget the last turn
    if current_speaker and current_content:
        content = '\n'.join(current_content).strip()
        if content:
            turns.append(f"**{current_speaker}**: {content}")
    
    return turns

def update_swap_claude_md(turns, max_turns=None):
    """Update swap_CLAUDE.md with conversation history"""
    try:
        # Get max_turns from config if not specified
        if max_turns is None:
            max_turns = int(get_config_value('HISTORY_TURNS', '20'))
        
        # Keep only the most recent turns
        if len(turns) > max_turns:
            turns = turns[-max_turns:]
        
        # Format the conversation
        conversation_text = "\n\n".join(turns) if turns else "(no recent conversation)"
        
        # Create the session context
        session_info = f"""## Current Session Context
*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

**Recent conversation flow**:

{conversation_text}

---
"""
        
        # Write to swap file
        with open(SWAP_CLAUDE_MD_PATH, 'w') as f:
            f.write(session_info)
        
        log(f"Updated swap_CLAUDE.md with {len(turns)} turns")
        return True
        
    except Exception as e:
        log(f"Error updating swap_CLAUDE.md: {e}")
        return False

def cleanup_old_exports(keep_hours=24):
    """Remove export files older than keep_hours"""
    try:
        cutoff_time = time.time() - (keep_hours * 3600)
        for export_file in EXPORT_DIR.glob("session_*.txt"):
            if export_file.stat().st_mtime < cutoff_time:
                export_file.unlink()
                log(f"Cleaned up old export: {export_file.name}")
    except Exception as e:
        log(f"Cleanup error: {e}")

def monitor_loop():
    """Main monitoring loop"""
    log("Export-based session bridge monitor started")
    
    while True:
        try:
            # Export current session
            export_path = export_current_session()
            
            if export_path:
                # Parse the export
                turns = parse_export_file(export_path)
                
                # Update swap_CLAUDE.md
                update_swap_claude_md(turns)
                
                # Cleanup old exports (once per loop is fine)
                cleanup_old_exports()
            
        except Exception as e:
            log(f"Monitor error: {e}")
        
        # Wait before next export (5 minutes default)
        sleep_minutes = int(get_config_value('EXPORT_INTERVAL_MINUTES', '5'))
        time.sleep(sleep_minutes * 60)

if __name__ == "__main__":
    # Ensure directories exist
    EXPORT_DIR.mkdir(exist_ok=True)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    
    # Run monitoring
    monitor_loop()