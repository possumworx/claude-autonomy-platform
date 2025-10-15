#!/usr/bin/env python3
"""
Monitor current Claude Code session token usage and report as percentage of 200K token budget.
Uses actual token counts from session JSONL files, not file size.
Supports configuration via context_monitoring.json or environment variables.
"""

import os
import sys
import json
from pathlib import Path
import subprocess

# Claude token budget
TOKEN_BUDGET = 200000

# Warning levels based on token percentage
DEFAULT_WARNING_LEVELS = {
    'yellow': 0.6,   # 60% - start awareness (120K tokens)
    'orange': 0.8,   # 80% - plan for swap (160K tokens)
    'red': 0.9       # 90% - immediate action (180K tokens)
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
                    'token_budget': config.get('token_budget', TOKEN_BUDGET),
                    'warning_levels': config.get('warning_levels', DEFAULT_WARNING_LEVELS)
                }
        except Exception as e:
            print(f"Warning: Failed to load config: {e}", file=sys.stderr)

    return {
        'token_budget': TOKEN_BUDGET,
        'warning_levels': DEFAULT_WARNING_LEVELS
    }

# Load configuration
config = load_config()
TOKEN_BUDGET = config['token_budget']
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

def get_latest_token_usage(filepath):
    """Extract token usage from the most recent message with usage data"""
    try:
        # Read the last 20 lines to find the most recent message with token usage
        cmd = f"tail -20 {filepath} | jq -r 'select(.message.usage) | .message.usage | (.input_tokens + .cache_read_input_tokens + (.output_tokens // 0))' | tail -1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
        else:
            return 0
    except Exception as e:
        print(f"Error extracting token usage: {e}", file=sys.stderr)
        return 0

def calculate_context_percentage(token_count):
    """Calculate percentage of token budget used"""
    return (token_count / TOKEN_BUDGET) * 100

def get_context_status(percentage):
    """Determine context status based on configurable percentage thresholds"""
    percent_ratio = percentage / 100.0

    if percent_ratio >= WARNING_LEVELS.get('red', 0.9):
        return "CRITICAL", "🔴"
    elif percent_ratio >= WARNING_LEVELS.get('orange', 0.8):
        return "WARNING", "🟠"
    elif percent_ratio >= WARNING_LEVELS.get('yellow', 0.6):
        return "CAUTION", "🟡"
    else:
        return "NORMAL", "🟢"

def format_tokens(tokens):
    """Format token count to human readable"""
    if tokens >= 1000:
        return f"{tokens/1000:.1f}K"
    else:
        return f"{tokens}"

def main():
    """Main monitoring function"""
    # Find current session
    session_file = find_current_session()

    if not session_file or not session_file.exists():
        print("No active session file found")
        return

    # Get token usage and calculate percentage
    token_count = get_latest_token_usage(session_file)
    percentage = calculate_context_percentage(token_count)
    status, emoji = get_context_status(percentage)

    # Output format for autonomous-timer
    print(f"Context: {percentage:.1f}% {emoji}")
    print(f"Tokens: {format_tokens(token_count)} / {format_tokens(TOKEN_BUDGET)}")
    print(f"Status: {status}")

    # If we're in warning/critical zone, provide recommendations
    if percentage >= WARNING_LEVELS.get('orange', 0.8) * 100:
        print("\n⚠️ RECOMMENDED ACTION:")
        if percentage >= WARNING_LEVELS.get('red', 0.9) * 100:
            print("- Trigger session swap NOW")
            print("- Save critical work to rag-memory")
            print("- Write swap keyword to new_session.txt")
        else:
            print("- Plan session swap soon")
            print("- Complete current task")
            print("- Save important context")

    # Return exit code based on status
    if percentage >= 90:
        sys.exit(2)  # Critical
    elif percentage >= 80:
        sys.exit(1)  # Warning
    else:
        sys.exit(0)  # Normal

if __name__ == "__main__":
    main()
