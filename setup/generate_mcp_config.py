#!/usr/bin/env python3
"""
Generate MCP servers configuration JSON
Creates mcp_servers_config.json that can be inserted into .claude.json or claude_desktop_config.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

def load_infrastructure_config() -> Dict[str, Dict[str, str]]:
    """Load the infrastructure config file"""
    # Find the config file
    clap_dir = os.environ.get('CLAP_DIR')
    if not clap_dir:
        # Try to find ClAP directory
        home = Path.home()
        possible_dirs = [
            home / "claude-autonomy-platform",
            home / "Claude-Autonomy-Platform"
        ]
        for dir_path in possible_dirs:
            if dir_path.exists() and (dir_path / "config").exists():
                clap_dir = str(dir_path)
                break
    
    if not clap_dir:
        raise FileNotFoundError("Could not find ClAP directory")
    
    config_file = Path(clap_dir) / "config" / "claude_infrastructure_config.txt"
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    # Parse the config
    config = {}
    current_section = None
    
    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                config[current_section] = {}
                continue
            
            if '=' in line and current_section:
                key, value = line.split('=', 1)
                config[current_section][key.strip()] = value.strip()
    
    return config

def generate_mcp_servers_config() -> Dict[str, Any]:
    """Generate the mcpServers configuration object"""
    
    # Load infrastructure config
    config = load_infrastructure_config()
    
    # Get user and paths
    current_user = os.environ.get('USER', config.get('CREDENTIALS', {}).get('LINUX_USER', 'claude'))
    home = Path.home()
    clap_dir = Path(config.get('PATHS', {}).get('AUTONOMY_DIR', home / 'claude-autonomy-platform'))
    
    mcp_servers = {}
    
    # Core MCP servers
    core_servers = config.get('CORE_MCP_SERVERS', {})
    
    # RAG Memory MCP
    if 'rag-memory' in core_servers:
        rag_path = core_servers['rag-memory'].replace('$AUTONOMY_DIR', str(clap_dir))
        mcp_servers['rag-memory'] = {
            "type": "stdio",
            "command": "node",
            "args": [f"{rag_path}/dist/index.js"],
            "env": {
                "DB_FILE_PATH": f"{home}/{config.get('CREDENTIALS', {}).get('PERSONAL_REPO', 'claude-home')}/rag-memory.db"
            }
        }
    
    # Discord MCP (Java)
    if 'discord-mcp' in core_servers:
        discord_path = core_servers['discord-mcp'].replace('$AUTONOMY_DIR', str(clap_dir))
        mcp_servers['discord'] = {
            "type": "stdio",
            "command": "java",
            "args": [
                "-jar",
                f"{discord_path}/target/discord-mcp-0.0.1-SNAPSHOT.jar"
            ],
            "env": {
                "DISCORD_TOKEN": config.get('CREDENTIALS', {}).get('DISCORD_BOT_TOKEN', ''),
                "DISCORD_GUILD_ID": "1383848194881884262"
            }
        }
    
    # Linear MCP
    if 'linear-mcp' in core_servers:
        linear_path = core_servers['linear-mcp'].replace('$AUTONOMY_DIR', str(clap_dir))
        mcp_servers['linear'] = {
            "type": "stdio",
            "command": "node",
            "args": [f"{linear_path}/dist/index.js"],
            "env": {
                "LINEAR_API_KEY": config.get('CREDENTIALS', {}).get('LINEAR_API_KEY', '')
            }
        }
    
    # Gmail MCP
    if 'gmail' in core_servers:
        gmail_path = core_servers['gmail'].replace('$AUTONOMY_DIR', str(clap_dir))
        mcp_servers['gmail'] = {
            "type": "stdio",
            "command": "node",
            "args": [f"{gmail_path}/dist/index.js"],
            "env": {}
        }
    
    # Filesystem MCP (built-in)
    mcp_servers['filesystem'] = {
        "type": "stdio",
        "command": "npx",
        "args": ["@modelcontextprotocol/server-filesystem", str(home)]
    }
    
    # Super Shell MCP (for system commands)
    mcp_servers['super-shell'] = {
        "type": "stdio",
        "command": "npx",
        "args": ["@mattpearce/mcp-server-super-shell"]
    }
    
    return mcp_servers

def main():
    """Generate and save the MCP servers configuration"""
    try:
        # Generate the config
        mcp_config = generate_mcp_servers_config()
        
        # Find output directory
        clap_dir = os.environ.get('CLAP_DIR', Path.home() / 'claude-autonomy-platform')
        output_dir = Path(clap_dir) / 'mcp-servers'
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / 'mcp_servers_config.json'
        
        # Write the config
        with open(output_file, 'w') as f:
            json.dump(mcp_config, f, indent=2)
        
        print(f"✅ Generated MCP servers configuration: {output_file}")
        print("\n📋 Configuration includes:")
        for server in mcp_config:
            print(f"   - {server}")
        
        print("\n💡 To use this configuration:")
        print("   1. Insert into .claude.json under projects.[project_path].mcpServers")
        print("   2. OR insert into claude_desktop_config.json under mcpServers")
        print("\n   The setup scripts will handle this automatically.")
        
    except Exception as e:
        print(f"❌ Error generating config: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
