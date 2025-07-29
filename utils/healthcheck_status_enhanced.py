#!/usr/bin/env python3
"""
Healthcheck Status Monitor
Fetches status from healthchecks.io API to give Claude visibility into system health
Now includes configuration file checks
"""

import requests
import json
import subprocess
from datetime import datetime
import os
from pathlib import Path

# API configuration
API_KEY = "hcr_icPvO9biFPnjkZfI8PgDNy16zlIV"
BASE_URL = "https://healthchecks.io/api/v3"

# Required tmux sessions for autonomous operation
REQUIRED_TMUX_SESSIONS = ["autonomous-claude", "persistent-login"]

# Configuration file locations
CONFIG_LOCATIONS = {
    "Claude Code Config": "~/.config/Claude/.claude.json",
    "Infrastructure Config": "~/claude-autonomy-platform/config/claude_infrastructure_config.txt",
    "Notification Config": "~/claude-autonomy-platform/config/notification_config.json"
}

# Deprecated/old config locations to warn about
DEPRECATED_CONFIGS = {
    "~/claude_config.json": "Old Claude config location - should use ~/.config/Claude/.claude.json",
    "~/claude-autonomy-platform/claude_infrastructure_config.txt": "Old infrastructure config - should be in config/ subdirectory"
}

def check_config_files():
    """Check configuration file status and warn about deprecated locations"""
    print("\n📁 Configuration Files:")
    issues = []
    
    # Check current config files
    for name, path in CONFIG_LOCATIONS.items():
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            try:
                stat = os.stat(expanded_path)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                size = stat.st_size
                print(f"  ✅ {name}: {path}")
                print(f"     Modified: {mtime}, Size: {size} bytes")
            except Exception as e:
                print(f"  ⚠️  {name}: {path} - Error reading: {e}")
                issues.append(f"Cannot read {name}")
        else:
            print(f"  ❌ {name}: {path} - NOT FOUND")
            issues.append(f"{name} missing")
    
    # Check for deprecated configs
    deprecated_found = []
    for old_path, message in DEPRECATED_CONFIGS.items():
        expanded_path = os.path.expanduser(old_path)
        if os.path.exists(expanded_path):
            deprecated_found.append((old_path, message))
    
    if deprecated_found:
        print("\n⚠️  DEPRECATED CONFIG FILES DETECTED:")
        for path, message in deprecated_found:
            print(f"  ❗ {path}")
            print(f"     {message}")
        print("\n  These files are NOT being used and may cause confusion!")
        issues.append(f"{len(deprecated_found)} deprecated config files found")
    
    return issues

def fetch_health_status():
    """Fetch all check statuses from healthchecks.io"""
    headers = {
        "X-Api-Key": API_KEY
    }
    
    try:
        response = requests.get(f"{BASE_URL}/checks/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"🌐 NETWORK ERROR: Unable to reach healthchecks.io")
        print(f"This indicates a network connectivity problem, not individual service issues.")
        print(f"Technical details: {e}")
        return None

def check_tmux_sessions():
    """Check if required tmux sessions are running"""
    try:
        result = subprocess.run(['tmux', 'list-sessions'], 
                              capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            # tmux not running or no sessions
            return {session: False for session in REQUIRED_TMUX_SESSIONS}
        
        # Parse tmux output to get session names
        running_sessions = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                session_name = line.split(':')[0]
                running_sessions.append(session_name)
        
        # Check if each required session exists
        session_status = {}
        for session in REQUIRED_TMUX_SESSIONS:
            session_status[session] = session in running_sessions
            
        return session_status
        
    except Exception as e:
        print(f"Error checking tmux sessions: {e}")
        return {session: False for session in REQUIRED_TMUX_SESSIONS}

def format_status(status):
    """Format status with emoji indicators"""
    status_map = {
        "up": "✅ UP",
        "down": "❌ DOWN", 
        "new": "🆕 NEW",
        "paused": "⏸️ PAUSED",
        "grace": "⚠️ GRACE"
    }
    return status_map.get(status, f"❓ {status.upper()}")

def display_health_status(data):
    """Display health status in a clean format"""
    print(f"\n🏥 System Health Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_issues = []
    
    # Check configuration files first
    config_issues = check_config_files()
    all_issues.extend(config_issues)
    
    # Check tmux sessions
    tmux_status = check_tmux_sessions()
    print("\n📺 Tmux Sessions:")
    tmux_issues = 0
    for session, is_running in tmux_status.items():
        if is_running:
            print(f"  ✅ UP        {session}")
        else:
            print(f"  ❌ DOWN      {session}")
            tmux_issues += 1
    
    print("\n🌐 Remote Health Checks:")
    if not data or "checks" not in data:
        print("❌ Unable to fetch health status - check network connectivity")
        return
    
    checks = data["checks"]
    
    # Group by status
    up_count = down_count = other_count = 0
    
    for check in checks:
        name = check.get("name", "Unnamed Check")
        status = check.get("status", "unknown")
        last_ping = check.get("last_ping")
        
        if status == "up":
            up_count += 1
        elif status == "down":
            down_count += 1
        else:
            other_count += 1
        
        # Format last ping time
        last_ping_str = "Never"
        if last_ping:
            try:
                ping_time = datetime.fromisoformat(last_ping.replace('Z', '+00:00'))
                last_ping_str = ping_time.strftime('%m-%d %H:%M')
            except:
                last_ping_str = "Unknown"
        
        print(f"{format_status(status):12} {name:30} Last: {last_ping_str}")
    
    print("=" * 60)
    print(f"Remote: {up_count} UP, {down_count} DOWN, {other_count} OTHER")
    print(f"Tmux: {len(REQUIRED_TMUX_SESSIONS) - tmux_issues} UP, {tmux_issues} DOWN")
    print(f"Config: {len(config_issues)} issues")
    
    total_issues = down_count + tmux_issues + len(config_issues)
    if total_issues > 0:
        print(f"\n⚠️  ATTENTION: {total_issues} issues detected:")
        if config_issues:
            print("\n📁 Config Issues:")
            for issue in config_issues:
                print(f"   - {issue}")
        if tmux_issues > 0:
            print("\n💡 Missing tmux sessions can be recreated with:")
            for session, is_running in tmux_status.items():
                if not is_running:
                    print(f"   tmux new-session -d -s {session}")
    else:
        print("\n🎉 All monitored services and configurations are operational!")

def main():
    """Main function"""
    data = fetch_health_status()
    display_health_status(data)

if __name__ == "__main__":
    main()
