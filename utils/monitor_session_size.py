#!/usr/bin/env python3
"""
Monitor current Claude Code session file size and report as percentage of configurable threshold.
Based on scientific analysis of 218 sessions showing optimal threshold at 1MB.
Supports configuration via context_monitoring.json or environment variables.
"""

import os
import sys
import json
from pathlib import Path
import subprocess

# Default thresholds based on scientific analysis
DEFAULT_THRESHOLD_MB = 1.0  # Primary threshold where issues begin
DEFAULT_WARNING_LEVELS = {
    'yellow': 0.6,  # 60% - start awareness
    'orange': 0.8,  # 80% - plan for swap
    'red': 1.0      # 100% - immediate action
}

def load_config():
    """Load configuration from file or environment."""
    config_path = Path(__file__).parent.parent / "config" / "context_monitoring.json"
    
    # Try to load from config file
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return {
                    'threshold_mb': config.get('threshold_mb', DEFAULT_THRESHOLD_MB),
                    'warning_levels': config.get('warning_levels', DEFAULT_WARNING_LEVELS)
                }
        except Exception as e:
            print(f"Warning: Failed to load config: {e}", file=sys.stderr)
    
    # Check environment variables as fallback
    threshold_mb = float(os.getenv('CLAUDE_CONTEXT_THRESHOLD_MB', DEFAULT_THRESHOLD_MB))
    
    return {
        'threshold_mb': threshold_mb,
        'warning_levels': DEFAULT_WARNING_LEVELS
    }

# Load configuration
config = load_config()
THRESHOLD_BYTES = config['threshold_mb'] * 1024 * 1024  # Convert MB to bytes
WARNING_LEVELS = config['warning_levels']

# Get the project directory dynamically
PROJECT_DIR = Path(__file__).parent.parent
PROJECT_NAME = PROJECT_DIR.name
SESSION_DIR = Path.home() / ".config/Claude/projects" / f"-home-{os.getlogin()}-{PROJECT_NAME}"

def find_current_session():
    """Find the most recently modified JSONL session file"""
    try:
        # Use find command to get most recent file
        cmd = f"cd {SESSION_DIR} && find . -name '*.jsonl' -type f -printf '%T@ %p\\n' | sort -n | tail -1 | cut -d' ' -f2"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            filename = result.stdout.strip()
            if filename.startswith('./'):
                filename = filename[2:]
            return SESSION_DIR / filename
        else:
            return None
    except Exception as e:
        print(f"Error finding session file: {e}", file=sys.stderr)
        return None

def get_session_size(filepath):
    """Get session file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except Exception as e:
        print(f"Error getting file size: {e}", file=sys.stderr)
        return 0

def calculate_context_percentage(size_bytes):
    """Calculate percentage of 1MB threshold"""
    return (size_bytes / THRESHOLD_BYTES) * 100

def get_context_status(percentage):
    """Determine context status based on configurable percentage thresholds"""
    percent_ratio = percentage / 100.0
    
    if percent_ratio >= WARNING_LEVELS.get('red', 1.0):
        return "CRITICAL", "🔴"
    elif percent_ratio >= WARNING_LEVELS.get('orange', 0.8):
        return "WARNING", "🟠"
    elif percent_ratio >= WARNING_LEVELS.get('yellow', 0.6):
        return "CAUTION", "🟡"
    else:
        return "NORMAL", "🟢"

def format_size(bytes):
    """Format bytes to human readable"""
    mb = bytes / (1024 * 1024)
    kb = bytes / 1024
    
    if mb >= 1:
        return f"{mb:.2f} MB"
    else:
        return f"{kb:.0f} KB"

def main():
    """Main monitoring function"""
    # Find current session
    session_file = find_current_session()
    
    if not session_file or not session_file.exists():
        print("No active session file found")
        return
    
    # Get size and calculate percentage
    size_bytes = get_session_size(session_file)
    percentage = calculate_context_percentage(size_bytes)
    status, emoji = get_context_status(percentage)
    
    # Output format for autonomous-timer
    print(f"Context: {percentage:.1f}% {emoji}")
    print(f"Size: {format_size(size_bytes)} / {config['threshold_mb']} MB")
    print(f"Status: {status}")
    
    # If we're in warning/critical zone, provide recommendations
    if percentage >= WARNING_LEVELS.get('orange', 0.8) * 100:
        print("\n⚠️ RECOMMENDED ACTION:")
        if percentage >= 100:
            print("- Trigger session swap NOW")
            print("- Save critical work to rag-memory")
            print("- Write swap keyword to new_session.txt")
        else:
            print("- Plan session swap soon")
            print("- Complete current task")
            print("- Save important context")
    
    # Return exit code based on status
    if percentage >= 100:
        sys.exit(2)  # Critical
    elif percentage >= 80:
        sys.exit(1)  # Warning
    else:
        sys.exit(0)  # Normal

if __name__ == "__main__":
    main()