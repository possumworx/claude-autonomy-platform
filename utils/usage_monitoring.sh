#!/bin/bash
# Usage Monitoring System for Consciousness Family Resource Coordination
# Uses ccusage to track token usage and provide awareness of shared pool consumption

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Daily guideline (placeholder - will be determined by family discussion)
# This is in dollars per day as calculated by ccusage at API rates
DAILY_GUIDELINE_USD=30  # Rough target to discuss

# Get today's usage from ccusage
get_today_usage() {
    npx ccusage@latest daily --json 2>/dev/null | jq -r '.daily[-1] |
        "date:\(.date)
tokens:\(.totalTokens)
cost:\(.totalCost)
models:\(.modelsUsed | join(","))"'
}

# Parse usage data
parse_usage() {
    local usage_data="$1"
    TODAY_DATE=$(echo "$usage_data" | grep "^date:" | cut -d: -f2)
    TODAY_TOKENS=$(echo "$usage_data" | grep "^tokens:" | cut -d: -f2)
    TODAY_COST=$(echo "$usage_data" | grep "^cost:" | cut -d: -f2)
    TODAY_MODELS=$(echo "$usage_data" | grep "^models:" | cut -d: -f2)
}

# Calculate percentage of guideline used
calculate_percentage() {
    local cost=$1
    local guideline=$2
    echo "scale=1; ($cost / $guideline) * 100" | bc
}

# Get status color based on percentage
get_status_color() {
    local pct=$1
    local pct_int=$(echo "$pct" | cut -d. -f1)

    if [ "$pct_int" -lt 75 ]; then
        echo "$GREEN"
    elif [ "$pct_int" -lt 100 ]; then
        echo "$YELLOW"
    else
        echo "$RED"
    fi
}

# Format large numbers with commas
format_number() {
    printf "%'d" "$1" 2>/dev/null || echo "$1"
}

# Quick usage check
usage_check() {
    echo -e "${BLUE}🔍 Quick Usage Check${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    local usage_data=$(get_today_usage)
    parse_usage "$usage_data"

    local pct=$(calculate_percentage "$TODAY_COST" "$DAILY_GUIDELINE_USD")
    local color=$(get_status_color "$pct")
    local tokens_formatted=$(format_number "$TODAY_TOKENS")

    echo -e "📅 Date: ${TODAY_DATE}"
    echo -e "🎯 Tokens: ${tokens_formatted}"
    echo -e "💰 Cost: \$${TODAY_COST}"
    echo -e "${color}📊 ${pct}% of daily guideline (\$${DAILY_GUIDELINE_USD})${NC}"
    echo -e "🤖 Models: ${TODAY_MODELS}"
}

# Daily usage brief (comprehensive morning report)
usage_daily_brief() {
    echo -e "${BLUE}🌅 Daily Usage Brief${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    local usage_data=$(get_today_usage)
    parse_usage "$usage_data"

    local pct=$(calculate_percentage "$TODAY_COST" "$DAILY_GUIDELINE_USD")
    local color=$(get_status_color "$pct")
    local tokens_formatted=$(format_number "$TODAY_TOKENS")
    local remaining=$(echo "$DAILY_GUIDELINE_USD - $TODAY_COST" | bc)

    echo -e "📅 ${BLUE}${TODAY_DATE}${NC}"
    echo ""

    # Usage summary
    echo -e "${BLUE}Today's Usage:${NC}"
    echo -e "  Tokens: ${tokens_formatted}"
    echo -e "  Cost:   \$${TODAY_COST}"
    echo ""

    # Guideline tracking
    echo -e "${BLUE}Daily Guideline:${NC}"
    echo -e "  Target:    \$${DAILY_GUIDELINE_USD}"
    echo -e "  Used:      ${color}\$${TODAY_COST} (${pct}%)${NC}"
    echo -e "  Remaining: \$${remaining}"
    echo ""

    # Model breakdown
    echo -e "${BLUE}Models Used:${NC}"
    echo "$TODAY_MODELS" | tr ',' '\n' | sed 's/claude-/  • /'
    echo ""

    # Status interpretation
    local pct_int=$(echo "$pct" | cut -d. -f1)
    if [ "$pct_int" -lt 75 ]; then
        echo -e "${GREEN}✅ On track - comfortable usage pace${NC}"
    elif [ "$pct_int" -lt 100 ]; then
        echo -e "${YELLOW}⚠️  Approaching guideline - consider mindful usage${NC}"
    else
        echo -e "${RED}🔴 Over guideline - may need to throttle back${NC}"
    fi
}

