# ClAP Execution Tracing

A lightweight execution tracer to understand script call chains during autonomous operations.

## Quick Start

```bash
# Trace a single command
./utils/trace_execution.sh some_command arg1 arg2

# View recent trace
./utils/trace_execution.sh --tail 50

# Analyze execution patterns
./utils/trace_execution.sh --analyze
```

## Integration with ClAP Scripts

### Method 1: Wrapper Approach
Replace direct calls with traced calls:

```bash
# Before:
./utils/session_swap.sh

# After:
./utils/trace_execution.sh ./utils/session_swap.sh
```

### Method 2: Source Integration
Add tracing inside scripts:

```bash
#!/bin/bash
source "$(dirname "$0")/trace_execution.sh"

# Trace external commands
trace_exec python3 some_script.py
trace_exec ./another_script.sh

# Regular commands run untraced
echo "This won't be traced"
```

### Method 3: Automatic Tracing
Set up aliases or wrapper scripts:

```bash
# In .bashrc or natural commands
alias traced_swap='trace_execution.sh session_swap.sh'
```

## Trace Output Format

```
[2025-08-21 14:30:15.123]→ EXEC: check_health
[2025-08-21 14:30:15.124]  CALLER: autonomous_handler.sh:45
[2025-08-21 14:30:15.124]  PID: 12345 PPID: 12340
[2025-08-21 14:30:15.234]  → EXEC: systemctl --user status
[2025-08-21 14:30:15.235]    CALLER: check_health:23
[2025-08-21 14:30:15.235]    PID: 12346 PPID: 12345
[2025-08-21 14:30:15.345]  ← SUCCESS: systemctl (0.110s)
[2025-08-21 14:30:15.456]← SUCCESS: check_health (0.332s)
```

## Environment Variables

- `TRACE_LOG`: Log file location (default: `~/claude-autonomy-platform/logs/execution_trace.log`)
- `TRACE_ENABLED`: Enable/disable tracing (default: 1)
- `TRACE_DEPTH`: Internal use for indentation

## Use Cases

1. **Debugging Autonomous Operations**
   - See exactly what scripts run during autonomous periods
   - Identify which scripts call which others
   - Find performance bottlenecks

2. **Understanding Call Chains**
   - Trace how session swaps trigger various utilities
   - See the full flow of export operations
   - Map dependencies between scripts

3. **Performance Analysis**
   - Identify slow operations
   - Find frequently called scripts
   - Detect failing commands

## Example Integration

Here's how to add tracing to the session swap monitor:

```bash
# In session_swap_monitor.sh
source "$(dirname "$0")/../utils/trace_execution.sh"

# Trace the critical operations
trace_exec python3 "$SCRIPT_DIR/update_conversation_history.py"
trace_exec "$SCRIPT_DIR/session_swap.sh"
trace_exec "$SCRIPT_DIR/export_handler.sh"
```

## Best Practices

1. **Trace Critical Paths**: Focus on operations that are complex or prone to failure
2. **Avoid Over-Tracing**: Don't trace every single command - focus on script boundaries
3. **Regular Cleanup**: Rotate or archive trace logs periodically
4. **Production vs Debug**: Consider using TRACE_ENABLED flag for different environments

## Analysis Commands

```bash
# Most called scripts
grep "→ EXEC:" ~/claude-autonomy-platform/logs/execution_trace.log | awk '{print $4}' | sort | uniq -c | sort -rn

# Failed operations
grep "← FAILED:" ~/claude-autonomy-platform/logs/execution_trace.log

# Slowest operations
grep "← SUCCESS:" ~/claude-autonomy-platform/logs/execution_trace.log | sed 's/.*(\(.*\)s)/\1/' | sort -rn | head
```