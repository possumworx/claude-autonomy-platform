#!/usr/bin/env python3
"""
Create a systemd-compatible environment file from claude_infrastructure_config.txt
This generates claude.env which can be used by systemd services (POSS-76)
"""

import os
from pathlib import Path

def create_systemd_env():
    """Create a systemd-compatible environment file"""
    
    # Get the ClAP directory from environment or find it
    clap_dir = os.environ.get('CLAP_DIR')
    if not clap_dir:
        clap_dir = Path.home() / "claude-autonomy-platform"
        if not clap_dir.exists():
            clap_dir = Path.home() / "Claude-Autonomy-Platform"
    else:
        clap_dir = Path(clap_dir)
    
    config_file = clap_dir / "config" / "claude_infrastructure_config.txt"
    env_file = clap_dir / "config" / "claude.env"
    
    if not config_file.exists():
        print(f"❌ Error: {config_file} not found")
        return False
    
    # Read config and extract key variables
    env_vars = {}
    
    # Set basic paths
    current_user = os.environ.get('USER', os.environ.get('CLAUDE_USER', 'claude'))
    home_dir = Path.home()
    
    env_vars['CLAUDE_USER'] = current_user
    env_vars['CLAUDE_HOME'] = str(home_dir)
    env_vars['CLAP_DIR'] = str(clap_dir)
    env_vars['AUTONOMY_DIR'] = str(clap_dir)
    
    # Read values from config
    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                # Only include simple values for systemd
                if key in ['PERSONAL_REPO', 'DISCORD_TOKEN', 'CLAUDE_DISCORD_USER_ID', 
                          'DISCORD_HEADLESS', 'MODEL', 'LINUX_USER', 'CLAUDE_NAME']:
                    env_vars[key] = value
    
    # Set derived paths
    if 'PERSONAL_REPO' in env_vars:
        env_vars['PERSONAL_DIR'] = str(home_dir / env_vars['PERSONAL_REPO'])
    
    # Write systemd environment file
    with open(env_file, 'w') as f:
        for key, value in env_vars.items():
            # Systemd format: no export, no quotes unless needed
            f.write(f"{key}={value}\n")
    
    print(f"✅ Created {env_file}")
    return True

if __name__ == "__main__":
    print("🔧 Creating systemd-compatible environment file...")
    if create_systemd_env():
        print("\n✅ Done! The services will now use claude.env instead of claude_env.sh")
        print("This eliminates the systemd syntax warnings.")
