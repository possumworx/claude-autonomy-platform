#!/usr/bin/env python3
"""
Healthcheck Status Monitor
Fetches status from healthchecks.io API to give Claude visibility into system health
"""

import requests
import json
from datetime import datetime

# API configuration
API_KEY = "hcr_icPvO9biFPnjkZfI8PgDNy16zlIV"
BASE_URL = "https://healthchecks.io/api/v3"

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
    if not data or "checks" not in data:
        print("❌ Unable to fetch health status - check network connectivity")
        return
    
    checks = data["checks"]
    print(f"\n🏥 System Health Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
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
    print(f"Summary: {up_count} UP, {down_count} DOWN, {other_count} OTHER")
    
    if down_count > 0:
        print("\n⚠️  ATTENTION: Some services are DOWN - investigate!")
    else:
        print("\n🎉 All monitored services are operational!")

def main():
    """Main function"""
    data = fetch_health_status()
    display_health_status(data)

if __name__ == "__main__":
    main()