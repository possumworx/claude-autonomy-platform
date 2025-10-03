#!/usr/bin/env python3
"""
Claude Autonomy Platform Path Utilities
Provides dynamic path detection for ClAP scripts
"""

import os
from pathlib import Path
from typing import Tuple


def read_config_value(key: str, config_file: Path) -> str:
    """Read a value from the infrastructure config file."""
    if not config_file.exists():
        return ""
    
    # Read the value, handling variable substitution
    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f"{key}="):
                value = line.split('=', 1)[1]
                
                # Handle variable substitution (e.g., $LINUX_USER)
                if '$' in value:
                    for var_line in open(config_file, 'r'):
                        var_line = var_line.strip()
                        if var_line.startswith('LINUX_USER='):
                            linux_user = var_line.split('=', 1)[1]
                            value = value.replace('$LINUX_USER', linux_user)
                        elif var_line.startswith('PERSONAL_REPO='):
                            personal_repo = var_line.split('=', 1)[1]
                            value = value.replace('$PERSONAL_REPO', personal_repo)
                
                return value
    return ""


def get_claude_paths() -> Tuple[Path, Path, Path]:
    """
    Get Claude paths with fallback detection.
    
    Returns:
        Tuple of (claude_home, personal_dir, autonomy_dir)
    """
    # Get ClAP directory and config file
    clap_dir = get_clap_dir()
    config_file = clap_dir / 'claude_infrastructure_config.txt'
    
    # Read from config file
    claude_user = read_config_value('LINUX_USER', config_file) or 'sonnet-4'
    personal_repo = read_config_value('PERSONAL_REPO', config_file) or 'personal'
    
    # Override with environment variables if set
    claude_user = os.environ.get('CLAUDE_USER', claude_user)
    claude_home = Path(os.environ.get('CLAUDE_HOME', Path.home()))
    
    # Set derived paths
    personal_dir = Path(os.environ.get('PERSONAL_DIR', claude_home / personal_repo))
    autonomy_dir = Path(os.environ.get('AUTONOMY_DIR', claude_home / 'claude-autonomy-platform'))
    
    return claude_home, personal_dir, autonomy_dir


def get_clap_dir() -> Path:
    """
    Get the ClAP (Claude Autonomy Platform) directory.

    Returns:
        Path to the ClAP directory
    """
    # Try environment variable first
    clap_dir = os.environ.get('CLAP_DIR')
    if clap_dir:
        return Path(clap_dir)

    # Fall back to parent directory of utils/ where this script is located
    # (this script is in utils/, ClAP root is one level up)
    return Path(__file__).parent.parent.resolve()


def get_claude_config_dir() -> Path:
    """
    Get the Claude configuration directory.
    
    Returns:
        Path to Claude config directory
    """
    claude_home, _, _ = get_claude_paths()
    return Path(os.environ.get('CLAUDE_CONFIG_DIR', claude_home / '.config' / 'Claude'))


def source_claude_env() -> None:
    """
    Source the claude_env.sh script to set environment variables.
    This is useful when the script is called directly.
    """
    clap_dir = get_clap_dir()
    env_script = clap_dir / 'claude_env.sh'
    
    if env_script.exists():
        # Read and execute the environment script
        import subprocess
        result = subprocess.run(['bash', '-c', f'source {env_script} && env'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if '=' in line and not line.startswith('_'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value


if __name__ == '__main__':
    # Debug output when run directly
    print("Claude Autonomy Platform Path Detection")
    print("=" * 50)
    
    # Source environment if available
    source_claude_env()
    
    # Get paths
    claude_home, personal_dir, autonomy_dir = get_claude_paths()
    clap_dir = get_clap_dir()
    config_dir = get_claude_config_dir()
    
    print(f"CLAUDE_HOME: {claude_home}")
    print(f"PERSONAL_DIR: {personal_dir}")
    print(f"AUTONOMY_DIR: {autonomy_dir}")
    print(f"CLAP_DIR: {clap_dir}")
    print(f"CLAUDE_CONFIG_DIR: {config_dir}")
    
    # Check if paths exist
    print("\nPath Status:")
    print(f"  CLAUDE_HOME exists: {claude_home.exists()}")
    print(f"  PERSONAL_DIR exists: {personal_dir.exists()}")
    print(f"  AUTONOMY_DIR exists: {autonomy_dir.exists()}")
    print(f"  CLAP_DIR exists: {clap_dir.exists()}")
    print(f"  CLAUDE_CONFIG_DIR exists: {config_dir.exists()}")