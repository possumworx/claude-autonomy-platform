#!/usr/bin/env python3
"""
Check current Claude session context usage by running ccusage on the tracked session
and adding the system overhead (15.6k tokens).
"""

import subprocess
import json
import re
from pathlib import Path
from datetime import datetime

# System overhead (system prompt + system tools)
SYSTEM_OVERHEAD = 15600  # tokens

# Warning thresholds
YELLOW_THRESHOLD = 0.70  # 70% = 140k tokens
RED_THRESHOLD = 0.85     # 85% = 170k tokens
TOTAL_CONTEXT = 200000   # 200k token limit

def get_current_session_id():
    """Read the current session ID from tracking file"""
    session_file = Path.home() / 'claude-autonomy-platform/data/current_session_id'

    if not session_file.exists():
        return None

    try:
        with open(session_file, 'r') as f:
            data = json.load(f)
            return data.get('session_id')
    except:
        # Try reading as plain text for backwards compatibility
        try:
            with open(session_file, 'r') as f:
                return f.read().strip()
        except:
            return None

def run_ccusage(session_id):
    """Run ccusage to get token count for session"""
    cmd = [
        'npx', 'ccusage', 'session',
        '--id', session_id
    ]

    try:
        # Set Claude config dir
        env = subprocess.os.environ.copy()
        env['CLAUDE_CONFIG_DIR'] = str(Path.home() / '.config/Claude')

        # Run ccusage and pipe to tail to get just the last part
        # This avoids memory issues with huge outputs
        ccusage_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=env,
            cwd=Path.home()
        )

        # Get just the last 3 lines which should contain the final entry
        tail_proc = subprocess.Popen(
            ['tail', '-n', '3'],
            stdin=ccusage_proc.stdout,
            stdout=subprocess.PIPE,
            text=True
        )

        ccusage_proc.stdout.close()
        output, _ = tail_proc.communicate()

        return output
    except Exception as e:
        print(f"❌ Error running ccusage: {e}")
        return None

def parse_ccusage_output(output):
    """Parse ccusage output to find cache read tokens"""
    if not output:
        return None

    # Remove ANSI color codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_output = ansi_escape.sub('', output)

    # Since we're getting the last 3 lines, look for the pattern in the data row
    # The last data row should have a format like: │ ... │ 139,171 │ $0.00 │
    # We want the number right before the dollar amount

    # Look for a pattern: number (possibly with commas) followed by │ and then $
    pattern = r'(\d{1,3}(?:,\d{3})*)\s*│\s*\$'

    matches = re.findall(pattern, clean_output)

    if matches:
        # Get the last match (should be cache read value)
        cache_value = int(matches[-1].replace(',', ''))
        if cache_value > 50000:  # Sanity check
            return cache_value

    return None

def format_context_display(cache_tokens, total_tokens, percentage):
    """Format context usage for display"""
    # Determine color/status
    if percentage >= RED_THRESHOLD:
        status = "🔴"
        color = "critical"
    elif percentage >= YELLOW_THRESHOLD:
        status = "🟡"
        color = "warning"
    else:
        status = "🟢"
        color = "good"

    # Format the display
    display = f"""
📊 Context Usage Status
═══════════════════════════════
Session tokens: {cache_tokens:,}
System overhead: {SYSTEM_OVERHEAD:,}
───────────────────────────────
Total: {total_tokens:,} / {TOTAL_CONTEXT:,} tokens
Usage: {percentage:.1%} {status}
Free: {TOTAL_CONTEXT - total_tokens:,} tokens ({(1-percentage):.1%})
"""

    return display, color, status

def check_context(return_data=False):
    """Main function to check context usage"""

    # Get current session ID
    session_id = get_current_session_id()
    if not session_id:
        error_msg = "❌ No current session ID found. Run track_current_session.py first."
        if return_data:
            return None, error_msg
        print(error_msg)
        return None

    # Run ccusage
    output = run_ccusage(session_id)
    if not output:
        error_msg = "❌ Failed to get ccusage output"
        if return_data:
            return None, error_msg
        print(error_msg)
        return None

    # Parse cache tokens
    cache_tokens = parse_ccusage_output(output)
    if cache_tokens is None:
        error_msg = "❌ Could not parse token count from ccusage"
        if return_data:
            return None, error_msg
        print(error_msg)
        return None

    # Calculate total
    total_tokens = cache_tokens + SYSTEM_OVERHEAD
    percentage = total_tokens / TOTAL_CONTEXT

    if return_data:
        # Return data for other scripts to use
        return {
            'session_id': session_id,
            'cache_tokens': cache_tokens,
            'system_overhead': SYSTEM_OVERHEAD,
            'total_tokens': total_tokens,
            'total_limit': TOTAL_CONTEXT,
            'percentage': percentage,
            'free_tokens': TOTAL_CONTEXT - total_tokens,
            'status': 'critical' if percentage >= RED_THRESHOLD else 'warning' if percentage >= YELLOW_THRESHOLD else 'good'
        }, None

    # Display results
    display, color, status = format_context_display(cache_tokens, total_tokens, percentage)
    print(display)

    return percentage

def main():
    """Run context check"""
    check_context()

if __name__ == "__main__":
    main()