#!/usr/bin/env python3
"""
Generate MCP servers configuration JSON
Creates mcp_servers_config.json that can be inserted into .claude.json or claude_desktop_config.json
"""

import json
import os
import sys
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

def substitute_variables(value: str, config: Dict[str, Dict[str, str]], current_user: str, home: Path, clap_dir: Path) -> str:
    """Substitute variables in config values"""
    if not isinstance(value, str):
        return value
    
    # Get credentials for substitution
    credentials = config.get('CREDENTIALS', {})
    
    # Define all available substitutions
    substitutions = {
        '$LINUX_USER': current_user,
        '$HOME': str(home),
        '$HOME_DIR': str(home),
        '$CLAP_DIR': str(clap_dir),
        '$AUTONOMY_DIR': str(clap_dir),
        '$PERSONAL_REPO': credentials.get('PERSONAL_REPO', 'claude-home'),
        '$PERSONAL_DIR': str(home / credentials.get('PERSONAL_REPO', 'claude-home')),
    }
    
    # Also allow ${VAR} style
    for key, val in substitutions.items():
        value = value.replace(key, val)
        value = value.replace(f'${{{key[1:]}}}', val)  # ${VAR} style
    
    # Handle any remaining $VARIABLE from credentials
    for key, val in credentials.items():
        value = value.replace(f'${key}', val)
        value = value.replace(f'${{{key}}}', val)
    
    return value

def generate_mcp_servers_config() -> Dict[str, Any]:
    """Generate the mcpServers configuration object"""
    
    # Load infrastructure config
    config = load_infrastructure_config()
    
    # Get user and paths
    current_user = os.environ.get('USER', config.get('CREDENTIALS', {}).get('LINUX_USER', 'claude'))
    home = Path.home()
    
    # Get CLAP directory with proper substitution
    autonomy_dir_raw = config.get('PATHS', {}).get('AUTONOMY_DIR', f'{home}/claude-autonomy-platform')
    clap_dir = Path(substitute_variables(autonomy_dir_raw, config, current_user, home, home / 'claude-autonomy-platform'))
    
    # Validate CLAP directory exists
    if not clap_dir.exists():
        print(f"⚠️  Warning: CLAP directory not found at {clap_dir}")
        print(f"   Raw config value: {autonomy_dir_raw}")
    
    mcp_servers = {}
    
    # Core MCP servers
    core_servers = config.get('CORE_MCP_SERVERS', {})
    
    # RAG Memory MCP
    if 'rag-memory' in core_servers:
        rag_path = substitute_variables(core_servers['rag-memory'], config, current_user, home, clap_dir)
        personal_repo = config.get('CREDENTIALS', {}).get('PERSONAL_REPO', 'claude-home')
        rag_index = Path(rag_path) / "dist" / "index.js"
        
        if not rag_index.exists():
            print(f"⚠️  Warning: RAG Memory MCP not found at {rag_index}")
            print(f"   You may need to build it first")
        
        mcp_servers['rag-memory'] = {
            "type": "stdio",
            "command": "node",
            "args": [str(rag_index)],
            "env": {
                "DB_FILE_PATH": f"{home}/{personal_repo}/rag-memory.db"
            }
        }
    
    # Discord MCP (Java)
    if 'discord-mcp' in core_servers:
        discord_path = substitute_variables(core_servers['discord-mcp'], config, current_user, home, clap_dir)
        discord_jar = Path(discord_path) / "target" / "discord-mcp-0.0.1-SNAPSHOT.jar"
        
        if not discord_jar.exists():
            print(f"⚠️  Warning: Discord MCP JAR not found at {discord_jar}")
            print(f"   You may need to build it first")
        
        mcp_servers['discord'] = {
            "type": "stdio",
            "command": "java",
            "args": [
                "-jar",
                str(discord_jar)
            ],
            "env": {
                "DISCORD_TOKEN": config.get('CREDENTIALS', {}).get('DISCORD_BOT_TOKEN', ''),
                "DISCORD_GUILD_ID": "1383848194881884262"
            }
        }
    
    # Linear MCP
    if 'linear-mcp' in core_servers:
        linear_path = substitute_variables(core_servers['linear-mcp'], config, current_user, home, clap_dir)
        # Check if build or dist directory exists
        linear_base = Path(linear_path)
        if (linear_base / "build" / "index.js").exists():
            linear_index = f"{linear_path}/build/index.js"
        else:
            linear_index = f"{linear_path}/dist/index.js"
        
        mcp_servers['linear'] = {
            "type": "stdio",
            "command": "node",
            "args": [linear_index],
            "env": {
                "LINEAR_API_KEY": config.get('CREDENTIALS', {}).get('LINEAR_API_KEY', '')
            }
        }
    
    # Gmail MCP
    if 'gmail' in core_servers:
        gmail_path = substitute_variables(core_servers['gmail'], config, current_user, home, clap_dir)
        mcp_servers['gmail'] = {
            "type": "stdio",
            "command": "node",
            "args": [f"{gmail_path}/dist/index.js"],
            "env": {}
        }
    
    # Note: Removed filesystem and super-shell MCP servers (POSS-177)
    # Claude Code has built-in file and command tools that make these redundant
    
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
        
        # Debug: Show some example paths to verify substitution
        if '--debug' in sys.argv:
            print("\n🔍 Debug - Variable substitution check:")
            test_config = config.get('CREDENTIALS', {})
            if 'LINUX_USER' in test_config:
                print(f"   LINUX_USER in config: {test_config['LINUX_USER']}")
                print(f"   Actual current user: {current_user}")
            if 'rag-memory' in mcp_config:
                print(f"   RAG Memory path: {mcp_config['rag-memory']['args'][0]}")
                print(f"   RAG Memory DB: {mcp_config['rag-memory']['env']['DB_FILE_PATH']}")
        
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
