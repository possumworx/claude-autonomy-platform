#!/bin/bash
# Traced version of health check - demonstrates execution tracing

# Source the tracer
source "$(dirname "$0")/trace_execution.sh"

# Use trace_exec for the main command
cd ~/claude-autonomy-platform && trace_exec python3 utils/healthcheck_status.py