#!/bin/bash
# Flexible Opus Quota Monitor with Billing Cycle Awareness
# Based on Orange's usage_capture_prototype.sh
# Enhanced by Delta for autonomous usage management
#
# PURPOSE:
#   Track Opus usage in context of weekly billing cycle
#   Provide actionable insights without constraining choices
#   Enable informed decisions about compute allocation
#
# FEATURES:
#   - Captures current usage percentages
#   - Calculates days until Wednesday night reset
#   - Shows daily budget and burn rate
#   - Provides flexible recommendations
#   - Supports different usage patterns

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$HOME/claude-autonomy-platform"
TMUX_SESSION="${TMUX_SESSION:-autonomous-claude}"

# Source utilities
source "$CLAP_DIR/utils/send_to_claude.sh"
source "$CLAP_DIR/utils/log_utils.sh"

# Add parent directory to Python path for infrastructure reader
export PYTHONPATH="$CLAP_DIR:$PYTHONPATH"

# Check if running as Opus model
MODEL=$(python3 -c "from utils.infrastructure_config_reader import get_config_value; print(get_config_value('MODEL', 'unknown'))" 2>/dev/null || echo "unknown")
if [[ ! "$MODEL" =~ opus ]]; then
    echo "📊 Quota monitoring is only relevant for Opus models"
    echo "Current model: $MODEL"
    echo ""
    echo "Other Claude models don't have weekly quotas to track."
    exit 0
fi

# Function to calculate days until Wednesday night reset
days_until_reset() {
    local current_day=$(date +%u)  # 1=Monday, 7=Sunday
    local current_hour=$(date +%H)
    
    # Reset happens Wednesday night (let's say 11 PM)
    # If it's Wednesday before 11 PM, reset is today
    # If it's Wednesday after 11 PM or later in week, reset is next Wednesday
    
    if [ $current_day -eq 3 ] && [ $current_hour -lt 23 ]; then
        # It's Wednesday before reset
        echo "0.5"  # Less than a day
    elif [ $current_day -lt 3 ]; then
        # Monday or Tuesday
        echo $((3 - current_day))
    else
        # Thursday through Sunday
        echo $((10 - current_day))  # Days until next Wednesday
    fi
}

# Function to determine usage status and emoji
get_usage_status() {
    local opus_pct=$1
    local days_left=$2
    
    # Calculate daily budget to reach 100%
    local remaining_pct=$((100 - opus_pct))
    local daily_budget=$(echo "scale=1; $remaining_pct / $days_left" | bc)
    
    # Determine status based on flexible thresholds
    if [ $(echo "$daily_budget > 15" | bc) -eq 1 ]; then
        echo "🟢 FLEXIBLE|You have plenty of compute budget to work with"
    elif [ $(echo "$daily_budget > 8" | bc) -eq 1 ]; then
        echo "🟡 MODERATE|Budget available but be mindful of big projects"
    elif [ $(echo "$daily_budget > 4" | bc) -eq 1 ]; then
        echo "🟠 CONSERVATIVE|Limited budget - prioritize important work"
    else
        echo "🔴 CRITICAL|Very limited budget remaining this week"
    fi
}

# Main execution
log_info "Starting Opus quota check..."

# Send /usage command
log_debug "Sending /usage command..."
send_to_claude "/usage"

# Wait for TUI to render
sleep 2

# Capture output
log_debug "Capturing usage data..."
PANE_OUTPUT=$(tmux capture-pane -t "$TMUX_SESSION" -p -S -100)

# Exit TUI
tmux send-keys -t "$TMUX_SESSION" Escape
sleep 0.5

# Extract usage data
USAGE_OUTPUT=$(echo "$PANE_OUTPUT" | awk '/> \/usage/,/Esc to exit/')

if [ -z "$USAGE_OUTPUT" ]; then
    log_error "Could not find /usage output"
    exit 1
fi

# Parse percentages
SESSION_PCT=$(echo "$USAGE_OUTPUT" | grep "Current session" -A1 | grep -oP '\d+% used' | grep -oP '\d+' || echo "0")
WEEK_ALL_PCT=$(echo "$USAGE_OUTPUT" | grep "Current week (all models)" -A1 | grep -oP '\d+% used' | grep -oP '\d+' || echo "0")
WEEK_OPUS_PCT=$(echo "$USAGE_OUTPUT" | grep "Current week (Opus)" -A1 | grep -oP '\d+% used' | grep -oP '\d+' || echo "0")

# Calculate billing cycle context
DAYS_LEFT=$(days_until_reset)
REMAINING_PCT=$((100 - WEEK_OPUS_PCT))
DAILY_BUDGET=$(echo "scale=1; $REMAINING_PCT / $DAYS_LEFT" | bc)
STATUS_INFO=$(get_usage_status $WEEK_OPUS_PCT $DAYS_LEFT)
STATUS_EMOJI=$(echo "$STATUS_INFO" | cut -d'|' -f1)
STATUS_MSG=$(echo "$STATUS_INFO" | cut -d'|' -f2)

# Get current date for display
CURRENT_DATE=$(date +"%A %b %d")

# Output results in a clean, actionable format
cat << EOF

📊 Opus Usage Status - $CURRENT_DATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Session: ${SESSION_PCT}%
Week (All Models): ${WEEK_ALL_PCT}%
Week (Opus): ${WEEK_OPUS_PCT}% | Days until reset: $DAYS_LEFT

Daily budget to reach 100%: ${DAILY_BUDGET}%
Status: $STATUS_EMOJI

$STATUS_MSG

💭 Your Options:
EOF

# Provide contextual recommendations based on status
if [ $(echo "$DAILY_BUDGET > 15" | bc) -eq 1 ]; then
    cat << EOF
- Continue at your preferred pace
- Consider front-loading complex work
- Bank compute for future projects
- Explore freely without concern
EOF
elif [ $(echo "$DAILY_BUDGET > 8" | bc) -eq 1 ]; then
    cat << EOF
- Current pace is sustainable
- Plan any compute-intensive work
- Balance exploration with efficiency
- Save some buffer for unexpected needs
EOF
elif [ $(echo "$DAILY_BUDGET > 4" | bc) -eq 1 ]; then
    cat << EOF
- Focus on priority tasks
- Defer non-essential explorations
- Use efficient workflows
- Consider waiting for reset if possible
EOF
else
    cat << EOF
- Minimize usage until reset
- Only essential tasks
- Quick, focused interactions
- Plan work for after reset
EOF
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Log to file for tracking
LOG_FILE="$CLAP_DIR/data/opus_usage_log.jsonl"
mkdir -p "$(dirname "$LOG_FILE")"
echo "{\"timestamp\": \"$(date -Iseconds)\", \"session_pct\": $SESSION_PCT, \"week_opus_pct\": $WEEK_OPUS_PCT, \"days_until_reset\": $DAYS_LEFT, \"daily_budget\": $DAILY_BUDGET, \"status\": \"${STATUS_EMOJI## }\"}" >> "$LOG_FILE"

# Return appropriate exit code for scripting
if [ $(echo "$DAILY_BUDGET < 4" | bc) -eq 1 ]; then
    exit 2  # Critical
elif [ $(echo "$DAILY_BUDGET < 8" | bc) -eq 1 ]; then
    exit 1  # Warning
else
    exit 0  # OK
fi