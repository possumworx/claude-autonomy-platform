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
        if config_file is None:
            script_dir = Path(__file__).parent
            config_file = script_dir / "claude_infrastructure_config.txt"
        
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
                    config[current_section][key.strip()] = value.strip()
                    
        return config
    
    def get_dynamic_xauth(self) -> str:
        """Get the current X11 authority file path."""
        pattern = self.config['X11_CONFIG']['XAUTH_PATTERN']
        auth_dir = Path('/run/user/1000')
        
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
        
        # Discord MCP
        if 'discord-mcp' in core_servers:
            mcp_config['discord'] = {
                "type": "stdio", 
                "command": "xvfb-run",
                "args": [
                    "-a",
                    "/home/sonnet-4/.local/bin/uv",
                    "run",
                    f"--directory={core_servers['discord-mcp']}",
                    "python",
                    "main.py"
                ],
                "cwd": core_servers['discord-mcp'],
                "env": {
                    "DISCORD_EMAIL": self.config['CREDENTIALS']['DISCORD_EMAIL'],
                    "DISCORD_PASSWORD": self.config['CREDENTIALS']['DISCORD_PASSWORD'],
                    "DISCORD_HEADLESS": "false",
                    "PATH": "/home/sonnet-4/.local/bin:/usr/local/bin:/usr/bin:/bin"
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
        
        # Discord MCP
        if 'discord-mcp' in core_servers:
            mcp_config['discord-mcp'] = {
                "command": "xvfb-run",
                "args": [
                    "-a",
                    "/home/sonnet-4/.local/bin/uv", 
                    "run",
                    f"--directory={core_servers['discord-mcp']}",
                    "python",
                    "main.py"
                ],
                "cwd": core_servers['discord-mcp'],
                "env": {
                    "DISCORD_EMAIL": self.config['CREDENTIALS']['DISCORD_EMAIL'],
                    "DISCORD_PASSWORD": self.config['CREDENTIALS']['DISCORD_PASSWORD'],
                    "DISCORD_HEADLESS": "true",
                    "PATH": "/home/sonnet-4/.local/bin:/usr/local/bin:/usr/bin:/bin"
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
        """Update the Claude Code configuration file."""
        try:
            claude_json_path = Path(self.config['PATHS']['CLAUDE_JSON_PATH'])
            
            # Read existing config
            if claude_json_path.exists():
                with open(claude_json_path, 'r') as f:
                    existing_config = json.load(f)
            else:
                existing_config = {}
            
            # Update MCP servers section
            if 'projects' in existing_config:
                sonnet_home = self.config['PATHS']['SONNET_HOME']
                if sonnet_home in existing_config['projects']:
                    existing_config['projects'][sonnet_home]['mcpServers'] = self.create_claude_code_mcp_config()
            
            # Write back
            with open(claude_json_path, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
            print(f"✅ Updated Claude Code config: {claude_json_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update Claude Code config: {e}")
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