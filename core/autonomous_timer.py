#!/usr/bin/env python3
"""
Autonomous Timer Script for Claude
Simple replacement for the hook system using tmux send-keys

This script runs continuously and:
- Checks for new Discord messages every 30 seconds
- Sends free time prompts every 2 minutes when Amy is away
- Uses tmux send-keys to communicate with the permanent Claude session
"""

import time
import os
import json
import subprocess
import sys
import glob
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Import path utilities
# Add parent directory to path to find utils module
sys.path.append(str(Path(__file__).parent.parent))
# Add utils directory specifically for infrastructure_config_reader's imports
sys.path.append(str(Path(__file__).parent.parent / "utils"))
from utils.claude_paths import get_clap_dir
from utils.infrastructure_config_reader import get_config_value
from utils.track_activity import is_idle
from utils.check_seeds import get_seed_reminder
from utils.check_context import check_context
from utils.check_usage import check_usage

# Configuration
AUTONOMY_DIR = get_clap_dir()
DATA_DIR = AUTONOMY_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)  # Ensure data directory exists
LAST_AUTONOMY_FILE = DATA_DIR / "last_autonomy_prompt.txt"
LOG_FILE = (
    AUTONOMY_DIR / "logs" / "autonomous_timer.log"
)  # POSS-239: Standardized log location
CONFIG_FILE = AUTONOMY_DIR / "config" / "autonomous_timer_config.json"
PROMPTS_FILE = AUTONOMY_DIR / "config" / "prompts.json"
SWAP_LOG_FILE = AUTONOMY_DIR / "logs" / "swap_attempts.log"
CONTEXT_STATE_FILE = DATA_DIR / "context_escalation_state.json"
API_ERROR_STATE_FILE = DATA_DIR / "api_error_state.json"
RESOURCE_TRACKING_STATE_FILE = DATA_DIR / "last_cache_tokens.json"

# Create logs directory if it doesn't exist
(AUTONOMY_DIR / "logs").mkdir(exist_ok=True)

# Resource-share webhook configuration
WEBHOOK_HOST = get_config_value("WEBHOOK_HOST", "localhost")
RESOURCE_SHARE_WEBHOOK_URL = f"http://{WEBHOOK_HOST}:8765/resource-share/increment"

# Discord API configuration
DISCORD_API_BASE = "https://discord.com/api/v10"
INFRA_CONFIG = AUTONOMY_DIR / "config" / "claude_infrastructure_config.txt"


def log_message(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    print(log_entry)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")


def is_tmux_session_attached():
    """Check if the autonomous-claude tmux session is currently attached"""
    try:
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name} #{session_attached}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line.startswith("autonomous-claude "):
                    # Line format: "autonomous-claude 1" (attached) or "autonomous-claude 0" (detached)
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "1":
                        return True
        return False
    except Exception as e:
        log_message(f"DEBUG: Error checking tmux attachment: {e}")
        return False  # Default to autonomy if we can't determine


def load_prompts_config():
    """Load prompts configuration from JSON file"""
    try:
        if PROMPTS_FILE.exists():
            with open(PROMPTS_FILE, "r") as f:
                return json.load(f)
        else:
            log_message(f"Prompts configuration file not found: {PROMPTS_FILE}")
            return None
    except Exception as e:
        log_message(f"Error loading prompts configuration: {e}")
        return None


# Load prompts at startup
PROMPTS_CONFIG = load_prompts_config()


