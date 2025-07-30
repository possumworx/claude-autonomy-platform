#!/usr/bin/env python3
"""
Test script for communications monitor
"""

import subprocess
import time
import json

def test_tmux_notification():
    """Test sending a notification to Claude via tmux"""
    print("Testing tmux notification system...")
    
    try:
        session = "autonomous-claude"
        test_message = "[TEST] This is a test notification from the comms monitor system"
        
        cmd = f'tmux send-keys -t {session} "{test_message}" Enter'
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        
        print(f"✅ Successfully sent test notification to {session}")
        print(f"Command: {cmd}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error sending notification: {e}")
        print(f"Command failed: {cmd}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_config_loading():
    """Test loading the configuration file"""
    print("\nTesting configuration loading...")
    
    try:
        config_file = "/home/sonnet-4/claude-autonomy-platform/comms_monitor_config.json"
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print("✅ Configuration loaded successfully")
        print(f"Gmail interval: {config['check_intervals']['gmail']} seconds")
        print(f"Discord interval: {config['check_intervals']['discord']} seconds")
        print(f"Tmux session: {config['tmux_session']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def main():
    """Run tests"""
    print("=== Communications Monitor Test Suite ===\n")
    
    # Test configuration loading
    config_ok = test_config_loading()
    
    # Test tmux notifications
    tmux_ok = test_tmux_notification()
    
    print(f"\n=== Test Results ===")
    print(f"Configuration loading: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Tmux notifications: {'✅ PASS' if tmux_ok else '❌ FAIL'}")
    
    if config_ok and tmux_ok:
        print("\n🎉 All tests passed! The comms monitor is ready to use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    exit(main())