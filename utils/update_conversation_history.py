#!/usr/bin/env python3
"""
Update conversation history from export file
Called by session_swap.sh to update swap_CLAUDE.md
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.conversation_history_utils import parse_export_file, update_swap_claude_md

def main():
    if len(sys.argv) != 2:
        print("Usage: update_conversation_history.py <export_file>")
        sys.exit(1)
    
    export_file = Path(sys.argv[1])
    
    if not export_file.exists():
        print(f"Error: Export file not found: {export_file}")
        sys.exit(1)
    
    print(f"Parsing export file: {export_file}")
    
    # Parse the export
    turns = parse_export_file(export_file)
    
    print(f"Found {len(turns)} conversation turns")
    
    # Update swap_CLAUDE.md
    if update_swap_claude_md(turns):
        print("Successfully updated swap_CLAUDE.md")
    else:
        print("Failed to update swap_CLAUDE.md")
        sys.exit(1)

if __name__ == "__main__":
    main()