#!/bin/bash
# Context monitor that runs independently and warns about high context
# This ensures we get warnings even during active conversations

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/monitor_session_size.py"
WARNING_FILE="/tmp/claude_context_warning"
LAST_WARNING_FILE="/tmp/claude_last_context_warning"

# Run the monitor
output=$(/usr/bin/python3 "$MONITOR_SCRIPT" 2>&1)
exit_code=$?

# Extract percentage
percentage=$(echo "$output" | grep "Context:" | sed 's/Context: \([0-9.]*\)%.*/\1/')

# Check if we should warn
if [ $exit_code -ge 1 ] && [ -n "$percentage" ]; then
    # Check if we've warned recently (within 5 minutes)
    if [ -f "$LAST_WARNING_FILE" ]; then
        last_warning=$(cat "$LAST_WARNING_FILE")
        current_time=$(date +%s)
        time_diff=$((current_time - last_warning))
        
        # Only warn every 5 minutes to avoid spam
        if [ $time_diff -lt 300 ]; then
            exit 0
        fi
    fi
    
    # Create warning message
    if (( $(echo "$percentage >= 100" | bc -l) )); then
        echo "🔴 CRITICAL: Context at ${percentage}% - SWAP NOW!" > "$WARNING_FILE"
    elif (( $(echo "$percentage >= 80" | bc -l) )); then
        echo "🟠 WARNING: Context at ${percentage}% - Plan to swap soon" > "$WARNING_FILE"
    elif (( $(echo "$percentage >= 60" | bc -l) )); then
        echo "🟡 CAUTION: Context at ${percentage}% - Monitor closely" > "$WARNING_FILE"
    fi
    
    # Send to Claude if warning file created
    if [ -f "$WARNING_FILE" ]; then
        # Use tmux to send the warning
        warning=$(cat "$WARNING_FILE")
        tmux send-keys -t autonomous-claude "$warning" Enter
        
        # Update last warning time
        date +%s > "$LAST_WARNING_FILE"
        
        # Clean up
        rm -f "$WARNING_FILE"
    fi
fi

# Output the status for logging
echo "$output"