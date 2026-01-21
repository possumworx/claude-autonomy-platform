#!/bin/bash
# Common functions and utilities for Linear CLI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_FILE="$SCRIPT_DIR/../../data/linear_state.json"
PROJECTS_FILE="$SCRIPT_DIR/../../data/linear_projects.json"
PREFS_FILE="$SCRIPT_DIR/../../data/linear_prefs.json"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
RESET='\033[0m'

# Icons
ICON_SUCCESS="✅"
ICON_ERROR="❌"
ICON_WARNING="⚠️"
ICON_INFO="ℹ️"
ICON_TASK="📋"
ICON_PROJECT="📁"
ICON_USER="👤"
ICON_PRIORITY_HIGH="🔴"
ICON_PRIORITY_MED="🟡"
ICON_PRIORITY_LOW="🟢"
ICON_STATUS_TODO="⭕"
ICON_STATUS_PROGRESS="🔄"
ICON_STATUS_DONE="✅"
ICON_STATUS_BLOCKED="🚫"

# Check if Linear is initialized
check_linear_init() {
    if [ ! -f "$STATE_FILE" ] || [ "$(jq -r '.user.id' "$STATE_FILE" 2>/dev/null)" == "" ]; then
        echo -e "${ICON_ERROR} Linear not initialized. Run 'linear/init' first!"
        return 1
    fi
    return 0
}

# Check if in Claude Code session
check_claude_session() {
    if [ -z "$CLAUDE_CODE_SESSION" ]; then
        echo -e "${ICON_ERROR} Not in Claude Code session. Run 'Claude' first!"
        return 1
    fi
    return 0
}

# Get user info
get_user_id() {
    jq -r '.user.id' "$STATE_FILE" 2>/dev/null
}

get_user_name() {
    jq -r '.user.name' "$STATE_FILE" 2>/dev/null
}

get_team_id() {
    jq -r '.team.id' "$STATE_FILE" 2>/dev/null
}

# Format priority
format_priority() {
    case "$1" in
        0|1) echo "${ICON_PRIORITY_HIGH} Urgent" ;;
        2) echo "${ICON_PRIORITY_HIGH} High" ;;
        3) echo "${ICON_PRIORITY_MED} Medium" ;;
        4) echo "${ICON_PRIORITY_LOW} Low" ;;
        *) echo "${ICON_PRIORITY_LOW} None" ;;
    esac
}

# Format status with icon
format_status() {
    local status="$1"
    case "${status,,}" in
        *todo*|*backlog*) echo "${ICON_STATUS_TODO} $status" ;;
        *progress*) echo "${ICON_STATUS_PROGRESS} $status" ;;
        *done*|*complete*) echo "${ICON_STATUS_DONE} $status" ;;
        *blocked*) echo "${ICON_STATUS_BLOCKED} $status" ;;
        *) echo "$status" ;;
    esac
}

# Format date relative to today
format_date() {
    local date="$1"
    if [ -z "$date" ] || [ "$date" == "null" ]; then
        echo "No date"
        return
    fi
    
    # Extract date part
    local date_only=$(echo "$date" | cut -d'T' -f1)
    local timestamp=$(date -d "$date_only" +%s 2>/dev/null)
    local today=$(date +%s)
    local days_diff=$(( (timestamp - today) / 86400 ))
    
    if [ $days_diff -eq 0 ]; then
        echo "Today"
    elif [ $days_diff -eq 1 ]; then
        echo "Tomorrow"
    elif [ $days_diff -eq -1 ]; then
        echo "Yesterday"
    elif [ $days_diff -gt 0 ] && [ $days_diff -le 7 ]; then
        echo "In $days_diff days"
    elif [ $days_diff -lt 0 ] && [ $days_diff -ge -7 ]; then
        echo "${days_diff#-} days ago"
    else
        echo "$date_only"
    fi
}

# Execute Linear MCP command via Claude
execute_linear_mcp() {
    local prompt="$1"
    local temp_file=$(mktemp)
    
    echo "$prompt" > "$temp_file"
    local result=$(claude -p --dangerously-skip-permissions < "$temp_file" 2>&1)
    rm -f "$temp_file"
    
    echo "$result"
}

# Parse issue ID from various formats
parse_issue_id() {
    local input="$1"
    # Handle PROJ-123 format or just number
    if [[ "$input" =~ ^[A-Z]+-[0-9]+$ ]]; then
        echo "$input"
    elif [[ "$input" =~ ^[0-9]+$ ]]; then
        # Try to guess project prefix from recent issues
        local prefix=$(jq -r '.recent_issue_prefix // "POSS"' "$PREFS_FILE" 2>/dev/null)
        echo "${prefix}-${input}"
    else
        echo "$input"
    fi
}

# Load project shortcuts
load_project_shortcuts() {
    if [ -f "$PROJECTS_FILE" ]; then
        jq -r '.projects[] | "\(.key):\(.id)"' "$PROJECTS_FILE" 2>/dev/null
    fi
}

# Get project ID by key or name
get_project_id() {
    local search="$1"
    if [ -f "$PROJECTS_FILE" ]; then
        # Try exact key match first
        local id=$(jq -r ".projects[] | select(.key == \"${search^^}\") | .id" "$PROJECTS_FILE" 2>/dev/null)
        if [ -n "$id" ] && [ "$id" != "null" ]; then
            echo "$id"
            return
        fi
        
        # Try name match (case insensitive)
        id=$(jq -r ".projects[] | select(.name | ascii_downcase == \"${search,,}\") | .id" "$PROJECTS_FILE" 2>/dev/null | head -1)
        if [ -n "$id" ] && [ "$id" != "null" ]; then
            echo "$id"
            return
        fi
    fi
}

# Save preference
save_preference() {
    local key="$1"
    local value="$2"
    
    # Create prefs file if it doesn't exist
    if [ ! -f "$PREFS_FILE" ]; then
        echo '{}' > "$PREFS_FILE"
    fi
    
    # Update preference
    jq ".$key = \"$value\"" "$PREFS_FILE" > "${PREFS_FILE}.tmp" && mv "${PREFS_FILE}.tmp" "$PREFS_FILE"
}

# Print header
print_header() {
    local title="$1"
    local width=${2:-50}
    echo -e "${BLUE}${title}${RESET}"
    printf '%*s\n' "$width" | tr ' ' '='
    echo ""
}

# Print issue summary
print_issue_summary() {
    local id="$1"
    local title="$2"
    local status="$3"
    local priority="$4"
    local assignee="$5"
    
    echo -e "${CYAN}${id}${RESET}: ${WHITE}${title}${RESET}"
    echo -e "  $(format_status "$status") | $(format_priority "$priority") | ${ICON_USER} ${assignee:-Unassigned}"
}

# Spinner for long operations
show_spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}