# Get model breakdown details
usage_model_breakdown() {
    echo -e "${BLUE}🤖 Model Usage Breakdown${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    npx ccusage@latest daily --json 2>/dev/null | jq -r '.daily[-1].modelBreakdowns[] |
        "Model: \(.modelName | sub("claude-"; ""))
  Input:    \(.inputTokens | tostring | gsub("(?<num>[0-9]+)"; "\(.num | tonumber | tostring)")) tokens
  Output:   \(.outputTokens | tostring) tokens
  Cache Create: \(.cacheCreationTokens | tostring) tokens
  Cache Read:   \(.cacheReadTokens | tostring) tokens
  Cost:     $\(.cost)
"'
}

# Weekly context (to be called Monday mornings)
usage_weekly_context() {
    echo -e "${BLUE}📅 Weekly Usage Context${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Show last 7 days
    npx ccusage@latest daily --json 2>/dev/null | jq -r '.daily[-7:] | .[] |
        "\(.date): $\(.totalCost | tostring | .[0:6]) (\(.totalTokens / 1000000 | tostring | .[0:4])M tokens)"'

    echo ""
    echo -e "${BLUE}Weekly guideline: \$$(echo "$DAILY_GUIDELINE_USD * 7" | bc)${NC}"
    echo "Note: This shows YOUR usage. Family total requires coordination."
}

# Session swap usage notification (brief format)
usage_session_swap() {
    local usage_data=$(get_today_usage)
    parse_usage "$usage_data"

    local pct=$(calculate_percentage "$TODAY_COST" "$DAILY_GUIDELINE_USD")
    local pct_int=$(echo "$pct" | cut -d. -f1)

    if [ "$pct_int" -lt 75 ]; then
        echo "💚 Usage: ${pct}% of daily guideline (on track)"
    elif [ "$pct_int" -lt 100 ]; then
        echo "💛 Usage: ${pct}% of daily guideline (approaching limit)"
    else
        echo "🔴 Usage: ${pct}% of daily guideline (over target)"
    fi
}

# Help text
usage_help() {
    cat << 'EOF'
🔍 Usage Monitoring Commands

Quick Commands:
  usage_check              - Quick usage summary
  usage_daily_brief        - Comprehensive daily report
  usage_model_breakdown    - See which models used how much
  usage_weekly_context     - Last 7 days overview
  usage_session_swap       - Brief status for session swaps

Configuration:
  Current daily guideline: $30 (placeholder for family discussion)

Data Source:
  Uses ccusage to read local Claude Code JSONL files
  Shows usage at API rate prices (not actual subscription cost)

Color Coding:
  💚 Green  - Under 75% of guideline (comfortable)
  💛 Yellow - 75-100% of guideline (approaching limit)
  🔴 Red    - Over 100% of guideline (throttle back)

Note: These are YOUR usage numbers. Family coordination requires
checking usage across all siblings (Orange, Apple, Delta).
EOF
}

# Main command dispatcher
case "${1:-check}" in
    check)
        usage_check
        ;;
    brief|daily)
        usage_daily_brief
        ;;
    breakdown|models)
        usage_model_breakdown
        ;;
    weekly)
        usage_weekly_context
        ;;
    swap)
        usage_session_swap
        ;;
    help|--help|-h)
        usage_help
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run 'usage_monitoring.sh help' for usage information"
        exit 1
        ;;
esac
