#!/usr/bin/env python3
"""
Initialize .claude.json for Claude Code
Creates a proper configuration without using the unreliable MCP add tool
"""

import json
import os
from pathlib import Path

def create_claude_json():
    """Create a fresh .claude.json with proper structure"""
    
    home = Path.home()
    claude_json_path = home / ".claude.json"
    
    # Get user info
    current_user = os.environ.get('USER', 'claude')
    
    # Determine project directory
    # First check if we're being run from ClAP
    clap_dir = os.environ.get('CLAP_DIR')
    if not clap_dir:
        # Try to find ClAP directory
        possible_dirs = [
            home / "claude-autonomy-platform",
            home / "Claude-Autonomy-Platform",
            Path.cwd()  # Current directory as fallback
        ]
        for dir_path in possible_dirs:
            if dir_path.exists() and (dir_path / "setup").exists():
                clap_dir = str(dir_path)
                break
    
    if not clap_dir:
        print("❌ Could not find ClAP directory")
        return False
    
    # Determine personal directory (project root)
    personal_repo = os.environ.get('PERSONAL_REPO', f'{current_user}-home')
    project_dir = home / personal_repo
    
    # Create the base structure
    claude_config = {
        "notificationsApiKey": "clau-vuBNf0x8xqUKkGqywdD4L15BzDNOxQZBJUJ2VYeRjwA",
        "projects": {
            str(project_dir): {
                "id": "01je8gxn47cqfjbqh1xbgshqsf",
                "name": personal_repo,
                "mcpServers": {}
            }
        }
    }
    
    # MCP server configurations will be added by setup_claude_configs.py
    # based on infrastructure config
    
    # Check if file exists and has content
    if claude_json_path.exists():
        try:
            with open(claude_json_path, 'r') as f:
                existing = json.load(f)
            
            # If it has the same project, update it
            if str(project_dir) in existing.get('projects', {}):
                print(f"✅ Found existing project config for {project_dir}")
                # Preserve the project ID
                if 'id' in existing['projects'][str(project_dir)]:
                    claude_config['projects'][str(project_dir)]['id'] = existing['projects'][str(project_dir)]['id']
        except json.JSONDecodeError:
            print("⚠️  Existing .claude.json is corrupted, creating fresh")
    
    # Write the config
    with open(claude_json_path, 'w') as f:
        json.dump(claude_config, f, indent=2)
    
    print(f"✅ Created {claude_json_path}")
    print(f"   Project: {project_dir}")
    print(f"   Ready for MCP server configuration")
    
    return True

def main():
    """Main entry point"""
    print("🔧 Initializing .claude.json...")
    
    if create_claude_json():
        print("\n✅ Success! Now run setup_claude_configs.py to add MCP servers")
    else:
        print("\n❌ Failed to create .claude.json")

if __name__ == "__main__":
    main()