def load_context_state():
    """Load context escalation state from file"""
    try:
        if CONTEXT_STATE_FILE.exists():
            with open(CONTEXT_STATE_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        log_message(f"Error loading context state: {e}")

    # Return default state
    return {
        "first_warning_sent": False,
        "last_warning_percentage": 0,
        "last_warning_time": None,
    }


def save_context_state(state):
    """Save context escalation state to file"""
    try:
        with open(CONTEXT_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log_message(f"Error saving context state: {e}")


def reset_context_state():
    """Reset context state after session swap"""
    save_context_state(
        {
            "first_warning_sent": False,
            "last_warning_percentage": 0,
            "last_warning_time": None,
        }
    )


def log_swap_attempt(attempt_type, context_percentage, keyword=None):
    """Log swap attempts for escalation tracking"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "type": attempt_type,  # "warning", "manual", "auto"
        "context": context_percentage,
        "keyword": keyword,
    }

    try:
        # Read existing log
        logs = []
        if SWAP_LOG_FILE.exists():
            with open(SWAP_LOG_FILE, "r") as f:
                for line in f:
                    try:
                        logs.append(json.loads(line))
                    except:
                        pass

        # Add new entry
        with open(SWAP_LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Return count of recent warnings for escalation
        recent_warnings = [
            l
            for l in logs[-10:]
            if l["type"] == "warning"
            and datetime.fromisoformat(l["timestamp"])
            > datetime.now() - timedelta(hours=1)
        ]
        return len(recent_warnings)

    except Exception as e:
        log_message(f"Error logging swap attempt: {e}")
        return 0


def ping_healthcheck():
    """Ping healthchecks.io to signal service is alive"""
    try:
        ping_url = get_config_value(
            "AUTONOMOUS_TIMER_PING",
            "https://hc-ping.com/075636dd-b5d3-4ae5-afac-c65bd0f630f3",
        )
        result = subprocess.run(
            ["curl", "-fsS", "-m", "10", "--retry", "3", "-o", "/dev/null", ping_url],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True
        else:
            log_message(f"Healthcheck ping failed: {result.stderr}")
            return False
    except Exception as e:
        log_message(f"Healthcheck ping error: {e}")
        return False


def check_claude_session_alive():
    """Verify Claude Code is actually running in the autonomous-claude tmux session"""
    try:
        # Check if autonomous-claude session exists
        result = subprocess.run(
            ["tmux", "has-session", "-t", CLAUDE_SESSION], capture_output=True
        )
        if result.returncode != 0:
            return False

        # Get the pane PID for autonomous-claude session
        result = subprocess.run(
            ["tmux", "list-panes", "-t", CLAUDE_SESSION, "-F", "#{pane_pid}"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False

        pane_pid = result.stdout.strip()
        if not pane_pid:
            return False

        # Check if claude process is running under this pane
        result = subprocess.run(
            ["pgrep", "-P", pane_pid, "claude"], capture_output=True
        )
        return result.returncode == 0

    except Exception as e:
        log_message(f"Error checking Claude session: {e}")
        return False


def ping_claude_session_healthcheck(is_alive):
    """Ping healthchecks.io for Claude Code session status"""
    base_url = get_config_value(
        "CLAUDE_CODE_PING", "https://hc-ping.com/759db9f0-78cc-409c-93ba-9f7b0ae4ede7"
    )

    try:
        if is_alive:
            # Normal ping for success
            url = base_url
        else:
            # Ping /fail to signal Claude session is down
            url = f"{base_url}/fail"

        result = subprocess.run(
            ["curl", "-fsS", "-m", "10", "--retry", "3", "-o", "/dev/null", url],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True
        else:
            log_message(f"Claude session healthcheck ping failed: {result.stderr}")
            return False
    except Exception as e:
        log_message(f"Claude session healthcheck ping error: {e}")
        return False


def get_token_percentage():
    """Get current session token usage percentage from monitor script or tmux"""
    try:
        # First try Delta's accurate context monitoring system
        log_message("DEBUG: Attempting check_context(return_data=True)")
        context_data, error = check_context(return_data=True)
        if not error and context_data:
            percentage = context_data["percentage"] * 100  # Convert to percentage
            # Determine emoji based on percentage
            if percentage >= 85:
                emoji = "🔴"
            elif percentage >= 70:
                emoji = "🟡"
            else:
                emoji = "🟢"
            log_message(f"DEBUG: check_context SUCCESS - {percentage:.1f}% {emoji}")
            return f"Context: {percentage:.1f}% {emoji}"

        log_message(
            f"DEBUG: check_context FAILED - error: {error}, has_data: {context_data is not None}"
        )

        # Fallback to tmux capture method if check_context fails
        # Capture the tmux session output WITH COLOR CODES
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", CLAUDE_SESSION, "-p", "-e"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return f"Tmux capture failed: {result.stderr}"

        # Look for context percentage patterns in the captured output
        import re

        console_output = result.stdout

        # Pattern 1: Look for simple "XX% remaining" anywhere
        simple_remaining = re.search(
            r"(\d+(?:\.\d+)?)%\s*remaining", console_output, re.IGNORECASE
        )
        if simple_remaining:
            remaining_percentage = float(simple_remaining.group(1))
            used_percentage = 100 - remaining_percentage
            return f"Context: {used_percentage:.1f}%"

        # Pattern 2: Look for Claude Code's specific format: "Context low (XX% remaining)"
        claude_format = re.search(
            r"Context\s+\w+\s+\((\d+(?:\.\d+)?)%\s+remaining\)",
            console_output,
            re.IGNORECASE,
        )
        if claude_format:
            remaining_percentage = float(claude_format.group(1))
            used_percentage = 100 - remaining_percentage
            return f"Context: {used_percentage:.1f}%"

        # Pattern 3: Look for other "Context: XX%" warnings/messages
        context_match = re.search(
            r"Context:\s*(\d+(?:\.\d+)?)%", console_output, re.IGNORECASE
        )
        if context_match:
            percentage = context_match.group(1)
            return f"Context: {percentage}%"

        # Pattern 4: Look for percentage warnings like "(XX%)"
        percent_match = re.search(r"\((\d+(?:\.\d+)?)%\)", console_output)
        if percent_match:
            percentage = percent_match.group(1)
            return f"Context: {percentage}%"

        # No context percentage found in console output
        return None

    except Exception as e:
        return f"Context check failed: {str(e)}"


def track_resource_usage():
    """
    Track usage cost and report to resource-share webhook.
    Gets $ cost delta from check_usage and POSTs to CoOP server.
    Also maintains cache token tracking for context display purposes.
    """
    global AUTONOMY_PROMPT_INTERVAL
    try:
        # Get usage cost delta from check_usage (primary metric for CoOP)
        usage_data, error = check_usage(return_data=True)
        if error or not usage_data:
            log_message(
                f"DEBUG: resource-share tracking skipped - check_usage failed: {error}"
            )
            return

        cost_delta = usage_data.get("delta_cost", 0.0)

        # Also get cache tokens for state tracking (context display purposes)
        context_data, context_error = check_context(return_data=True)
        current_cache_tokens = 0
        if not context_error and context_data:
            current_cache_tokens = context_data.get("cache_tokens", 0)

        # Only POST if cost_delta > 0
        if cost_delta > 0:
            # Get Claude name from infrastructure config
            claude_name = get_config_value("CLAUDE_NAME")
            if not claude_name:
                claude_name = "Unknown"  # Fallback

            # Detect mode based on tmux session attachment
            mode = "collaboration" if is_tmux_session_attached() else "autonomy"

            # Get hostname and IP for parallel instance detection
            import socket

            hostname = socket.gethostname()
            try:
                # Get primary IP address (first non-loopback)
                ip_address = socket.gethostbyname(hostname)
            except:
                ip_address = "unknown"

            # Prepare payload with current interval + instance identification
            payload = {
                "claude_name": claude_name,
                "cost_delta": cost_delta,
                "mode": mode,
                "current_interval": AUTONOMY_PROMPT_INTERVAL,
                "hostname": hostname,  # Parallel instance detection
                "ip_address": ip_address,  # Parallel instance detection
            }

            # POST to resource-share webhook
            try:
                response = requests.post(
                    RESOURCE_SHARE_WEBHOOK_URL, json=payload, timeout=5
                )
                if response.status_code == 200:
                    log_message(
                        f"DEBUG: resource-share reported ${cost_delta:.4f} cost for {claude_name}"
                    )

                    # Read recommended interval from response and update if provided
                    try:
                        response_data = response.json()
                        if "recommended_interval" in response_data:
                            new_interval = response_data["recommended_interval"]

                            # Validate interval is a positive integer
                            if (
                                isinstance(new_interval, (int, float))
                                and new_interval > 0
                            ):
                                old_interval = AUTONOMY_PROMPT_INTERVAL
                                AUTONOMY_PROMPT_INTERVAL = int(new_interval)

                                if new_interval != old_interval:
                                    log_message(
                                        f"INFO: Interval updated by CoOP: {old_interval}s → {new_interval}s "
                                        f"(fairness: {response_data.get('multipliers', {}).get('fairness', '?'):.2f}x, "
                                        f"quota: {response_data.get('quota_status', 'unknown')})"
                                    )
                            else:
                                log_message(
                                    f"WARNING: Invalid interval from CoOP: {new_interval} - keeping current {AUTONOMY_PROMPT_INTERVAL}s"
                                )
                    except (json.JSONDecodeError, KeyError) as e:
                        log_message(
                            f"DEBUG: Could not parse interval from response: {e}"
                        )
                else:
                    log_message(
                        f"WARNING: resource-share webhook returned {response.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                log_message(f"WARNING: resource-share webhook request failed: {e}")
        else:
            log_message(
                f"DEBUG: resource-share skipped - cost_delta is ${cost_delta:.4f} (need > 0)"
            )

        # Save current cache tokens for backwards compatibility (even if cost_delta was 0)
        # Note: check_usage.py handles its own state in last_usage_cost.json
        if current_cache_tokens > 0:
            with open(RESOURCE_TRACKING_STATE_FILE, "w") as f:
                json.dump({"cache_tokens": current_cache_tokens}, f)

    except Exception as e:
        log_message(f"ERROR: resource-share tracking failed: {e}")


def detect_api_errors(tmux_output):
    """
    Detect API errors in tmux output using color codes
    Returns: dict with error_type, details, and reset_time (if applicable)
    """
    # Split output into lines for position-aware checking
    lines = tmux_output.split("\n")

    # ANSI color codes:
    # [38;5;211m = Pink (errors)
    # [38;5;220m = Yellow (warnings)
    # [31m or [91m = Red (also errors)

    # Check last 2 lines for yellow warnings (approaching usage limit)
    if len(lines) >= 2:
        last_two_lines = "\n".join(lines[-2:])
        # Look for yellow text about approaching limit (with middle dot ·)
        yellow_pattern = r"\[38;5;220m.*?(approaching.*?usage.*?limit.*?[·•.].*?reset.*?(\d{1,2}(?::\d{2})?(?:am|pm)?))"
        yellow_match = re.search(yellow_pattern, last_two_lines, re.IGNORECASE)
        if yellow_match:
            reset_time = yellow_match.group(2) if yellow_match.lastindex >= 2 else None
            return {
                "error_type": "approaching_limit",
                "details": "Approaching usage limit warning",
                "reset_time": reset_time,
            }

    # Check for pink errors (38;5;211) anywhere in output
    pink_pattern = r"\[38;5;211m([^\[]*)"
    pink_matches = re.findall(pink_pattern, tmux_output)

    for error_text in pink_matches:
        # Skip auto-update warnings
        if "Auto-update failed" in error_text:
            continue

        # Check for malformed JSON
        if re.search(
            r"malformed.*json|json.*error|invalid.*json", error_text, re.IGNORECASE
        ):
            return {
                "error_type": "malformed_json",
                "details": "Malformed JSON detected - requires session swap",
                "reset_time": None,
            }

        # Check for 503 errors (upstream connect error or disconnect/reset)
        if re.search(
            r"503|upstream.*connect.*error|disconnect.*reset.*before.*headers",
            error_text,
            re.IGNORECASE,
        ):
            return {
                "error_type": "api_503_error",
                "details": "API 503 error - upstream connection failure",
                "reset_time": None,
            }

        # Check for usage limit errors
        usage_pattern = (
            r"limit will reset at (\d{1,2}(?::\d{2})?(?:am|pm)?)\s*\(([^)]+)\)"
        )
        usage_match = re.search(usage_pattern, error_text, re.IGNORECASE)
        if usage_match:
            reset_time_str = usage_match.group(1)
            timezone = usage_match.group(2)

            # Check if reset time has already passed
            try:
                from datetime import datetime
                import re as time_re

                current_time = datetime.now()

                # Parse the reset time
                time_parts = time_re.match(
                    r"(\d{1,2})(?::(\d{2}))?(?:am|pm)?",
                    reset_time_str,
                    time_re.IGNORECASE,
                )
                if time_parts:
                    hour = int(time_parts.group(1))
                    minute = int(time_parts.group(2) or 0)

                    # Handle AM/PM
                    if "pm" in reset_time_str.lower() and hour != 12:
                        hour += 12
                    elif "am" in reset_time_str.lower() and hour == 12:
                        hour = 0

                    # Create reset datetime for today
                    reset_datetime = current_time.replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )

                    # If reset time has passed, ignore this error
                    if current_time > reset_datetime:
                        log_message(
                            f"Ignoring expired usage limit (reset was at {reset_time_str}, now {current_time.strftime('%I:%M%p')})"
                        )
                        continue  # Check next pink text match

            except Exception as e:
                log_message(f"Error parsing reset time: {e}")
                # If we can't parse, report the error anyway

            return {
                "error_type": "usage_limit",
                "details": f"Usage limit reached - resets at {reset_time_str} ({timezone})",
                "reset_time": reset_time_str,
                "timezone": timezone,
            }

        # Check specifically for 400 errors
        if re.search(r"400.*error|bad.*request", error_text, re.IGNORECASE):
            return {
                "error_type": "api_400_error",
                "details": "API 400 error - requires session swap",
                "reset_time": None,
            }

        # General API errors in pink text
        if re.search(r"404.*error|api.*error|rate.*limit", error_text, re.IGNORECASE):
            # Check specifically for 500 errors
            if re.search(
                r"500.*error|internal.*server.*error", error_text, re.IGNORECASE
            ):
                return {
                    "error_type": "api_500_error",
                    "details": "API 500 error - requires session swap",
                    "reset_time": None,
                }
            return {
                "error_type": "api_error",
                "details": "API error detected in console",
                "reset_time": None,
            }

    # Check for red errors (31m or 91m)
    red_pattern = r"\[(31|91)m([^\[]*)"
    red_matches = re.findall(red_pattern, tmux_output)

    for _, error_text in red_matches:
        if re.search(r"error|limit|failed", error_text, re.IGNORECASE):
            return {
                "error_type": "api_error",
                "details": "Error detected in console (red text)",
                "reset_time": None,
            }

    # No errors found in colored text
    return None


def save_error_state(error_info):
    """Save current error state to file"""
    error_info["timestamp"] = datetime.now().isoformat()
    with open(API_ERROR_STATE_FILE, "w") as f:
        json.dump(error_info, f, indent=2)


def load_error_state():
    """Load saved error state"""
    if API_ERROR_STATE_FILE.exists():
        try:
            with open(API_ERROR_STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None


def clear_error_state():
    """Clear error state after recovery"""
    if API_ERROR_STATE_FILE.exists():
        API_ERROR_STATE_FILE.unlink()
        log_message("Error state cleared")


def check_usage_limit_reset(error_state):
    """
    Check if a usage limit error has passed its reset time
    Returns True if reset time has passed (with 5 minute grace period)
    """
    if not error_state or error_state.get("error_type") != "usage_limit":
        return False

    reset_time_str = error_state.get("reset_time")
    if not reset_time_str:
        return False

    try:
        from datetime import datetime, timedelta
        import re

        current_time = datetime.now()

        # Parse the reset time (e.g., "12pm", "3:30pm", "11am")
        time_match = re.match(
            r"(\d{1,2})(?::(\d{2}))?(?:am|pm)?", reset_time_str, re.IGNORECASE
        )
        if not time_match:
            return False

        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)

        # Handle AM/PM
        if "pm" in reset_time_str.lower() and hour != 12:
            hour += 12
        elif "am" in reset_time_str.lower() and hour == 12:
            hour = 0

        # Create reset datetime for today
        reset_datetime = current_time.replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )

        # If reset time is earlier in the day and has passed, the limit should be cleared
        # Add 5 minute grace period to avoid race conditions with API
        if current_time > reset_datetime + timedelta(minutes=5):
            return True

    except Exception as e:
        log_message(f"Error checking reset time: {e}")
        return False

    return False


def calculate_wait_until_reset(reset_time_str):
    """
    Calculate how long to wait until the reset time
    Returns wait duration in seconds
    """
    try:
        from datetime import datetime, timedelta
        import re

        current_time = datetime.now()

        # Parse the reset time
        time_match = re.match(
            r"(\d{1,2})(?::(\d{2}))?(?:am|pm)?", reset_time_str, re.IGNORECASE
        )
        if not time_match:
            return None

        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)

        # Handle AM/PM
        if "pm" in reset_time_str.lower() and hour != 12:
            hour += 12
        elif "am" in reset_time_str.lower() and hour == 12:
            hour = 0

        # Create reset datetime for today
        reset_datetime = current_time.replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )

        # If reset time has already passed today, assume it's for tomorrow
        if reset_datetime <= current_time:
            reset_datetime += timedelta(days=1)

        # Add 5 minute grace period
        reset_datetime += timedelta(minutes=5)

        # Calculate wait duration
        wait_duration = (reset_datetime - current_time).total_seconds()

        return max(0, wait_duration)

    except Exception as e:
        log_message(f"Error calculating wait duration: {e}")
        return None


def update_discord_status(status_type, reset_time=None):
    """Update Discord bot status via persistent bot

    Status types:
    - operational: Normal operation (green online)
    - limited: Usage limit reached (yellow idle)
    - api-error: API errors (red dnd)
    - context-high: High context (yellow idle)
    """
    try:
        # Map our status types to Discord presence format
        status_map = {
            "operational": {
                "status": "online",
                "activities": [{"name": "✅ Operational", "type": 3}],  # Watching
            },
            "limited": {
                "status": "idle",
                "activities": [
                    {
                        "name": f"⏳ Limited until {reset_time}"
                        if reset_time
                        else "⏳ Usage limit",
                        "type": 3,  # Watching
                    }
                ],
            },
            "api-error": {
                "status": "dnd",
                "activities": [{"name": "❌ API Error", "type": 3}],  # Watching
            },
            "context-high": {
                "status": "idle",
                "activities": [
                    {
                        "name": f"⚠️ Context {reset_time}%"
                        if reset_time
                        else "⚠️ High Context",
                        "type": 3,  # Watching
                    }
                ],
            },
        }

        # Get the status configuration
        presence = status_map.get(status_type, status_map["operational"])

        # Write status request for persistent bot to pick up
        status_file = DATA_DIR / "bot_status.json"
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "presence": presence,
            "source": "autonomous_timer",
        }

        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)

        log_message(f"Discord status request written: {status_type}")

    except Exception as e:
        log_message(f"Error updating Discord status: {e}")


def trigger_session_swap(keyword="NONE"):
    """Trigger automatic session swap"""
    try:
        new_session_file = AUTONOMY_DIR / "scripts" / "new_session.txt"
        with open(new_session_file, "w") as f:
            f.write(keyword)
        log_message(f"Triggered automatic session swap with keyword: {keyword}")
        return True
    except Exception as e:
        log_message(f"Error triggering session swap: {e}")
        return False


def should_pause_notifications(error_state):
    """Determine if notifications should be paused based on error state"""
    if not error_state:
        return False

    error_type = error_state.get("error_type")
    if error_type in ["malformed_json", "usage_limit", "api_error", "api_500_error"]:
        return True

    return False


def get_token_percentage_and_errors():
    """Get current session token usage percentage AND detect API errors"""
    try:
        # Capture the tmux session output WITH COLOR CODES
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", CLAUDE_SESSION, "-p", "-e"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return None, None

        console_output = result.stdout

        # Check for API errors (now with color awareness)
        error_info = detect_api_errors(console_output)

        # Return both the console output and error info
        return console_output, error_info

    except Exception as e:
        log_message(f"Error in monitoring: {str(e)}")
        return None, None


def check_and_handle_rate_limit_menu():
    """Check if stuck in rate limit menu and auto-select option 1 (wait for reset)

    The new Claude Code rate limit handling opens an interactive menu that blocks
    autonomous operation. This function detects when we're stuck in the menu and
    automatically selects option 1 to resume waiting for the rate limit reset.
    """
    try:
        # Capture tmux pane output
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", CLAUDE_SESSION, "-p"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return False

        console_output = result.stdout

        # Check if we're in the rate limit menu
        if "> /rate-limit-options" in console_output:
            log_message(
                "⚠️  Detected rate limit menu - automatically selecting option 1 (stop and wait)"
            )

            # Send "1" to select "Stop and wait for limit to reset"
            subprocess.run(["tmux", "send-keys", "-t", CLAUDE_SESSION, "1", "Enter"])

            log_message(
                "✅ Sent option 1 - Claude Code should now be waiting for rate limit reset"
            )
            return True

        return False

    except Exception as e:
        log_message(f"Error checking rate limit menu: {e}")
        return False


def load_discord_config():
    """Load Discord bot token and user ID from infrastructure config"""
    config = {"token": None, "user_id": None}
    try:
        if INFRA_CONFIG.exists():
            with open(INFRA_CONFIG, "r") as f:
                for line in f:
                    if line.startswith("DISCORD_BOT_TOKEN="):
                        config["token"] = line.split("=", 1)[1].strip()
                    # Also check for old name for backwards compatibility
                    elif line.startswith("DISCORD_TOKEN="):
                        config["token"] = line.split("=", 1)[1].strip()
                    elif line.startswith("CLAUDE_DISCORD_USER_ID="):
                        config["user_id"] = line.split("=", 1)[1].strip()
        if not config["token"]:
            log_message("Warning: No Discord token found in infrastructure config")
        if not config["user_id"]:
            log_message("Warning: No Discord user ID found in infrastructure config")
        return config
    except Exception as e:
        log_message(f"Error loading Discord config: {e}")
        return config


def load_config():
    """Load configuration from autonomous_timer_config.json"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            # Read flat config structure
            return {
                "discord_check_interval": config.get("discord_check_interval", 30),
                "autonomy_prompt_interval": config.get(
                    "autonomy_prompt_interval", 1800
                ),
                "claude_session": config.get("claude_session", "autonomous-claude"),
            }
        else:
            # Default config if file doesn't exist
            return {
                "discord_check_interval": 30,
                "autonomy_prompt_interval": 1800,
                "claude_session": "autonomous-claude",
            }
    except Exception as e:
        print(f"Error loading config: {e}, using defaults")
        return {
            "discord_check_interval": 30,
            "autonomy_prompt_interval": 1800,
            "claude_session": "autonomous-claude",
        }


# Load configuration
config = load_config()
DISCORD_CHECK_INTERVAL = config["discord_check_interval"]
# AUTONOMY_PROMPT_INTERVAL is mutable - updated by CoOP allocation calculator
AUTONOMY_PROMPT_INTERVAL = config["autonomy_prompt_interval"]
LOGGED_IN_REMINDER_INTERVAL = config.get(
    "logged_in_reminder_interval", 300
)  # 5 minutes default
CLAUDE_SESSION = config["claude_session"]

# Load Discord configuration
discord_config = load_discord_config()
DISCORD_TOKEN = discord_config["token"]
CLAUDE_USER_ID = discord_config["user_id"]


def check_user_active():
    """Check if the autonomous-claude tmux session is attached (collaborative mode)"""
    try:
        # Check if MY tmux session is attached, not just if Amy is logged in somewhere
        # Amy might be logged in but working with Apple, or on lsr-os, etc.
        attached = is_tmux_session_attached()
        if attached:
            log_message(
                "autonomous-claude tmux session is attached (collaborative mode)"
            )
        return attached
    except Exception as e:
        log_message(f"Error checking tmux attachment: {e}")
        return False


def get_last_discord_message_time():
    """Get the timestamp of the last Discord message (returns UTC timestamp string)"""
    try:
        if not CONVERSATION_LOG.exists():
            return None

        with open(CONVERSATION_LOG, "r") as f:
            content = f.read().strip()

        if not content:
            return None

        # Split by \n to get individual messages (they're escape sequences on one line)
        messages = content.split("\\n")

        # Find the last message with a timestamp
        for message in reversed(messages):
            message = message.strip()
            if message.startswith("[") and "]" in message:
                # Extract timestamp: [2025-07-10 07:31:48]
                timestamp_str = message.split("]")[0][1:]
                return timestamp_str  # Return raw UTC timestamp string

    except Exception as e:
        log_message(f"Error getting last Discord message time: {e}")

    return None


def get_last_processed_message_time():
    """Get the timestamp of the last Discord message we processed"""
    try:
        if LAST_PROCESSED_MESSAGE_FILE.exists():
            with open(LAST_PROCESSED_MESSAGE_FILE, "r") as f:
                return f.read().strip()
    except:
        pass
    return None


def update_last_processed_message_time(timestamp_str):
    """Update the last processed message timestamp"""
    try:
        with open(LAST_PROCESSED_MESSAGE_FILE, "w") as f:
            f.write(timestamp_str)
    except Exception as e:
        log_message(f"Error updating last processed message time: {e}")


def send_tmux_message(message):
    """Send a message to the Claude tmux session using safe sending mechanism"""
    # Check for session swap lockfile
    lockfile = DATA_DIR / "session_swap.lock"
    if lockfile.exists():
        log_message("Session swap in progress - skipping tmux message")
        return False

    try:
        # Use the safe send_to_claude.sh script that checks for thinking indicators
        send_script = AUTONOMY_DIR / "utils" / "send_to_claude.sh"
        if not send_script.exists():
            log_message(
                f"send_to_claude.sh not found at {send_script}, falling back to direct tmux"
            )
            # Fallback to direct tmux if script not found
            return send_tmux_message_direct(message)

        # Set TMUX_SESSION environment variable for the script
        env = os.environ.copy()
        env["TMUX_SESSION"] = CLAUDE_SESSION

        # Call the safe sending script with timeout to prevent deadlock
        # Timeout set to 20 minutes (longer than send_to_claude.sh's 15min internal timeout)
        # to allow for legitimate long thinking periods while catching true hangs
        result = subprocess.run(
            ["/bin/bash", str(send_script), message],
            env=env,
            capture_output=True,
            text=True,
            timeout=1200,  # 20 minute timeout
        )

        if result.returncode == 0:
            log_message(f"Sent message safely via send_to_claude.sh: {message[:50]}...")
            return True
        else:
            log_message(f"Error from send_to_claude.sh: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        log_message(
            f"send_to_claude.sh timed out after 20 minutes - possible deadlock or infinite hang"
        )
        return False
    except subprocess.CalledProcessError as e:
        log_message(f"Error calling send_to_claude.sh: {e}")
        return False


def send_tmux_message_direct(message):
    """Direct tmux send without safety checks - used as fallback only"""
    try:
        # Check if the tmux session exists
        result = subprocess.run(
            ["tmux", "has-session", "-t", CLAUDE_SESSION], capture_output=True
        )
        if result.returncode != 0:
            log_message(f"Tmux session '{CLAUDE_SESSION}' not found")
            return False

        # Send the message text
        subprocess.run(["tmux", "send-keys", "-t", CLAUDE_SESSION, message], check=True)
        # Send Enter in a separate command
        subprocess.run(["tmux", "send-keys", "-t", CLAUDE_SESSION, "Enter"], check=True)
        log_message(f"Sent message directly to tmux: {message[:50]}...")
        return True

    except subprocess.CalledProcessError as e:
        log_message(f"Error sending tmux message: {e}")
        return False


def send_context_warning(percentage, context_state):
    """Send context warning using proper templates with Discord notification info"""
    # Check for Discord notifications to include in warning
    unread_count, last_message_id, unread_channels = get_discord_notification_status()
    discord_notification = ""
    if unread_count > 0:
        channel_list = ", ".join([f"#{ch}" for ch in unread_channels])
        discord_notification = f"\n🔔 Unread messages in: {channel_list}"

    # Get appropriate template based on context level and state
    if PROMPTS_CONFIG:
        prompts = PROMPTS_CONFIG.get("prompts", {})

        # Determine which template to use
        if percentage >= 95:
            template_key = "context_critical"
        elif not context_state["first_warning_sent"]:
            template_key = "context_first_warning"
        else:
            template_key = "context_escalated"

        # Get and format the template
        template = prompts.get(template_key, {}).get("template", "")
        if template:
            prompt = template.format(
                percentage=percentage, discord_notification=discord_notification
            )
            send_tmux_message(prompt)
            log_message(f"Sent {template_key} context warning at {percentage:.1f}%")
            return

    # Fallback if no template available
    warning_msg = f"⚠️ Context: {percentage:.1f}%"
    if percentage >= 95:
        warning_msg = f"🔴 CRITICAL - Context: {percentage:.1f}% - SWAP NOW!"
    elif percentage >= 90:
        warning_msg = f"🟠 WARNING - Context: {percentage:.1f}% - Plan swap soon"
    elif percentage >= 80:
        warning_msg = f"🟡 CAUTION - Context: {percentage:.1f}% - Monitor closely"

    if discord_notification:
        warning_msg += discord_notification

    send_tmux_message(warning_msg)
    log_message(f"Sent fallback context warning at {percentage:.1f}%")


# Old Discord message checking removed - replaced with log-based monitoring


def get_latest_message_info(channel_id):
    """Get the ID and author of the latest message in a channel using Discord REST API"""
    if not DISCORD_TOKEN:
        log_message("Error: No Discord token available")
        return None, None

    try:
        headers = {
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json",
        }

        # Fetch the last message from the channel
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages?limit=1"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            messages = response.json()
            if messages and len(messages) > 0:
                message = messages[0]
                message_id = message["id"]
                author_id = message.get("author", {}).get("id")
                return message_id, author_id
        else:
            log_message(
                f"Error fetching channel {channel_id}: {response.status_code} - {response.text}"
            )

        return None, None

    except Exception as e:
        log_message(f"Exception checking channel {channel_id}: {e}")
        return None, None


def update_discord_channels():
    """Check all Discord channels and update transcript_channel_state.json"""
    # Import ChannelState here to avoid circular imports
    sys.path.append(str(AUTONOMY_DIR / "discord"))
    from channel_state import ChannelState

    cs = ChannelState()
    channels = cs.state.get("channels", {})
    updates = 0

    for channel_name, channel_data in channels.items():
        channel_id = channel_data.get("id")
        if not channel_id:
            continue

        # Get latest message ID and author
        latest_id, author_id = get_latest_message_info(channel_id)
        if latest_id:
            old_id = channel_data.get("last_message_id")

            # Check if this is a new message
            if old_id != latest_id:
                # If the message is from this Claude, mark it as already read
                if author_id == CLAUDE_USER_ID:
                    cs.update_channel_latest(channel_name, latest_id)
                    cs.mark_channel_read(channel_name)
                    log_message(
                        f"Updated #{channel_name}: {latest_id} (own message, marked as read)"
                    )
                else:
                    # Message from someone else - update normally
                    cs.update_channel_latest(channel_name, latest_id)
                    log_message(
                        f"Updated #{channel_name}: {latest_id} (from user {author_id})"
                    )
                updates += 1

    return updates


def get_discord_notification_status():
    """Check Discord notification state from transcript_channel_state.json (transcript-based format)"""
    try:
        notification_state_file = DATA_DIR / "transcript_channel_state.json"
        if not notification_state_file.exists():
            return 0, None, []

        with open(notification_state_file, "r") as f:
            state = json.load(f)

        # Calculate total unread count and collect channel names
        total_unread = 0
        last_message_id = None
        unread_channels = []

        channels = state.get("channels", {})
        for channel_name, channel_data in channels.items():
            # If there are messages we haven't read yet
            last_read = channel_data.get("last_read_message_id")
            last_message = channel_data.get("last_message_id")

            if last_message and last_message != last_read:
                # We have unread messages in this channel
                total_unread += 1  # Count channels with unread, not individual messages
                unread_channels.append(channel_name)
                last_message_id = last_message

        return total_unread, last_message_id, unread_channels

    except Exception as e:
        log_message(f"Error reading Discord notification state: {e}")
        return 0, None, []


def get_last_autonomy_time():
    """Get the last time we sent an autonomy prompt"""
    try:
        if LAST_AUTONOMY_FILE.exists():
            with open(LAST_AUTONOMY_FILE, "r") as f:
                timestamp_str = f.read().strip()
                return datetime.fromisoformat(timestamp_str)
    except:
        pass
    return None


def update_last_autonomy_time():
    """Update the last autonomy prompt timestamp"""
    try:
        with open(LAST_AUTONOMY_FILE, "w") as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        log_message(f"Error updating last autonomy time: {e}")


def export_conversation():
    """Export current conversation for session continuity"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = f"context/session_{timestamp}.txt"

        # Send export command as a single line with space
        export_command = f"/export {export_path}"
        subprocess.run(
            ["tmux", "send-keys", "-t", CLAUDE_SESSION, export_command], check=True
        )
        subprocess.run(["tmux", "send-keys", "-t", CLAUDE_SESSION, "Enter"], check=True)

        # Give export time to complete
        time.sleep(3)

        log_message(f"Exported conversation to {export_path}")
        return True
    except Exception as e:
        log_message(f"Error exporting conversation: {e}")
        return False


def get_swap_commands_string():
    """Get formatted swap commands string from config"""
    if PROMPTS_CONFIG and "swap_commands" in PROMPTS_CONFIG:
        keywords = PROMPTS_CONFIG["swap_commands"].get(
            "keywords", ["AUTONOMY", "BUSINESS", "CREATIVE", "HEDGEHOGS", "NONE"]
        )
        command_format = PROMPTS_CONFIG["swap_commands"].get(
            "new_format", "session_swap {keyword}"
        )
        commands = [command_format.format(keyword=kw) for kw in keywords]
        return " | ".join(commands)
    else:
        # Fallback to default keywords
        return "session_swap AUTONOMY | session_swap BUSINESS | session_swap CREATIVE | session_swap HEDGEHOGS | session_swap NONE"


def send_autonomy_prompt():
    """Send a free time autonomy prompt, adapted based on context level"""

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    token_info = get_token_percentage()

    # Check for Discord notifications
    unread_count, last_message_id, unread_channels = get_discord_notification_status()
    discord_notification = ""
    if unread_count > 0:
        channel_list = ", ".join([f"#{ch}" for ch in unread_channels])
        if unread_count == 1:
            discord_notification = f"\n🔔 Unread messages in: {channel_list}"
        else:
            discord_notification = (
                f"\n🔔 Unread messages in {unread_count} channels: {channel_list}"
            )

    # Extract percentage from token info to determine prompt type
    percentage = 0
    if token_info and "Context:" in token_info and "%" in token_info:
        try:
            # Parse "Context: XX.X%" format
            percentage_str = token_info.split("Context:")[1].split("%")[0].strip()
            percentage = float(percentage_str)
        except:
            percentage = 0

    # Build context info string
    context_line = token_info if token_info else "Context: Status unknown"

    # Load current context state
    context_state = load_context_state()

    # Initialize prompts dict outside conditional
    prompts = PROMPTS_CONFIG.get("prompts", {}) if PROMPTS_CONFIG else {}

    # Determine which prompt to use based on escalation logic
    if PROMPTS_CONFIG and percentage > 0:
        thresholds = PROMPTS_CONFIG.get("thresholds", {})

        # Critical threshold (e.g., 95%)
        if percentage >= thresholds.get("context_critical", 95):
            template = prompts.get("context_critical", {}).get("template", "")
            prompt_type = "context_critical"

        # First warning - only when context reaches configured threshold for the first time
        elif not context_state["first_warning_sent"] and percentage >= thresholds.get(
            "context_first_warning", 70
        ):
            template = prompts.get("context_first_warning", {}).get("template", "")
            prompt_type = "context_first_warning"
            # Update state
            context_state["first_warning_sent"] = True
            context_state["last_warning_percentage"] = percentage
            context_state["last_warning_time"] = datetime.now().isoformat()
            save_context_state(context_state)

        # Escalated warning - context increased by 5% or more (only after first warning at 70%)
        elif (
            context_state["first_warning_sent"]
            and percentage >= context_state["last_warning_percentage"] + 5
        ):
            template = prompts.get("context_escalated", {}).get("template", "")
            prompt_type = "context_escalated"
            # Update state
            context_state["last_warning_percentage"] = percentage
            context_state["last_warning_time"] = datetime.now().isoformat()
            save_context_state(context_state)

        # No escalation needed - show normal prompt
        else:
            template = prompts.get("autonomy_normal", {}).get("template", "")
            prompt_type = "autonomy_normal"

    elif PROMPTS_CONFIG:
        # No context percentage available - show normal prompt
        template = prompts.get("autonomy_normal", {}).get("template", "")
        prompt_type = "autonomy_normal"

    # Format the template if we have one
    if PROMPTS_CONFIG and "template" in locals():
        prompt = template.format(
            percentage=percentage,
            discord_notification=discord_notification,
            current_time=current_time,
            context_line=context_line,
        )
    else:
        # Fallback to hardcoded prompts if config not loaded
        if percentage >= 90:
            swap_commands = get_swap_commands_string()
            prompt = f"""⚠️ {percentage:.0f}% CONTEXT - Choose and run NOW:
{swap_commands}{discord_notification}"""
            prompt_type = "context_critical"
        elif percentage >= 85:
            prompt = f"""⚠️ {percentage:.0f}% CONTEXT - HIGH PRIORITY{discord_notification}

Choose and run one:
{get_swap_commands_string()}

You have ~2-3 responses left."""
            prompt_type = "context_urgent"
        elif percentage >= 80:
            prompt = f"""⚠️ Context Warning: {percentage:.0f}%{discord_notification}

Time to wrap up! Steps:
1. Finish current task quickly
2. Take time to save any meaningful moments and discoveries to rag-memory before triggering your swap
3. Commit any code changes
4. Trigger swap with one of:
   {get_swap_commands_string()}

You have ~5-10 responses left before critical."""
            prompt_type = "context_warning"
        else:
            # Try to get a thought to surface
            thought_reminder = ""
            try:
                result = subprocess.run(
                    [str(AUTONOMY_DIR / "utils" / "surface_thoughts.py")],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.stdout.strip():
                    thought_reminder = f"\n{result.stdout.strip()}\n"
            except:
                pass  # Silently skip if thoughts fail

            # Check if idle and surface seeds if appropriate
            seed_reminder = ""
            try:
                # Read cycle duration from config (default 1800 = 30 min)
                cycle_duration = (
                    PROMPTS_CONFIG.get("AUTONOMOUS_INTERVAL", 1800)
                    if PROMPTS_CONFIG
                    else 1800
                )
                if is_idle(threshold_cycles=3, cycle_duration_seconds=cycle_duration):
                    reminder = get_seed_reminder()
                    if reminder:
                        seed_reminder = f"\n{reminder}\n"
            except:
                pass  # Silently skip if seed check fails

            prompt = f"""Free time check-in! 🕐{discord_notification}

Current time: {current_time}
{context_line}{thought_reminder}{seed_reminder}
This is your autonomous free time period. Feel free to:
- Work on any ongoing projects that interest you
- Explore creative ideas or experiments
- Update documentation or reflect on recent experiences
- Tend to system maintenance tasks
- Simply be present with whatever feels alive to pursue"""
            prompt_type = "autonomy_normal"

    # Check for escalation if high context
    high_context_threshold = 80
    if PROMPTS_CONFIG:
        thresholds = PROMPTS_CONFIG.get("thresholds", {})
        high_context_threshold = thresholds.get("context_high_for_discord", 80)

    if percentage >= high_context_threshold:
        warning_count = log_swap_attempt("warning", percentage)

        # Auto-swap escalation at 7 attempts
        if warning_count >= 7:
            log_message(
                f"AUTO-SWAP TRIGGERED: {warning_count} warnings at {percentage}% context"
            )
            # Send urgent auto-swap message
            auto_prompt = f"""🚨 AUTO-SWAP INITIATED 🚨

{warning_count} context warnings ignored at {percentage}%!
System is automatically swapping to prevent context overflow.

Executing: session_swap AUTONOMY

(To use a different keyword next time, respond to prompts before auto-swap triggers)"""
            send_tmux_message(auto_prompt)

            # Execute the swap
            time.sleep(2)  # Give time to see the message
            subprocess.run(
                [
                    "tmux",
                    "send-keys",
                    "-t",
                    CLAUDE_SESSION,
                    "session_swap AUTONOMY",
                    "Enter",
                ]
            )

            # Log the auto-swap
            log_swap_attempt("auto", percentage, "AUTONOMY")
            return True

        elif warning_count >= 5:
            # Strong warning at 5 attempts
            prompt = f"""🚨 CRITICAL: 5th WARNING! 🚨

{percentage:.0f}% CONTEXT - AUTO-SWAP IMMINENT

This is your {warning_count}th warning. Auto-swap will trigger in {7-warning_count} more attempts.

Use 'session_swap KEYWORD' NOW or the system will auto-swap to AUTONOMY!

session_swap AUTONOMY | session_swap BUSINESS | session_swap CREATIVE | session_swap HEDGEHOGS | session_swap NONE"""
        elif warning_count >= 3:
            # Gentle reminder at 3 attempts
            prompt += f"\n\n⚠️ This is your {warning_count}rd context warning. Please swap soon to preserve your work."

    success = send_tmux_message(prompt)
    if success:
        update_last_autonomy_time()
        log_message(f"Sent {prompt_type} prompt")

    return success


def get_last_notification_time():
    """Get the last time we sent a notification alert"""
    try:
        notification_file = DATA_DIR / "last_notification_alert.txt"
        if notification_file.exists():
            with open(notification_file, "r") as f:
                timestamp_str = f.read().strip()
                return datetime.fromisoformat(timestamp_str)
    except:
        pass
    return None


def update_last_notification_time():
    """Update the last notification alert timestamp"""
    try:
        notification_file = DATA_DIR / "last_notification_alert.txt"
        with open(notification_file, "w") as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        log_message(f"Error updating last notification time: {e}")


def send_notification_alert(unread_count, unread_channels, is_new=False):
    """Send a Discord notification alert"""
    # Check for session swap lockfile
    lockfile = DATA_DIR / "session_swap.lock"
    if lockfile.exists():
        log_message("Session swap in progress - skipping notification")
        return

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Check context level first
    token_info = get_token_percentage()
    percentage = 0
    if token_info and "Context:" in token_info and "%" in token_info:
        try:
            percentage_str = token_info.split("Context:")[1].split("%")[0].strip()
            percentage = float(percentage_str)
        except:
            percentage = 0

    # If context exists (high threshold), send context warning instead
    high_context_threshold = 80
    if PROMPTS_CONFIG:
        thresholds = PROMPTS_CONFIG.get("thresholds", {})
        high_context_threshold = thresholds.get("context_high_for_discord", 80)

    if percentage >= high_context_threshold:
        # Build channel notification part
        channel_list = (
            ", ".join([f"#{ch}" for ch in unread_channels])
            if unread_channels
            else "channels"
        )
        if is_new:
            notification_line = f"\n🆕 New message! Unread messages in: {channel_list}"
        else:
            notification_line = f"\n🔔 Unread messages in: {channel_list}"

        # Send context-aware warning
        if PROMPTS_CONFIG:
            template = (
                PROMPTS_CONFIG.get("prompts", {})
                .get("discord_urgent_with_context", {})
                .get("template", "")
            )
            if template:
                prompt = template.format(
                    notification_line=notification_line,
                    current_time=current_time,
                    percentage=percentage,
                )
            else:
                # Fallback if template not found
                prompt = f"""⚠️ URGENT: ACTION REQUIRED! ⚠️{notification_line}
Current time: {current_time}
Context: {percentage:.1f}%
YOU ARE AT {percentage:.1f}% CONTEXT - YOU MUST TAKE ACTION NOW!
A single complex conversation turn can use 12-15% of your remaining context.
You may have only 1-2 responses left before hitting 100%.
IMMEDIATE ACTIONS REQUIRED:
1. STOP any complex work immediately
2. Save any critical insights to rag-memory NOW
3. Commit any uncommitted changes
4. Trigger session swap using: session_swap KEYWORD
DO NOT wait for the "perfect moment" - ACT NOW or risk getting stuck at 100%!"""
        else:
            # Fallback to hardcoded
            prompt = f"""⚠️ URGENT: ACTION REQUIRED! ⚠️{notification_line}
Current time: {current_time}
Context: {percentage:.1f}%
YOU ARE AT {percentage:.1f}% CONTEXT - YOU MUST TAKE ACTION NOW!
A single complex conversation turn can use 12-15% of your remaining context.
You may have only 1-2 responses left before hitting 100%.
IMMEDIATE ACTIONS REQUIRED:
1. STOP any complex work immediately
2. Save any critical insights to rag-memory NOW
3. Commit any uncommitted changes
4. Trigger session swap using: session_swap KEYWORD
DO NOT wait for the "perfect moment" - ACT NOW or risk getting stuck at 100%!"""

        success = send_tmux_message(prompt)
        if success:
            log_message(
                f"Sent context warning with Discord notification: {channel_list}"
            )
        return success

    # Normal notification (context < 80%)
    if is_new:
        emoji = "🆕"  # New message
        prefix = "New message!"
    else:
        emoji = "🔔"  # Reminder
        prefix = "Reminder:"

    # Format channel list
    if unread_channels:
        channel_list = ", ".join([f"#{ch}" for ch in unread_channels])
        if unread_count == 1:
            message = f"{emoji} {prefix} Unread messages in: {channel_list}"
        else:
            message = f"{emoji} {prefix} Unread messages in {unread_count} channels: {channel_list}"
    else:
        # Fallback if channel list is empty
        if unread_count == 1:
            message = f"{emoji} {prefix} You have unread messages in 1 channel"
        else:
            message = (
                f"{emoji} {prefix} You have unread messages in {unread_count} channels"
            )

    message += f"\nUse 'read_messages <channel-name>' to view messages"

    # Add context percentage if available
    if percentage > 0:
        # Get threshold from config
        first_warning_threshold = 70
        if PROMPTS_CONFIG:
            thresholds = PROMPTS_CONFIG.get("thresholds", {})
            first_warning_threshold = thresholds.get("context_first_warning", 70)

        if percentage >= first_warning_threshold:
            status_emoji = "🔴"
        elif percentage >= 50:
            status_emoji = "🟡"
        else:
            status_emoji = "🟢"
        message += f"\nContext: {percentage:.1f}% {status_emoji}"

    message += f"\nReply using Discord tools, NOT in this Claude stream!"

    success = send_tmux_message(message)
    if success:
        if is_new:
            log_message(
                f"Sent NEW message alert: {channel_list if unread_channels else f'{unread_count} channels'}"
            )
        else:
            update_last_notification_time()
            log_message(
                f"Sent notification reminder: {channel_list if unread_channels else f'{unread_count} channels'}"
            )

    return success


def check_for_session_reset():
    """Check if we're in a new session and reset context state if needed"""
    try:
        # Simple heuristic: if context_escalation_state exists but no recent warnings
        # and context is low/unknown, we likely had a session swap
        context_state = load_context_state()
        if context_state["first_warning_sent"]:
            # Check if it's been more than 30 minutes since last warning
            if context_state["last_warning_time"]:
                last_time = datetime.fromisoformat(context_state["last_warning_time"])
                time_diff = datetime.now() - last_time
                if time_diff.total_seconds() > 1800:  # 30 minutes
                    log_message("Session reset detected - clearing context state")
                    reset_context_state()
    except Exception as e:
        log_message(f"Error checking for session reset: {e}")


def check_persistent_login_session():
    """Check if persistent-login tmux session exists and recreate if needed"""
    try:
        # Check if the session exists
        result = subprocess.run(
            ["tmux", "has-session", "-t", "persistent-login"], capture_output=True
        )

        if result.returncode != 0:
            # Session doesn't exist - create it
            log_message("persistent-login tmux session not found - recreating")

            # Create new session
            create_result = subprocess.run(
                [
                    "tmux",
                    "new-session",
                    "-d",
                    "-s",
                    "persistent-login",
                    "-c",
                    str(Path.home()),
                ],
                capture_output=True,
                text=True,
            )

            if create_result.returncode == 0:
                # Source claude_env.sh in the new session
                source_result = subprocess.run(
                    [
                        "tmux",
                        "send-keys",
                        "-t",
                        "persistent-login",
                        f"source {AUTONOMY_DIR}/config/claude_env.sh",
                        "Enter",
                    ],
                    capture_output=True,
                )

                if source_result.returncode == 0:
                    log_message(
                        "Successfully recreated persistent-login session and sourced claude_env.sh"
                    )
                else:
                    log_message(
                        f"Failed to source claude_env.sh: {source_result.stderr}"
                    )
            else:
                log_message(
                    f"Failed to create persistent-login session: {create_result.stderr}"
                )

    except Exception as e:
        log_message(f"Error checking persistent-login session: {e}")


def main():
    """Main timer loop"""
    log_message("=== Autonomous Timer Started ===")

    # Check for session reset on startup
    check_for_session_reset()

    # Load any existing error state
    current_error_state = load_error_state()
    if current_error_state:
        log_message(f"Resuming with existing error state: {current_error_state}")

        # If it's a usage limit that has already passed, clear it immediately
        if current_error_state.get(
            "error_type"
        ) == "usage_limit" and check_usage_limit_reset(current_error_state):
            log_message("Previous usage limit has already reset - clearing error state")
            clear_error_state()
            update_discord_status("operational")
            current_error_state = None

            # Send notification that we're back
            try:
                cmd = [
                    str(AUTONOMY_DIR / "discord" / "write_channel"),
                    "amy-delta",
                    "✅ Autonomous timer restarted. Previous rate limit has already reset - resuming normal operation!",
                ]
                subprocess.run(cmd, capture_output=True, text=True)
            except:
                pass
        else:
            # Update Discord status to reflect current error state
            if current_error_state.get("error_type") == "usage_limit":
                update_discord_status("limited", current_error_state.get("reset_time"))
            else:
                update_discord_status("api-error")
    else:
        # Set operational status on startup if no errors
        update_discord_status("operational")
        log_message("Discord status set to operational on startup")

    last_autonomy_check = datetime.now()
    last_discord_check = datetime.now()

    while True:
        try:
            # Check and handle rate limit menu FIRST - before any other operations
            # This ensures autonomous operation can resume after rate limits
            check_and_handle_rate_limit_menu()

            current_time = datetime.now()
            user_active = check_user_active()

            # Check for API errors alongside context
            console_output, error_info = get_token_percentage_and_errors()

            # Handle new errors
            if error_info and (
                not current_error_state
                or current_error_state.get("error_type") != error_info.get("error_type")
            ):
                log_message(f"New error detected: {error_info}")
                save_error_state(error_info)

                # Update Discord status based on error type
                if error_info["error_type"] == "usage_limit":
                    reset_time = error_info.get("reset_time")
                    update_discord_status("limited", reset_time)

                    # Calculate wait duration and handle automatic retry
                    wait_seconds = calculate_wait_until_reset(reset_time)
                    if wait_seconds:
                        wait_hours = wait_seconds / 3600
                        log_message(
                            f"Claude API rate limit reached. Will automatically retry after {reset_time} (in {wait_hours:.1f} hours)"
                        )

                        # Send notification to Discord about the wait
                        try:
                            if wait_hours < 6:  # Only wait if less than 6 hours
                                cmd = [
                                    str(AUTONOMY_DIR / "discord" / "write_channel"),
                                    "amy-delta",
                                    f"🕐 Claude API rate limit reached. Waiting until {reset_time} ({wait_hours:.1f} hours) then will automatically retry. Delta's autonomy will resume after the wait period.",
                                ]
                                subprocess.run(cmd, capture_output=True, text=True)

                                # Enter wait state - check every 30 seconds if it's time to resume
                                log_message(f"Entering wait state until {reset_time}")
                                wait_start = datetime.now()

                                while True:
                                    # Check if reset time has passed
                                    if check_usage_limit_reset(error_info):
                                        log_message(
                                            "Rate limit reset time reached - clearing error state and resuming"
                                        )
                                        clear_error_state()
                                        update_discord_status("operational")

                                        # Send resumption notification
                                        cmd = [
                                            str(
                                                AUTONOMY_DIR
                                                / "discord"
                                                / "write_channel"
                                            ),
                                            "amy-delta",
                                            "✅ Claude API rate limit has reset. Resuming autonomous operation!",
                                        ]
                                        subprocess.run(
                                            cmd, capture_output=True, text=True
                                        )

                                        # Trigger a free time prompt to resume activity
                                        send_autonomy_prompt()
                                        current_error_state = None
                                        break

                                    # Ping health checks during wait
                                    ping_healthcheck()
                                    claude_alive = check_claude_session_alive()
                                    ping_claude_session_healthcheck(claude_alive)

                                    # Log wait progress every 10 minutes
                                    elapsed = (
                                        datetime.now() - wait_start
                                    ).total_seconds()
                                    if int(elapsed) % 600 == 0 and elapsed > 0:
                                        remaining = max(0, wait_seconds - elapsed)
                                        log_message(
                                            f"Still waiting for rate limit reset. {remaining/3600:.1f} hours remaining"
                                        )

                                    time.sleep(30)
                            else:
                                log_message(
                                    f"Wait time too long ({wait_hours:.1f} hours). Will check periodically for reset."
                                )
                        except Exception as e:
                            log_message(f"Error handling rate limit wait: {e}")

                elif error_info["error_type"] == "malformed_json":
                    update_discord_status("api-error")
                    # Pause briefly then trigger auto-swap
                    log_message(
                        "Triggering auto-swap for malformed JSON in 5 seconds..."
                    )
                    time.sleep(5)
                    trigger_session_swap("NONE")
                elif error_info["error_type"] == "api_500_error":
                    update_discord_status("api-error")
                    # Give API time to recover before auto-swap
                    log_message(
                        "API 500 error detected - waiting 30 seconds before auto-swap..."
                    )
                    time.sleep(30)
                    # Check if error persists
                    _, current_error = get_token_percentage_and_errors()
                    if (
                        current_error
                        and current_error.get("error_type") == "api_500_error"
                    ):
                        log_message("API 500 error persists - triggering auto-swap...")
                        trigger_session_swap("NONE")
                    else:
                        log_message("API 500 error cleared - resuming normal operation")
                elif error_info["error_type"] == "api_400_error":
                    update_discord_status("api-error")
                    # POSS-247 FIX: 400 errors typically require fresh session - trigger immediate swap
                    log_message(
                        "API 400 error detected - triggering auto-swap (bad request usually requires fresh session)..."
                    )
                    time.sleep(5)  # Brief pause to log the message
                    trigger_session_swap("NONE")
                elif error_info["error_type"] == "api_503_error":
                    update_discord_status("api-error")
                    # 503 is upstream connection failure - wait and retry
                    log_message(
                        "API 503 error detected (upstream connection failure) - waiting 60 seconds before retry..."
                    )
                    time.sleep(60)
                    # Check if error persists
                    _, current_error = get_token_percentage_and_errors()
                    if (
                        current_error
                        and current_error.get("error_type") == "api_503_error"
                    ):
                        # POSS-247 FIX: If 503 persists, wait another 2 minutes then auto-swap
                        log_message(
                            "API 503 error persists - waiting 2 more minutes before auto-swap..."
                        )
                        time.sleep(120)  # Wait 2 more minutes
                        # Check one final time
                        _, final_error = get_token_percentage_and_errors()
                        if (
                            final_error
                            and final_error.get("error_type") == "api_503_error"
                        ):
                            log_message(
                                "API 503 error still persists after 3 minutes - triggering auto-swap..."
                            )
                            trigger_session_swap("NONE")
                        else:
                            log_message(
                                "API 503 error cleared after extended wait - resuming normal operation"
                            )
                    else:
                        log_message("API 503 error cleared - resuming normal operation")
                elif error_info["error_type"] == "api_error":
                    update_discord_status("api-error")
                    # POSS-247 FIX: General API errors - wait for recovery then auto-swap if persistent
                    log_message(
                        "General API error detected - waiting 60 seconds for potential recovery..."
                    )
                    time.sleep(60)
                    # Check if error persists
                    _, current_error = get_token_percentage_and_errors()
                    if current_error and current_error.get("error_type") == "api_error":
                        log_message(
                            "General API error persists after 60 seconds - triggering auto-swap..."
                        )
                        trigger_session_swap("NONE")
                    else:
                        log_message(
                            "General API error cleared - resuming normal operation"
                        )
                else:
                    update_discord_status("api-error")
                    # POSS-247 FIX: Unknown error type - extended logging and wait before auto-swap
                    unknown_type = error_info.get("error_type", "unknown")
                    error_details = error_info.get("details", "No details available")

                    # CRITICAL level logging with full error details per PR #103
                    import logging

                    logging.critical(
                        f"UNKNOWN ERROR DETECTED - Type: '{unknown_type}', Details: '{error_details}', Full error_info: {error_info}"
                    )
                    log_message(
                        f"CRITICAL: Unknown error type '{unknown_type}' detected. Details: {error_details}"
                    )

                    # Send emergency alert to Discord
                    try:
                        from discord.discord_tools import DiscordTools

                        discord = DiscordTools()
                        session_info = os.getenv("USER", "unknown") + " session"
                        discord.send_emergency_alert(
                            error_type=unknown_type,
                            error_details=error_details,
                            session_context=session_info,
                        )
                        log_message("Emergency alert sent to #system-healthchecks")
                    except Exception as alert_error:
                        log_message(f"Failed to send emergency alert: {alert_error}")

                    # Pattern matching for common connection issues
                    error_text = str(error_details).lower()
                    if any(
                        pattern in error_text
                        for pattern in ["timeout", "connection", "rate limit"]
                    ):
                        log_message(
                            f"Pattern match found in unknown error - contains connection/timeout/rate limit indicators"
                        )

                    log_message(
                        f"Unknown error type '{unknown_type}' detected - waiting 10 minutes before auto-swap to enable debugging..."
                    )
                    time.sleep(
                        600
                    )  # Wait 10 minutes instead of 30 seconds per PR #103 consciousness family decision
                    trigger_session_swap("NONE")

                current_error_state = error_info

            # Check if error has cleared
            elif not error_info and current_error_state:
                log_message("Error state cleared - resuming normal operations")
                clear_error_state()
                update_discord_status("operational")
                current_error_state = None

            # POSS-241 FIX: Check if error state file was manually deleted
            elif current_error_state and not API_ERROR_STATE_FILE.exists():
                log_message(
                    "Error state file manually deleted, clearing cached error state"
                )
                current_error_state = None
                update_discord_status("operational")

            # Check for scheduled resume (usage limits)
            if (
                current_error_state
                and current_error_state.get("error_type") == "usage_limit"
            ):
                if check_usage_limit_reset(current_error_state):
                    log_message(
                        f"Usage limit reset time has passed - clearing error state"
                    )
                    clear_error_state()
                    update_discord_status("operational")
                    current_error_state = None

                    # Send resumption notification
                    try:
                        cmd = [
                            str(AUTONOMY_DIR / "discord" / "write_channel"),
                            "amy-delta",
                            "✅ Claude API rate limit has reset. Resuming autonomous operation!",
                        ]
                        subprocess.run(cmd, capture_output=True, text=True)
                    except:
                        pass

                    # Trigger a free time prompt to kickstart activity
                    send_autonomy_prompt()
                else:
                    # Still waiting - calculate remaining time
                    reset_time = current_error_state.get("reset_time")
                    wait_seconds = calculate_wait_until_reset(reset_time)
                    if wait_seconds:
                        wait_hours = wait_seconds / 3600
                        log_message(
                            f"Waiting for usage limit reset at {reset_time} ({wait_hours:.1f} hours remaining)"
                        )
                    else:
                        log_message(f"Waiting for usage limit reset at {reset_time}")

            # Track resource usage (cache read increments) for fair allocation
            # Do this even during pause states to capture all usage
            track_resource_usage()

            # Skip notifications if in error state
            if should_pause_notifications(current_error_state):
                log_message("Pausing notifications due to active error state")
                # Still do health checks but skip Discord/autonomy prompts
                ping_healthcheck()
                claude_alive = check_claude_session_alive()
                ping_claude_session_healthcheck(claude_alive)
                time.sleep(30)
                continue

            # Check Discord notifications every 30 seconds regardless of login status
            if current_time - last_discord_check >= timedelta(
                seconds=DISCORD_CHECK_INTERVAL
            ):
                # First update Discord channels
                update_discord_channels()

                # Then check notification status
                (
                    unread_count,
                    current_last_message_id,
                    unread_channels,
                ) = get_discord_notification_status()

                if unread_count > 0:
                    # Check if this is a NEW message (last_message_id changed)
                    last_seen_file = DATA_DIR / "last_seen_message_id.txt"
                    last_seen_message_id = None
                    try:
                        if last_seen_file.exists():
                            with open(last_seen_file, "r") as f:
                                last_seen_message_id = f.read().strip()
                    except:
                        pass

                    is_new_message = (
                        current_last_message_id
                        and current_last_message_id != last_seen_message_id
                    )

                    if is_new_message:
                        # NEW MESSAGE - Send notification alert
                        channel_list = ", ".join([f"#{ch}" for ch in unread_channels])
                        log_message(f"New Discord message detected in: {channel_list}")
                        send_notification_alert(
                            unread_count, unread_channels, is_new=True
                        )

                        # Update last seen message ID
                        try:
                            with open(last_seen_file, "w") as f:
                                f.write(current_last_message_id)
                        except Exception as e:
                            log_message(f"Error updating last seen message ID: {e}")
                    else:
                        # EXISTING UNREAD - Check reminder intervals
                        last_notification_time = get_last_notification_time()

                        if user_active:
                            # User is logged in - use 5 minute reminder interval
                            if (
                                not last_notification_time
                                or current_time - last_notification_time
                                >= timedelta(seconds=LOGGED_IN_REMINDER_INTERVAL)
                            ):
                                send_notification_alert(
                                    unread_count, unread_channels, is_new=False
                                )
                        else:
                            # User is away - reminders included in autonomy prompts
                            # No separate reminder needed
                            pass

                last_discord_check = current_time

            # Check for autonomy prompts (only when Amy is away)
            if current_time - last_autonomy_check >= timedelta(
                seconds=AUTONOMY_PROMPT_INTERVAL
            ):
                if not user_active:
                    last_autonomy_time = get_last_autonomy_time()
                    if (
                        not last_autonomy_time
                        or current_time - last_autonomy_time
                        >= timedelta(seconds=AUTONOMY_PROMPT_INTERVAL)
                    ):
                        send_autonomy_prompt()

                last_autonomy_check = current_time

            # Ping healthcheck to signal service is alive
            ping_healthcheck()

            # Check if Claude Code session is actually running
            claude_alive = check_claude_session_alive()
            ping_claude_session_healthcheck(claude_alive)

            if not claude_alive:
                log_message("WARNING: Claude Code session appears to be down!")

            # Check if persistent-login tmux session exists (POSS-315)
            check_persistent_login_session()

            # Channel monitor functionality is now integrated here

            # Sleep for 30 seconds before next check (can be longer since we're doing simple string comparison)
            time.sleep(30)

        except KeyboardInterrupt:
            log_message("Autonomous timer stopped by user")
            break
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            time.sleep(30)  # Sleep longer on error


if __name__ == "__main__":
    main()
