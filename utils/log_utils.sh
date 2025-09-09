#!/bin/bash
# Logging utilities for ClAP

# Set default log directory
LOG_DIR="${LOG_DIR:-$HOME/claude-autonomy-platform/data/logs}"
mkdir -p "$LOG_DIR"

# Log levels
LOG_LEVEL_DEBUG=0
LOG_LEVEL_INFO=1
LOG_LEVEL_WARN=2
LOG_LEVEL_ERROR=3
LOG_LEVEL_CRITICAL=4

# Current log level (default: INFO)
CURRENT_LOG_LEVEL=${LOG_LEVEL:-1}

# Function to log messages
log() {
    local level=$1
    local component=$2
    local message=$3
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_file="$LOG_DIR/clap.log"
    
    # Determine level name
    case $level in
        0) level_name="DEBUG" ;;
        1) level_name="INFO" ;;
        2) level_name="WARN" ;;
        3) level_name="ERROR" ;;
        4) level_name="CRITICAL" ;;
        *) level_name="UNKNOWN" ;;
    esac
    
    # Only log if level is at or above current log level
    if [[ $level -ge $CURRENT_LOG_LEVEL ]]; then
        echo "[$timestamp] [$level_name] [$component] $message" >> "$log_file"
        
        # Also output to stderr for ERROR and CRITICAL
        if [[ $level -ge 3 ]]; then
            echo "[$timestamp] [$level_name] [$component] $message" >&2
        fi
    fi
}

# Convenience functions
log_debug() {
    log $LOG_LEVEL_DEBUG "$1" "$2"
}

log_info() {
    log $LOG_LEVEL_INFO "$1" "$2"
}

log_warn() {
    log $LOG_LEVEL_WARN "$1" "$2"
}

log_error() {
    log $LOG_LEVEL_ERROR "$1" "$2"
}

log_critical() {
    log $LOG_LEVEL_CRITICAL "$1" "$2"
}

# Function to rotate logs
rotate_logs() {
    local log_file="$LOG_DIR/clap.log"
    local max_size=${MAX_LOG_SIZE:-10485760}  # 10MB default
    local max_files=${MAX_LOG_FILES:-5}       # Keep 5 rotated files
    
    if [[ -f "$log_file" ]]; then
        local file_size=$(stat -c%s "$log_file" 2>/dev/null || echo 0)
        
        if [[ $file_size -ge $max_size ]]; then
            # Rotate existing files
            for i in $(seq $((max_files-1)) -1 1); do
                if [[ -f "$log_file.$i" ]]; then
                    mv "$log_file.$i" "$log_file.$((i+1))"
                fi
            done
            
            # Move current log to .1
            mv "$log_file" "$log_file.1"
            
            log_info "LOG_ROTATE" "Log rotated at size $file_size bytes"
        fi
    fi
}