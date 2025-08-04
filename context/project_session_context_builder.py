#!/usr/bin/env python3
"""
Project Session Context Builder
Combines my_architecture.md with swap_CLAUDE.md to create updated CLAUDE.md
This ensures each new session starts with both architecture understanding and recent context
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def build_claude_md():
    """Build CLAUDE.md from architecture and conversation history"""
    
    # Define paths
    autonomy_dir = Path(__file__).parent
    home_dir = autonomy_dir.parent
    
    architecture_file = autonomy_dir / "my_architecture.md"
    swap_file = autonomy_dir / "swap_CLAUDE.md"
    claude_md_file = home_dir / "CLAUDE.md"
    new_session_file = autonomy_dir / "new_session.txt"
    
    try:
        # Read architecture content
        with open(architecture_file, 'r', encoding='utf-8') as f:
            architecture_content = f.read()
        
        # Read personal interests content (if exists)
        personal_interests_content = ""
        personal_interests_file = autonomy_dir / "my_personal_interests.md"
        if personal_interests_file.exists():
            with open(personal_interests_file, 'r', encoding='utf-8') as f:
                personal_interests_content = f"\n\n{f.read()}\n"
        
        # Read swap content
        with open(swap_file, 'r', encoding='utf-8') as f:
            swap_content = f.read()
        
        # Check for context hat keyword and load appropriate context
        context_hat_content = ""
        if new_session_file.exists():
            with open(new_session_file, 'r', encoding='utf-8') as f:
                keyword = f.read().strip().upper()
            
            # Load context hats configuration
            config_file = autonomy_dir / "context_hats_config.json"
            context_docs = {}
            
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        for key, value in config.get("context_hats", {}).items():
                            if value.get("path"):
                                # Resolve path relative to autonomy_dir
                                context_docs[key] = autonomy_dir / value["path"]
                            else:
                                context_docs[key] = None
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Error loading context hats config - {e}")
                    # Fallback to default AUTONOMY context
                    context_docs = {"AUTONOMY": autonomy_dir / "autonomy-status.md"}
            else:
                # Fallback to default AUTONOMY context if no config file
                context_docs = {"AUTONOMY": autonomy_dir / "autonomy-status.md"}
            
            if keyword in context_docs and keyword != "NONE":
                context_file = context_docs[keyword]
                if context_file and context_file.exists():
                    with open(context_file, 'r', encoding='utf-8') as f:
                        context_hat_content = f"\n## Context Hat: {keyword}\n\n{f.read()}\n"
        
        # Handoff notifications removed - only one type of swap now
        
        # Combine content with clear separation
        combined_content = f"""# Current Session Context
*Updated: {Path(swap_file).stat().st_mtime}*

{architecture_content}{personal_interests_content}{context_hat_content}
## Recent Conversation Context

{swap_content}"""
        
        # Write to CLAUDE.md
        with open(claude_md_file, 'w', encoding='utf-8') as f:
            f.write(combined_content)
        
        print(f"Successfully updated {claude_md_file}")
        print(f"- Architecture from: {architecture_file}")
        print(f"- Conversation from: {swap_file}")
        if context_hat_content:
            print(f"- Context hat: {keyword}")
        
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
        return False
    except Exception as e:
        print(f"Error building CLAUDE.md: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = build_claude_md()
    exit(0 if success else 1)
