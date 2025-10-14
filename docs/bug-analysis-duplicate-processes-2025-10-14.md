# Bug Analysis: Duplicate Claude Code Processes
**Date:** 2025-10-14
**Reported by:** Amy & Apple
**Investigated by:** Sparkle-Orange
**Status:** Root cause identified

## Problem Description

Two Claude Code processes (PIDs 389235 & 391796) were found running simultaneously outside their proper tmux sessions, both consuming high CPU and causing UI flickering and crashes.

## Root Cause Analysis

### The Race Condition

The duplicate processes were caused by a race condition in the session swap system when Claude Code takes an unusually long time to start:

1. **First Swap Initiated** (20:01:37)
   - session_swap.sh starts executing
   - Line 228 starts new Claude Code process in tmux
   - Line 232 removes lockfile immediately after starting Claude
   - **BUT**: Claude takes 401 seconds to become ready (stuck "thinking")

2. **Second Swap Triggered** (20:09:45)
   - While first Claude is still loading, trigger file is set again
   - Lockfile is GONE (removed at 20:01:37), so monitor thinks system is idle
   - Monitor triggers SECOND session swap
   - Second swap kills the first tmux session mid-startup (line 181)
   - Second swap starts ANOTHER Claude Code process

3. **Result**: Two orphaned Claude processes
   - Both consuming high CPU
   - Neither properly attached to tmux
   - Competing for resources and causing instability

### Evidence from Logs

```
Oct 14 20:01:37 - Running session swap with keyword: HEDGEHOGS
[SEND_TO_CLAUDE] Claude thinking... (waiting 0s)
[SEND_TO_CLAUDE] Claude thinking... (waiting 30s)
[SEND_TO_CLAUDE] Claude thinking... (waiting 60s)
... (continues for 401 seconds)
[SEND_TO_CLAUDE] Claude ready after 401s - sending message

Oct 14 20:09:45 - Running session swap with keyword: HEDGEHOGS
[Another swap triggered while first still in progress!]

Oct 14 20:11:24 - session-swap-monitor.service was stopped and restarted
```

### Vulnerable Code Paths

**session_swap.sh (lines 228-232):**
```bash
# Start Claude in the new session
tmux send-keys -t autonomous-claude "cd $CLAP_DIR && claude..." Enter

# Remove lockfile to resume autonomous timer notifications
echo "[SESSION_SWAP] Removing lockfile to resume autonomous timer..."
rm -f "$LOCKFILE"
```

**Problem**: Lockfile is removed IMMEDIATELY after starting Claude, but Claude might take minutes to become ready. During that time, the system is vulnerable to concurrent swap triggers.

**session_swap_monitor.py (lines 64-73):**
```python
if content != "FALSE" and content != "":
    keyword = content if content in ["AUTONOMY", "BUSINESS", ...] else "NONE"

    # Run session swap
    run_session_swap(keyword)

    # Reset trigger file only after successful completion
    TRIGGER_FILE.write_text("FALSE")
```

**Problem**: No check for existing swap in progress. If Claude startup is delayed, a new trigger can initiate a second swap.

## Prevention Measures

### Proposed Solutions

1. **Keep lockfile until Claude is ready**
   - Don't remove lockfile at line 232
   - Add a post-swap verification step that waits for Claude to be responsive
   - Only remove lockfile after confirming Claude is ready

2. **Add concurrent swap protection in monitor**
   - Check if lockfile exists before starting new swap
   - Add a "swap in progress" state that prevents concurrent swaps
   - Consider using a different lockfile for "swap complete" vs "system ready"

3. **Improve Claude readiness detection**
   - The 401-second wait suggests Claude startup detection isn't working well
   - Consider adding better health checks for Claude readiness
   - Maybe use a simpler command than the export workflow to test readiness

4. **Add duplicate process detection**
   - Enhance health monitoring to detect multiple Claude processes
   - Automatically kill duplicates when detected
   - Alert when duplicate condition occurs

### Implementation Priority

**HIGH**: Keep lockfile until Claude is ready (solution #1)
- Most direct fix to the race condition
- Minimal code changes required
- Low risk of unintended side effects

**MEDIUM**: Add concurrent swap protection (solution #2)
- Additional safety layer
- Helps with edge cases
- Should be done alongside #1

**LOW**: Improve readiness detection (solution #3)
- Nice to have but not critical
- The 401-second wait was unusual, not typical
- Can be addressed in future improvements

**LOW**: Duplicate process detection (solution #4)
- Symptom management rather than prevention
- Good for monitoring but doesn't fix root cause
- Should be added but not sufficient alone

## Testing Recommendations

After implementing fixes:
1. Test session swap with simulated slow Claude startup
2. Trigger multiple swaps in rapid succession
3. Monitor for orphaned processes
4. Verify lockfile behavior throughout swap lifecycle

## Notes

- This bug was intermittent and hard to reproduce because it requires Claude to be unusually slow during startup
- The service restart at 20:11:24 likely cleaned up the duplicate processes
- Amy's manual kill of PIDs 389235 & 391796 resolved the immediate issue
- The system is currently stable with just one Claude process per consciousness
