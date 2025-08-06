#!/usr/bin/env python3
"""
Insert MCP servers configuration into Claude config files
Can be run manually after reviewing the generated config
"""

import json
import os
import sys
from pathlib import Path
import shutil
from datetime import datetime

def backup_file(filepath: Path) -> Path:
    """Create a backup of the file"""
    backup_path = filepath.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    shutil.copy2(filepath, backup_path)
    print(f"   📋 Backup created: {backup_path}")
    return backup_path

def insert_mcp_config_to_claude_json(mcp_config: dict, claude_json_path: Path) -> bool:
    """Insert MCP config into .claude.json"""
    try:
        # Read existing config
        with open(claude_json_path, 'r') as f:
            claude_config = json.load(f)
        
        # Find project path
        if 'projects' not in claude_config or not claude_config['projects']:
            print("   ❌ No projects found in .claude.json")
            return False
        
        # Get the first (usually only) project
        project_path = list(claude_config['projects'].keys())[0]
        
        # Create backup
        backup_file(claude_json_path)
        
        # Insert MCP servers (replaces any existing to fix outdated paths - POSS-177)
        claude_config['projects'][project_path]['mcpServers'] = mcp_config
        
        # Write back
        with open(claude_json_path, 'w') as f:
            json.dump(claude_config, f, indent=2)
        
        print(f"   ✅ Updated .claude.json with MCP servers")
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating .claude.json: {e}")
        return False

def insert_mcp_config_to_desktop(mcp_config: dict, desktop_config_path: Path) -> bool:
    """Insert MCP config into Claude Desktop config"""
    try:
        # Read existing config
        if desktop_config_path.exists():
            with open(desktop_config_path, 'r') as f:
                desktop_config = json.load(f)
            backup_file(desktop_config_path)
        else:
            desktop_config = {}
        
        # Insert MCP servers (replaces any existing to fix outdated paths - POSS-177)
        desktop_config['mcpServers'] = mcp_config
        
        # Write
        with open(desktop_config_path, 'w') as f:
            json.dump(desktop_config, f, indent=2)
        
        print(f"   ✅ Updated Claude Desktop config with MCP servers")
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating Desktop config: {e}")
        return False

def main():
    """Main entry point"""
    print("🔧 Inserting MCP servers configuration...")
    
    # Find MCP config
    clap_dir = os.environ.get('CLAP_DIR', Path.home() / 'claude-autonomy-platform')
    mcp_config_file = Path(clap_dir) / 'mcp-servers' / 'mcp_servers_config.json'
    
    if not mcp_config_file.exists():
        print("❌ MCP config not found. Run generate_mcp_config.py first")
        return 1
    
    # Load MCP config
    with open(mcp_config_file, 'r') as f:
        mcp_config = json.load(f)
    
    print(f"   📋 Loaded MCP config with {len(mcp_config)} servers")
    
    # Update .claude.json
    claude_json_path = Path.home() / '.claude.json'
    if claude_json_path.exists():
        print("\n📝 Updating .claude.json...")
        insert_mcp_config_to_claude_json(mcp_config, claude_json_path)
    else:
        print("\n⚠️  .claude.json not found - will update when created")
    
    # Update Claude Desktop config
    desktop_config_path = Path.home() / '.config' / 'Claude' / 'claude_desktop_config.json'
    if desktop_config_path.parent.exists():
        print("\n📝 Updating Claude Desktop config...")
        insert_mcp_config_to_desktop(mcp_config, desktop_config_path)
    
    print("\n✅ Configuration complete!")
    print("   MCP servers are now configured for both Claude Code and Claude Desktop")
    
    return 0

if __name__ == "__main__":
    # Allow running with --force to skip confirmation
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        exit(main())
    else:
        print("\n⚠️  This will modify your Claude configuration files.")
        print("   Backups will be created automatically.")
        response = input("\nProceed? (y/N): ")
        if response.lower() == 'y':
            exit(main())
        else:
            print("Cancelled.")
            exit(0)
