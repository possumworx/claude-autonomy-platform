#!/usr/bin/env python3
"""
Conversation History Utilities
Functions for parsing conversation exports and updating swap_CLAUDE.md
Used by session_swap.sh during session transitions.
"""

import os
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
SWAP_CLAUDE_MD_PATH = clap_dir / "context/swap_CLAUDE.md"

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
        
        print(f"Updated swap_CLAUDE.md with {len(turns)} turns")
        return True
        
    except Exception as e:
        print(f"Error updating swap_CLAUDE.md: {e}")
        return False