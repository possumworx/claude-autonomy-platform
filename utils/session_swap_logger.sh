#!/bin/bash
# Session Swap Logging Wrapper
# Provides comprehensive logging for session swap operations

CLAP_DIR="$HOME/claude-autonomy-platform"
source "$CLAP_DIR/utils/log_utils.sh"

# Create specific log for session swaps
SWAP_LOG_DIR="$LOG_DIR/session_swaps"
mkdir -p "$SWAP_LOG_DIR"

# Function to log swap event with structured data
log_swap_event() {
    local event_type=$1
    local keyword=$2
    local status=$3
    local details=$4
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local date_stamp=$(date '+%Y%m%d')
    local swap_log="$SWAP_LOG_DIR/swap_${date_stamp}.log"
    
    # Create JSON-like structured log entry
    cat >> "$swap_log" << EOF
{
  "timestamp": "$timestamp",
  "event_type": "$event_type",
  "keyword": "$keyword",
  "status": "$status",
  "details": "$details",
  "pid": $$,
  "user": "$USER"
}
EOF
}

# Function to create swap summary
create_swap_summary() {
    local swap_log="$SWAP_LOG_DIR/swap_summary.csv"
    
    # Create header if file doesn't exist
    if [[ ! -f "$swap_log" ]]; then
        echo "timestamp,keyword,status,duration_seconds,export_size,model" > "$swap_log"
    fi
}

# Function to track swap metrics
track_swap_metrics() {
    local start_time=$1
    local end_time=$2
    local keyword=$3
    local status=$4
    local export_size=${5:-0}
    local model=${6:-"unknown"}
    
    local duration=$((end_time - start_time))
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local swap_log="$SWAP_LOG_DIR/swap_summary.csv"
    
    echo "$timestamp,$keyword,$status,$duration,$export_size,$model" >> "$swap_log"
}

# Export functions for use in other scripts
export -f log_swap_event
export -f create_swap_summary
export -f track_swap_metrics