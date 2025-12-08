#!/bin/bash
# Manual usage tracking system
# Run /usage in Claude Code and record the results here

USAGE_LOG="$HOME/claude-autonomy-platform/data/usage_log.json"
USAGE_DIR="$(dirname "$USAGE_LOG")"

# Create data directory if it doesn't exist
mkdir -p "$USAGE_DIR"

# Function to add usage entry
log_usage() {
    local session_pct="$1"
    local week_pct="$2"
    local sonnet_pct="${3:-}"  # Optional Sonnet percentage
    local reset_time="${4:-}"   # Optional reset time
    local timestamp=$(date -u +%s)
    local date_str=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

    # Create or append to log
    if [ ! -f "$USAGE_LOG" ]; then
        echo "[]" > "$USAGE_LOG"
    fi

    # Add new entry
    jq --arg ts "$timestamp" \
       --arg date "$date_str" \
       --arg session "$session_pct" \
       --arg week "$week_pct" \
       --arg sonnet "$sonnet_pct" \
       --arg reset "$reset_time" \
       '. += [{
           "timestamp": ($ts | tonumber),
           "date": $date,
           "session_percent": ($session | tonumber),
           "week_percent": ($week | tonumber),
           "sonnet_percent": (if $sonnet == "" then null else ($sonnet | tonumber) end),
           "reset_time": (if $reset == "" then null else $reset end)
       }]' "$USAGE_LOG" > "${USAGE_LOG}.tmp" && mv "${USAGE_LOG}.tmp" "$USAGE_LOG"

    echo -n "✅ Logged usage: Session ${session_pct}%, Week ${week_pct}%"
    [ -n "$sonnet_pct" ] && echo -n ", Sonnet ${sonnet_pct}%"
    [ -n "$reset_time" ] && echo -n " (Reset: $reset_time)"
    echo ""
}

# Function to show usage trend
show_trend() {
    if [ ! -f "$USAGE_LOG" ]; then
        echo "No usage data logged yet"
        return
    fi

    echo "📊 Usage Trend (last 5 entries):"
    jq -r '.[-5:] | .[] |
        "\(.date): Session \(.session_percent)%, Week \(.week_percent)%" +
        (if .sonnet_percent then ", Sonnet \(.sonnet_percent)%" else "" end) +
        (if .reset_time then " (Reset: \(.reset_time))" else "" end)' "$USAGE_LOG"

    # Calculate rate of increase
    local current_week=$(jq -r '.[-1].week_percent' "$USAGE_LOG")
    local prev_week=$(jq -r '.[-2].week_percent // 0' "$USAGE_LOG")
    local current_ts=$(jq -r '.[-1].timestamp' "$USAGE_LOG")
    local prev_ts=$(jq -r '.[-2].timestamp // 0' "$USAGE_LOG")

    if [ "$prev_ts" != "0" ] && [ "$prev_ts" != "$current_ts" ]; then
        local hours_diff=$(( (current_ts - prev_ts) / 3600 ))
        local pct_diff=$(( current_week - prev_week ))
        if [ "$hours_diff" -gt 0 ]; then
            local rate=$(echo "scale=2; $pct_diff / $hours_diff" | bc)
            echo ""
            echo "📈 Current burn rate: ${rate}% per hour"

            # Project when we'll hit 100%
            local remaining=$(( 100 - current_week ))
            local hours_left=$(echo "scale=1; $remaining / $rate" | bc)
            echo "⏱️  Projected to hit 100% in ${hours_left} hours"
        fi
    fi
}

# Main menu
case "${1:-}" in
    log)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 log <session_%> <week_%> [sonnet_%] [reset_time]"
            echo "Example: $0 log 22 67"
            echo "Example: $0 log 22 67 45 '6:59pm'"
            exit 1
        fi
        log_usage "$2" "$3" "$4" "$5"
        show_trend
        ;;
    trend)
        show_trend
        ;;
    *)
        echo "Claude Usage Tracker"
        echo "==================="
        echo ""
        echo "Usage:"
        echo "  $0 log <session_%> <week_%> [sonnet_%] [reset_time]"
        echo "  $0 trend                     - Show usage trend"
        echo ""
        echo "To get FULL usage data:"
        echo "1. Go to claude.ai/settings/usage in your browser"
        echo "2. Log in if needed"
        echo "3. Record ALL percentages shown, including:"
        echo "   - Current session %"
        echo "   - Current week (all models) %"
        echo "   - Sonnet-specific % (if shown)"
        echo "   - Reset time (note if it changes!)"
        echo ""
        echo "Example: $0 log 22 67 45 '6:59pm Europe/London'"
        ;;
esac