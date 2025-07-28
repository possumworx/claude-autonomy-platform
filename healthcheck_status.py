#!/usr/bin/env python3
"""
Healthcheck Status Monitor
Fetches status from healthchecks.io API to give Claude visibility into system health
"""

import requests
import json
import subprocess
from datetime import datetime

# API configuration
from infrastructure_config_reader import get_config_value
API_KEY = get_config_value('HEALTHCHECK_API_KEY')
BASE_URL = "https://healthchecks.io/api/v3"

# Required tmux sessions for autonomous operation
REQUIRED_TMUX_SESSIONS = ["autonomous-claude", "persistent-login"]

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
    
    # Check tmux sessions first
    tmux_status = check_tmux_sessions()
    print("📺 Tmux Sessions:")
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
    
    total_issues = down_count + tmux_issues
    if total_issues > 0:
        print(f"\n⚠️  ATTENTION: {total_issues} issues detected - investigate!")
        if tmux_issues > 0:
            print("💡 Missing tmux sessions can be recreated with:")
            for session, is_running in tmux_status.items():
                if not is_running:
                    print(f"   tmux new-session -d -s {session}")
    else:
        print("\n🎉 All monitored services are operational!")

def main():
    """Main function"""
    data = fetch_health_status()
    display_health_status(data)

if __name__ == "__main__":
    main()