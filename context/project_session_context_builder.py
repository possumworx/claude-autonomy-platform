#!/usr/bin/env python3
"""
Project Session Context Builder
Combines my_architecture.md with swap_CLAUDE.md to create updated CLAUDE.md
This ensures each new session starts with both architecture understanding and recent context
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

def update_clap_architecture_tree(autonomy_dir):
    """Update clap_architecture.md with current directory tree"""
    try:
        clap_arch_file = autonomy_dir / "clap_architecture.md"
        
        # Generate tree output
        tree_cmd = ["tree", str(autonomy_dir.parent), "-I", "__pycache__|*.pyc|.git|logs", "--dirsfirst", "-L", "3"]
        result = subprocess.run(tree_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Warning: tree command failed - {result.stderr}")
            return
        
        tree_output = result.stdout
        
        # Read current clap_architecture.md
        with open(clap_arch_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Define the tree section with markers
        tree_section = f"""<!-- TREE_START -->
```
{tree_output}```
<!-- TREE_END -->

"""
        
        # Check if tree section exists and update it
        if "<!-- TREE_START -->" in content and "<!-- TREE_END -->" in content:
            # Replace existing tree section
            import re
            pattern = r'<!-- TREE_START -->.*?<!-- TREE_END -->\n\n'
            content = re.sub(pattern, tree_section, content, flags=re.DOTALL)
        else:
            # Insert tree section after "## Component Deep Dives" or at a suitable location
            if "## Component Deep Dives" in content:
                content = content.replace("## Component Deep Dives", 
                                        tree_section + "## Component Deep Dives")
            else:
                # Insert after overview section if Component Deep Dives doesn't exist
                lines = content.split('\n')
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.startswith('## ') and 'Overview' in line:
                        # Find the next section after overview
                        for j in range(i+1, len(lines)):
                            if lines[j].startswith('## '):
                                insert_index = j
                                break
                        break
                
                if insert_index > 0:
                    lines.insert(insert_index, tree_section)
                    content = '\n'.join(lines)
        
        # Write updated content back
        with open(clap_arch_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated directory tree in {clap_arch_file}")
        
    except Exception as e:
        print(f"Warning: Could not update directory tree - {e}")

def build_claude_md():
    """Build CLAUDE.md from architecture and conversation history"""
    
    # Define paths
    autonomy_dir = Path(__file__).parent
    home_dir = autonomy_dir.parent
    
    architecture_file = autonomy_dir / "my_architecture.md"
    swap_file = autonomy_dir / "swap_CLAUDE.md"
    claude_md_file = home_dir / "CLAUDE.md"
    new_session_file = autonomy_dir.parent / "new_session.txt"
    
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
        
        # Parse natural commands content (if exists)
        natural_commands_content = ""
        natural_commands_file = autonomy_dir.parent / "config" / "natural_commands.sh"
        if natural_commands_file.exists():
            import subprocess
            try:
                # Run the parser script to get formatted commands
                parser_script = autonomy_dir.parent / "utils" / "parse_natural_commands.sh"
                if parser_script.exists():
                    result = subprocess.run([str(parser_script)], capture_output=True, text=True)
                    if result.returncode == 0:
                        natural_commands_content = f"\n\n{result.stdout}\n"
            except Exception as e:
                print(f"Warning: Could not parse natural commands - {e}")
        
        # Parse personal commands content (if exists)
        personal_commands_content = ""
        personal_commands_file = autonomy_dir.parent / "config" / "personal_commands.sh"
        if personal_commands_file.exists():
            try:
                with open(personal_commands_file, 'r', encoding='utf-8') as f:
                    personal_commands_content = f"\n\n## Personal Natural Commands\n\n{f.read()}\n"
            except Exception as e:
                print(f"Warning: Could not read personal commands - {e}")
        
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
                
        
        # Always update directory tree in clap_architecture.md for fresh reference
        update_clap_architecture_tree(autonomy_dir)
        
        # Handoff notifications removed - only one type of swap now
        
        # Combine content with clear separation
        combined_content = f"""# Current Session Context
*Updated: {Path(swap_file).stat().st_mtime}*

{architecture_content}{personal_interests_content}{natural_commands_content}{personal_commands_content}{context_hat_content}
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
        else:
            print(f"- No context hat content added (keyword was: {keyword if new_session_file.exists() else 'No keyword file'})")
        
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
