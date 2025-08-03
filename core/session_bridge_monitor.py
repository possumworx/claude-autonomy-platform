#!/usr/bin/env python3
"""
Session Bridge Monitor
Automatically maintains CLAUDE.md bridge from current session
"""

import json
import time
import glob
import os
import shutil
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

# Convert personal directory path to Claude Code's project directory format
# Claude Code converts /home/user/project to -home-user-project
def path_to_claude_project_dir(path):
    """Convert a filesystem path to Claude Code's project directory format"""
    return str(path).replace('/', '-')

# Paths - watching the personal directory for session files
claude_project_dir = path_to_claude_project_dir(personal_dir)
SESSION_DIR = claude_home / ".claude" / "projects" / claude_project_dir
ARCHIVE_DIR = SESSION_DIR / "archive"
SWAP_CLAUDE_MD_PATH = clap_dir / "swap_CLAUDE.md"
LOG_PATH = clap_dir / "data" / "session_bridge_monitor.log"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    with open(LOG_PATH, "a") as f:
        f.write(log_entry + "\n")

def ping_healthcheck():
    """Ping healthchecks.io to signal service is alive"""
    import subprocess
    try:
        ping_url = get_config_value('CONTINUITY_BRIDGE_PING', 'https://hc-ping.com/fbadae5b-8303-4ba7-a478-a162ed6e6aa1')
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

def get_session_files():
    """Get all .jsonl files in session directory"""
    return glob.glob(f"{SESSION_DIR}/*.jsonl")

def get_new_turns_from_session(session_file, last_processed_line=0):
    """Get all new conversation turns from a session file since last_processed_line"""
    try:
        with open(session_file, 'r') as f:
            lines = f.readlines()
            
        new_turns = []
        
        # Process lines starting from last_processed_line
        for line_num, line in enumerate(lines[last_processed_line:], start=last_processed_line):
            try:
                data = json.loads(line.strip())
                if data.get('type') == 'user':
                    content = data['message']['content']
                    # Only get string content (real messages), skip array content (tool results)
                    if isinstance(content, str):
                        new_turns.append(f"**Amy**: {content}")
                elif data.get('type') == 'assistant' and 'message' in data:
                    # Extract text content from assistant message
                    message = data['message']
                    if 'content' in message:
                        if isinstance(message['content'], list):
                            # Handle structured content - only get text parts
                            text_parts = []
                            for part in message['content']:
                                if part.get('type') == 'text':
                                    text_parts.append(part['text'])
                            if text_parts:
                                full_text = ' '.join(text_parts)
                                # Only add if it's actual conversation, not tool noise
                                if len(full_text) > 50:  # Filter out very short responses
                                    new_turns.append(f"**Claude**: {full_text}")
                        elif isinstance(message['content'], str):
                            # Only add substantial responses
                            if len(message['content']) > 50:
                                new_turns.append(f"**Claude**: {message['content']}")
            except (json.JSONDecodeError, KeyError):
                continue
                
        return new_turns, len(lines)  # Return turns and total line count
        
    except Exception as e:
        log(f"Error extracting new turns: {e}")
        return [], 0

def parse_existing_conversation(swap_file_path):
    """Parse existing conversation turns from swap_CLAUDE.md"""
    try:
        if not os.path.exists(swap_file_path):
            return []
            
        with open(swap_file_path, 'r') as f:
            content = f.read()
            
        # Find the conversation section
        if "**Recent conversation flow**:" in content:
            conversation_section = content.split("**Recent conversation flow**:")[1]
            conversation_section = conversation_section.split("---")[0].strip()
            
            if conversation_section:
                # Split by double newlines to get individual turns
                turns = [turn.strip() for turn in conversation_section.split('\n\n') if turn.strip()]
                return turns
                
        return []
        
    except Exception as e:
        log(f"Error parsing existing conversation: {e}")
        return []

def update_swap_bridge_rolling(new_turns, session_file, max_turns=None):
    """Update swap_CLAUDE.md with rolling window of conversation turns"""
    try:
        # Get max_turns from config if not specified
        if max_turns is None:
            max_turns = int(get_config_value('HISTORY_TURNS', '20'))
            
        # Get existing conversation turns
        existing_turns = parse_existing_conversation(SWAP_CLAUDE_MD_PATH)
        
        # Add all new turns
        for new_turn in new_turns:
            if new_turn and (not existing_turns or existing_turns[-1] != new_turn):
                existing_turns.append(new_turn)
        
        # Keep only the most recent max_turns
        if len(existing_turns) > max_turns:
            existing_turns = existing_turns[-max_turns:]
        
        # Create the conversation section
        conversation_section = "\n\n".join(existing_turns) if existing_turns else "(no recent conversation)"
        
        session_info = f"""## Current Session Context
*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

**Previous session file**: {os.path.basename(session_file)}

**Recent conversation flow**:
{conversation_section}

---
"""
        
        # Write to swap file
        with open(SWAP_CLAUDE_MD_PATH, 'w') as f:
            f.write(session_info)
        
        log(f"Updated swap_CLAUDE.md rolling window from {os.path.basename(session_file)} (turns: {len(existing_turns)})")
        
    except Exception as e:
        log(f"Error updating swap_CLAUDE.md: {e}")

def archive_old_session(old_session_file):
    """Move old session to archive"""
    try:
        filename = os.path.basename(old_session_file)
        archive_path = os.path.join(ARCHIVE_DIR, filename)
        shutil.move(old_session_file, archive_path)
        log(f"Archived session: {filename}")
        return archive_path
    except Exception as e:
        log(f"Error archiving session: {e}")
        return None

def monitor_loop():
    """Main monitoring loop"""
    log("Session bridge monitor started")
    session_line_counts = {}  # Track line counts per session file
    
    while True:
        try:
            session_files = get_session_files()
            
            if len(session_files) == 0:
                log("No session files found")
                
            elif len(session_files) == 1:
                # Normal case: check for new turns in current session
                current_session = session_files[0]
                last_processed_line = session_line_counts.get(current_session, 0)
                
                new_turns, total_lines = get_new_turns_from_session(current_session, last_processed_line)
                
                # Only update if we have new turns
                if new_turns:
                    update_swap_bridge_rolling(new_turns, current_session)
                    session_line_counts[current_session] = total_lines
                    log(f"Added {len(new_turns)} new turns from {os.path.basename(current_session)}")
                
            elif len(session_files) > 1:
                # Session transition detected - just use the newest session without archiving
                session_files.sort(key=lambda x: os.path.getmtime(x))
                
                log(f"Multiple sessions detected ({len(session_files)} files), using newest without archiving")
                
                # Update swap bridge from new current session
                current_session = session_files[-1]
                last_processed_line = session_line_counts.get(current_session, 0)
                
                new_turns, total_lines = get_new_turns_from_session(current_session, last_processed_line)
                
                if new_turns:
                    update_swap_bridge_rolling(new_turns, current_session)
                    session_line_counts[current_session] = total_lines
                    
                log(f"Multiple sessions detected, now monitoring: {os.path.basename(current_session)}")
                
        except Exception as e:
            log(f"Monitor error: {e}")
        
        # Ping healthcheck to signal service is alive
        ping_healthcheck()
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    
    # Run monitoring
    monitor_loop()