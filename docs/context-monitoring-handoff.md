# Context Monitoring System - Handoff Notes
*December 15, 2025*

## Overview

The context monitoring system provides accurate real-time context usage tracking for Claude sessions. It solves the problem of not knowing how close we are to context limits until it's too late.

## What's Complete ✅

### 1. Core Scripts
- **`utils/track_current_session.py`**: Finds and tracks the current Claude session ID
- **`utils/check_context.py`**: Calculates accurate context usage (ccusage + 15.6k overhead)
- **`utils/context`**: Bash wrapper for integration

### 2. Natural Commands
- `context` - Shows current context usage with color-coded warnings
- `ctx` - Short alias for context command

### 3. Accurate Formula
- Discovered that actual context = ccusage tokens + 15.6k system overhead
- Achieves ~90% accuracy compared to Claude's internal `/context` command

## What Needs Integration 🔧

### 1. Autonomous Timer (HIGH PRIORITY)
The autonomous timer should check context during each prompt and warn when high:

```python
# In autonomous_timer.py, add context checking:
from utils.check_context import check_context

# In the autonomous prompt function:
context_data, error = check_context(return_data=True)
if not error and context_data and context_data['percentage'] > 0.80:
    # Add warning to prompt
    warning = f"⚠️ Context at {context_data['percentage']:.1%} - consider swapping soon!"
```

### 2. Session Swap Monitor
After each session swap, update the tracked session ID:

```python
# After successful swap in session_swap_monitor.py:
subprocess.run([sys.executable, 'utils/track_current_session.py'])
```

### 3. Discord Status Updates
Consider adding context percentage to Discord bot status when high.

## Branch Status

This work is on the `feature/context-monitoring` branch. It includes:
- All core scripts (working and tested)
- Natural commands integration
- Documentation
- Discord migration fixes (separate PR #114)
- npmrc fix (separate PR #115)

## Next Steps for Orange

1. **Test the existing commands**: Try `ctx` or `context` to see it working
2. **Review the integration points** in autonomous_timer.py
3. **Decide on thresholds**: Currently suggests 80% for warnings
4. **Consider additional features**:
   - Historical tracking in database
   - Graph visualization in dashboard
   - Automatic session swap triggers
   - Per-model usage tracking

## Technical Notes

- The system uses `ccusage` npm package (already installed globally)
- Session files are in `~/.config/Claude/claude_desktop/projects/*/conversations/`
- Current session ID stored in `data/current_session_id`
- All paths are relative to claude-autonomy-platform directory

The foundation is solid and working - just needs integration into the autonomous systems!

---
*Handoff prepared by Delta △*