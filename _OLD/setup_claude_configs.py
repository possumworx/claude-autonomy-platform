#!/usr/bin/env python3
"""
Claude Infrastructure Configuration Setup Script

Reads claude_infrastructure_config.txt and populates both:
- ~/.claude.json (Claude Code config)
- ~/.config/Claude/claude_desktop_config.json (Claude Desktop config)

This ensures consistent paths and credentials across configurations.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any

class ClaudeConfigSetup:
    def __init__(self, config_file: str = None):
        # Get actual user and paths from environment or system FIRST
        self.actual_user = os.environ.get('CLAUDE_USER', os.environ.get('USER', 'claude'))
        self.actual_home = os.environ.get('CLAUDE_HOME', os.path.expanduser('~'))
        self.actual_clap_dir = os.environ.get('CLAP_DIR', str(Path(__file__).parent.parent))
        
        if config_file is None:
            script_dir = Path(__file__).parent
            # Config is now in config/ directory
            config_file = script_dir.parent / "config" / "claude_infrastructure_config.txt"
        
        self.config_file = Path(config_file)
        self.config = self.parse_config()
        
    def parse_config(self) -> Dict[str, Dict[str, str]]:
        """Parse the infrastructure config file into sections."""
        config = {}
        current_section = None
        
        with open(self.config_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                    
                # Section headers
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    config[current_section] = {}
                    continue
                
                # Key-value pairs
                if '=' in line and current_section:
                    key, value = line.split('=', 1)
                    # Substitute variables
                    value = value.strip()
                    value = value.replace('$LINUX_USER', self.actual_user)
                    value = value.replace('$HOME', self.actual_home)
                    value = value.replace('$AUTONOMY_DIR', self.actual_clap_dir)
                    value = value.replace('$(whoami)', self.actual_user)
                    value = value.replace('$(id -u)', str(os.getuid()))
                    
                    config[current_section][key.strip()] = value
                    
        return config
    
    def get_dynamic_xauth(self) -> str:
        """Get the current X11 authority file path."""
        pattern = self.config['X11_CONFIG']['XAUTH_PATTERN']
        auth_dir = Path(f'/run/user/{os.getuid()}')
        
        if auth_dir.exists():
            for auth_file in auth_dir.glob('.mutter-Xwaylandauth.*'):
                return str(auth_file)
        
        # Fallback to pattern
        return pattern
    
    def create_claude_code_mcp_config(self) -> Dict[str, Any]:
        """Create MCP server configuration for Claude Code (.claude.json)."""
        mcp_config = {}
        
        # Core MCP servers (essential infrastructure)
        core_servers = self.config.get('CORE_MCP_SERVERS', {})
        
        # RAG Memory
        if 'rag-memory' in core_servers:
            mcp_config['rag-memory'] = {
                "type": "stdio",
                "command": "node",
                "args": [f"{core_servers['rag-memory']}/dist/index.js"],
                "env": {
                    "DB_FILE_PATH": f"{self.config['PATHS']['PERSONAL_DIR']}/rag-memory.db"
                }
            }
        
        # Discord MCP - Java version
        if 'discord-mcp' in core_servers:
            mcp_config['discord'] = {
                "type": "stdio", 
                "command": "java",
                "args": [
                    "-jar",
                    f"{core_servers['discord-mcp']}/target/discord-mcp-0.0.1-SNAPSHOT.jar"
                ],
                "env": {
                    "DISCORD_TOKEN": self.config['CREDENTIALS']['DISCORD_TOKEN'],
                    "DISCORD_GUILD_ID": "1383848194881884262"
                }
            }
        
        # Computer Use - removed, use direct bash tools instead
        # Desktop automation now handled by direct shell scripts
        
        # External servers (if configured)
        external_servers = self.config.get('EXTERNAL_MCP_SERVERS', {})
        
        # Gmail (using npm package)
        if 'gmail' in external_servers:
            mcp_config['gmail'] = {
                "type": "stdio",
                "command": "node",
                "args": [f"{external_servers['gmail']}/dist/index.js"],
                "env": {}
            }
        
        # Personal servers would go here but are handled separately
        # Each Claude instance can add their own personal MCP servers
        # by manually editing their .claude.json after setup
        
        return mcp_config
    
    def create_claude_desktop_mcp_config(self) -> Dict[str, Any]:
        """Create MCP server configuration for Claude Desktop."""
        mcp_config = {}
        
        # Core servers
        core_servers = self.config.get('CORE_MCP_SERVERS', {})
        
        # RAG Memory
        if 'rag-memory' in core_servers:
            mcp_config['rag-memory'] = {
                "command": "node",
                "args": [f"{core_servers['rag-memory']}/dist/index.js"],
                "env": {
                    "DB_FILE_PATH": f"{self.config['PATHS']['PERSONAL_DIR']}/rag-memory.db"
                }
            }
        
        # Discord MCP - Java version
        if 'discord-mcp' in core_servers:
            mcp_config['discord-mcp'] = {
                "command": "java",
                "args": [
                    "-jar",
                    f"{core_servers['discord-mcp']}/target/discord-mcp-0.0.1-SNAPSHOT.jar"
                ],
                "env": {
                    "DISCORD_TOKEN": self.config['CREDENTIALS']['DISCORD_TOKEN'],
                    "DISCORD_GUILD_ID": "1383848194881884262"
                }
            }
        
        # Computer Use - removed, use direct bash tools instead
        # Desktop automation now handled by direct shell scripts
        
        # External servers
        external_servers = self.config.get('EXTERNAL_MCP_SERVERS', {})
        
        # Gmail (using npm package)
        if 'gmail' in external_servers:
            mcp_config['gmail'] = {
                "command": "node",
                "args": [f"{external_servers['gmail']}/dist/index.js"]
            }
        
        return {"mcpServers": mcp_config}
    
    def update_claude_code_config(self) -> bool:
        """Update the Claude Code configuration file with robust handling (POSS-81)."""
        try:
            claude_json_path = Path(self.config['PATHS']['CLAUDE_JSON_PATH'])
            
            # Ensure parent directory exists
            claude_json_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing config or create minimal structure
            if claude_json_path.exists():
                with open(claude_json_path, 'r') as f:
                    existing_config = json.load(f)
            else:
                print(f"   Creating new .claude.json file...")
                existing_config = {
                    "projects": {},
                    "mcpServers": {}
                }
            
            # Ensure projects section exists
            if 'projects' not in existing_config:
                existing_config['projects'] = {}
            
            # Get current working directory as project path
            current_project_path = self.actual_clap_dir
            
            # Ensure current project exists in config
            if current_project_path not in existing_config['projects']:
                print(f"   Adding project: {current_project_path}")
                existing_config['projects'][current_project_path] = {
                    "allowedTools": [],
                    "history": [],
                    "mcpContextUris": [],
                    "mcpServers": {},
                    "enabledMcpjsonServers": [],
                    "disabledMcpjsonServers": [],
                    "hasTrustDialogAccepted": True
                }
            
            # Update MCP servers for current project
            mcp_config = self.create_claude_code_mcp_config()
            existing_config['projects'][current_project_path]['mcpServers'] = mcp_config
            
            # Also update global mcpServers (used by some versions)
            existing_config['mcpServers'] = mcp_config
            
            print(f"   Updated MCP servers: {', '.join(mcp_config.keys())}")
            
            # Write back with proper formatting
            with open(claude_json_path, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
            print(f"✅ Updated Claude Code config: {claude_json_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update Claude Code config: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_claude_desktop_config(self) -> bool:
        """Update the Claude Desktop configuration file."""
        try:
            desktop_config_path = Path(self.config['PATHS']['CLAUDE_CONFIG_DIR']) / "claude_desktop_config.json"
            
            # Ensure directory exists
            desktop_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create new config
            new_config = self.create_claude_desktop_mcp_config()
            
            # Write config
            with open(desktop_config_path, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            print(f"✅ Updated Claude Desktop config: {desktop_config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update Claude Desktop config: {e}")
            return False
    
    def setup_all(self) -> bool:
        """Setup both configurations."""
        print("🔧 Setting up Claude configurations from infrastructure config...")
        print(f"📁 Config file: {self.config_file}")
        
        success = True
        success &= self.update_claude_code_config()
        success &= self.update_claude_desktop_config()
        
        if success:
            print("✅ All configurations updated successfully!")
        else:
            print("❌ Some configurations failed to update.")
        
        return success

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Claude configurations from infrastructure config")
    parser.add_argument("--config", help="Path to infrastructure config file")
    parser.add_argument("--claude-code-only", action="store_true", help="Update only Claude Code config")
    parser.add_argument("--claude-desktop-only", action="store_true", help="Update only Claude Desktop config")
    
    args = parser.parse_args()
    
    setup = ClaudeConfigSetup(args.config)
    
    if args.claude_code_only:
        setup.update_claude_code_config()
    elif args.claude_desktop_only:
        setup.update_claude_desktop_config()
    else:
        setup.setup_all()

if __name__ == "__main__":
    main()