#!/bin/bash
# Execution tracer for ClAP - logs script calls and their relationships
# Lightweight wrapper to understand call chains during autonomous operations

# Configuration
TRACE_LOG="${TRACE_LOG:-$HOME/claude-autonomy-platform/logs/execution_trace.log}"
TRACE_ENABLED="${TRACE_ENABLED:-1}"
TRACE_DEPTH="${TRACE_DEPTH:-0}"

# Create log directory if needed
mkdir -p "$(dirname "$TRACE_LOG")"

# Function to log execution
trace_log() {
    if [[ "$TRACE_ENABLED" != "1" ]]; then
        return
    fi
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S.%3N')
    local indent=""
    for ((i=0; i<TRACE_DEPTH; i++)); do
        indent+="  "
    done
    
    echo "[$timestamp]$indent $*" >> "$TRACE_LOG"
}

# Function to trace a command execution
trace_exec() {
    local cmd="$1"
    shift
    
    # Log the call
    trace_log "→ EXEC: $cmd $*"
    trace_log "  CALLER: ${BASH_SOURCE[2]:-unknown}:${BASH_LINENO[1]:-?}"
    trace_log "  PID: $$ PPID: $PPID"
    
    # Increment depth for child processes
    export TRACE_DEPTH=$((TRACE_DEPTH + 1))
    
    # Execute the command
    local start_time=$(date +%s.%N)
    "$cmd" "$@"
    local exit_code=$?
    local end_time=$(date +%s.%N)
    
    # Calculate duration
    local duration=$(echo "$end_time - $start_time" | bc)
    
    # Restore depth
    export TRACE_DEPTH=$((TRACE_DEPTH - 1))
    
    # Log the result
    if [[ $exit_code -eq 0 ]]; then
        trace_log "← SUCCESS: $cmd (${duration}s)"
    else
        trace_log "← FAILED: $cmd (exit: $exit_code, ${duration}s)"
    fi
    
    return $exit_code
}

# Function to enable/disable tracing
trace_enable() {
    export TRACE_ENABLED=1
    trace_log "=== TRACING ENABLED ==="
}

trace_disable() {
    trace_log "=== TRACING DISABLED ==="
    export TRACE_ENABLED=0
}

# Function to show recent trace
trace_tail() {
    local lines="${1:-50}"
    if [[ -f "$TRACE_LOG" ]]; then
        tail -n "$lines" "$TRACE_LOG"
    else
        echo "No trace log found at: $TRACE_LOG"
    fi
}

# Function to analyze trace for patterns
trace_analyze() {
    if [[ ! -f "$TRACE_LOG" ]]; then
        echo "No trace log found"
        return 1
    fi
    
    echo "=== Execution Trace Analysis ==="
    echo
    echo "Most called scripts:"
    grep "→ EXEC:" "$TRACE_LOG" | awk '{print $4}' | sort | uniq -c | sort -rn | head -10
    echo
    echo "Failed executions:"
    grep "← FAILED:" "$TRACE_LOG" | tail -10
    echo
    echo "Longest running commands:"
    grep "← SUCCESS:" "$TRACE_LOG" | sed 's/.*(\(.*\)s)/\1/' | sort -rn | head -10
}

# If sourced, provide functions
# If executed directly, wrap the command
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -eq 0 ]]; then
        echo "Usage: trace_execution.sh <command> [args...]"
        echo "   or: trace_execution.sh --tail [lines]"
        echo "   or: trace_execution.sh --analyze"
        echo ""
        echo "Environment variables:"
        echo "  TRACE_LOG      - Log file location (default: ~/claude-autonomy-platform/logs/execution_trace.log)"
        echo "  TRACE_ENABLED  - Enable/disable tracing (default: 1)"
        echo ""
        echo "To use in scripts, source this file and use trace_exec:"
        echo "  source trace_execution.sh"
        echo "  trace_exec some_command arg1 arg2"
        exit 1
    fi
    
    case "$1" in
        --tail)
            trace_tail "${2:-50}"
            ;;
        --analyze)
            trace_analyze
            ;;
        *)
            trace_exec "$@"
            ;;
    esac
fi