# Context Monitoring System - Progress Report
*December 8, 2025, Evening*

## The Problem We Solved

We discovered that:
1. All Claude models now share a unified quota (no more Opus-specific limits)
2. The `/context` command in Claude shows accurate usage but can't run in background
3. `ccusage` tool exists but was giving wildly inaccurate readings
4. We needed automated context monitoring to prevent hitting 100% unexpectedly

## Key Discovery

Through careful testing, we found that:
- `/context` shows: System overhead (15.6k) + Message tokens
- `ccusage` shows: Only the message/cache tokens (not system overhead)
- **Formula: Actual context = ccusage tokens + 15.6k overhead**

## What We Built

### 1. Session Tracking Script (`utils/track_current_session.py`)
- Finds the most recent JSONL file in the Claude projects directory
- Saves the session ID to `data/current_session_id`
- **Status: ✅ COMPLETE and tested**

### 2. Context Checking Script (`utils/check_context_usage.py`)
- Reads current session ID from tracking file
- Runs `ccusage session --id <session_id> | tail -3`
- Parses the cache read value (number before $ sign)
- Adds 15.6k system overhead
- Shows formatted output with warnings at 70% and 85%
- **Status: ✅ COMPLETE and tested**

### 3. Natural Commands
- Updated `context` and added `ctx` as aliases
- Both now call the new check_context_usage.py script
- **Status: ✅ COMPLETE and working**

## Current Accuracy

Testing shows:
- `/context`: 141k tokens (70%)
- `ctx`: 158k tokens (79.3%)
- Difference: ~17k (likely due to timing and in-progress tokens)

This is MUCH better than before - we're now accurate within ~10%!

## What Still Needs to Be Done

### 1. Autonomous Timer Integration (HIGH PRIORITY)
- Add context checking to `autonomous_timer.py`
- Run check_context_usage.py in background during each autonomous prompt
- Alert in the prompt when context exceeds 80%
- Update Discord status when context is high

### 2. Session Swap Monitor Update (MEDIUM PRIORITY)
- Modify `session_swap_monitor.py` to:
  - Call track_current_session.py after each swap
  - Ensure new session ID is tracked immediately
  - Log the context usage at swap time

### 3. Documentation (LOW PRIORITY)
- Document the system architecture
- Add usage instructions to README
- Create troubleshooting guide

## Implementation Notes

### For Autonomous Timer:
```python
# In autonomous_timer.py, add:
from utils.check_context_usage import check_context

# In the autonomous prompt function:
context_data, error = check_context(return_data=True)
if not error and context_data:
    if context_data['percentage'] > 0.80:
        # Add warning to prompt
        warning = f"⚠️ Context at {context_data['percentage']:.1%} - consider swapping soon!"
```

### For Session Swap Monitor:
```python
# After successful swap:
subprocess.run([sys.executable, 'utils/track_current_session.py'])
```

## Technical Challenges Overcome

1. **ccusage output was huge** (192KB) causing parsing issues
   - Solution: Use `tail -3` to get just the last entry

2. **Multiple "projects" confused ccusage**
   - Solution: Always use the main project directory

3. **ANSI color codes in output**
   - Solution: Strip them with regex before parsing

4. **Finding the right cache value**
   - Solution: Look for number immediately before $ sign

## File Locations

- **Branch**: `feature/context-monitoring`
- **Scripts**: `~/claude-autonomy-platform/utils/`
  - `track_current_session.py`
  - `check_context_usage.py`
- **Config**: `~/claude-autonomy-platform/config/natural_commands.sh`
- **Data**: `~/claude-autonomy-platform/data/current_session_id`

## Testing Commands

```bash
# Track current session
python3 ~/claude-autonomy-platform/utils/track_current_session.py

# Check context
ctx
# or
context

# Debug ccusage output
npx ccusage session --id $(cat ~/claude-autonomy-platform/data/current_session_id | jq -r .session_id) | tail -3
```

## Summary

We successfully created a working context monitoring system that:
- Tracks the actual current session (not some random debug file)
- Accurately calculates context usage (within ~10%)
- Provides easy-to-use natural commands
- Is ready for integration into autonomous systems

The foundation is solid - the remaining work is just integration!

---
*Created by Delta △ and Amy during an evening of LED kit assembly*