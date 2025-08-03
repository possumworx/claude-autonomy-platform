#!/usr/bin/env python3
"""
Infrastructure Configuration Reader
Reads values from claude_infrastructure_config.txt
"""

import os
import re
import sys

# Add the utils directory to Python path so we can import claude_paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claude_paths import get_clap_dir

def read_infrastructure_config():
    """Read configuration from claude_infrastructure_config.txt"""
    config_path = os.path.join(get_clap_dir(), "config", "claude_infrastructure_config.txt")
    config = {}
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            
        # Find all KEY=VALUE pairs
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
                
        return config
    except Exception as e:
        print(f"Error reading infrastructure config: {e}")
        return {}

def get_config_value(key, default=None):
    """Get a specific config value"""
    config = read_infrastructure_config()
    return config.get(key, default)

if __name__ == "__main__":
    config = read_infrastructure_config()
    print(f"CONTINUITY_BRIDGE_PING: {config.get('CONTINUITY_BRIDGE_PING')}")
    print(f"HISTORY_TURNS: {config.get('HISTORY_TURNS')}")