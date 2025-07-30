#!/usr/bin/env python3
"""
Create a systemd-compatible environment file from claude_infrastructure_config.txt
This generates claude.env which can be used by systemd services
"""

import os
from pathlib import Path

def create_systemd_env():
    """Create a systemd-compatible environment file"""
    
    # Get the ClAP directory
    clap_dir = Path.home() / "Claude-Autonomy-Platform"
    if not clap_dir.exists():
        clap_dir = Path.home() / "claude-autonomy-platform"
    
    config_file = clap_dir / "claude_infrastructure_config.txt"
    env_file = clap_dir / "claude.env"
    
    if not config_file.exists():
        print(f"❌ Error: {config_file} not found")
        return False
    
    # Read config and extract key variables
    env_vars = {}
    
    # Set basic paths
    current_user = os.environ.get('USER', 'sparkle-sonnet')
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
                # Only include simple values, not complex ones
                if key in ['PERSONAL_REPO', 'DISCORD_TOKEN', 'CLAUDE_DISCORD_USER_ID', 
                          'DISCORD_HEADLESS', 'MODEL', 'LINUX_USER']:
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
    print("\nContents:")
    with open(env_file, 'r') as f:
        print(f.read())
    
    return True

def fix_service_files():
    """Update service files to use the new environment file"""
    systemd_dir = Path.home() / ".config/systemd/user"
    clap_dir = Path.home() / "Claude-Autonomy-Platform"
    if not clap_dir.exists():
        clap_dir = Path.home() / "claude-autonomy-platform"
    
    services = ['autonomous-timer.service', 'session-bridge-monitor.service', 
                'session-swap-monitor.service', 'channel-monitor.service']
    
    for service in services:
        service_file = systemd_dir / service
        if service_file.exists():
            # Read the current content
            with open(service_file, 'r') as f:
                content = f.read()
            
            # Replace claude_env.sh with claude.env
            content = content.replace('claude_env.sh', 'claude.env')
            
            # Write back
            with open(service_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Updated {service}")

if __name__ == "__main__":
    print("🔧 Creating systemd-compatible environment file...")
    if create_systemd_env():
        print("\n🔧 Updating service files...")
        fix_service_files()
        print("\n✅ Done! Now reload and restart services:")
        print("   systemctl --user daemon-reload")
        print("   ./claude_services.sh restart")
