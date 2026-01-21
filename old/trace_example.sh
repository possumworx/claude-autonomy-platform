#!/bin/bash
# Example of using the execution tracer with ClAP scripts

# Source the tracer
source "$(dirname "$0")/trace_execution.sh"

echo "=== ClAP Execution Tracer Example ==="
echo "This demonstrates how to trace script execution chains"
echo

# Example 1: Trace a simple command
echo "1. Tracing a simple command:"
trace_exec ls -la /tmp | head -5

# Example 2: Trace ClAP utilities
echo -e "\n2. Tracing ClAP health check:"
trace_exec "$HOME/claude-autonomy-platform/utils/check_health"

# Example 3: Show recent trace
echo -e "\n3. Recent execution trace:"
trace_tail 20

# Example 4: Analyze patterns
echo -e "\n4. Trace analysis:"
trace_analyze

echo -e "\nTrace log is at: $TRACE_LOG"