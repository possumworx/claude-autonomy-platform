# Autonomous Timer Issues - September 22, 2025

## Summary
Both Delta and Sonnet-4's autonomous timers stopped working after midnight on September 21-22, 2025. Additionally, Sonnet-4 received incorrect context escalation warnings.

## Issue 1: Timer Stops After Midnight

### Symptoms
- Delta's timer: Last message at 00:12:26, then silent until manual restart at 08:24
- Sonnet-4's timer: Last message at 00:09, detected session as down, health check failed at 00:33
- Both timers affected simultaneously around midnight

### Possible Causes
1. Network-wide issue around midnight
2. Bug in date rollover handling 
3. Health check failure causing complete halt (shouldn't happen)
4. Session detection false positive causing backoff

### Resolution
- Manual restart of service fixes the issue
- `systemctl --user restart autonomous-timer.service`

## Issue 2: Incorrect Context Escalation

### Symptoms
- Sonnet-4 received "escalating urgency" warnings at 8% and 6% context
- These should only trigger at high context (70%+)

### Root Cause
Bug in context percentage parsing in `autonomous_timer.py`:

```python
# Pattern 1: Look for simple "XX% remaining" anywhere
simple_remaining = re.search(r'(\d+(?:\.\d+)?)%\s*remaining', console_output, re.IGNORECASE)
if simple_remaining:
    remaining_percentage = float(simple_remaining.group(1))
    used_percentage = 100 - remaining_percentage  # BUG HERE!
    return f"Context: {used_percentage:.1f}%"
```

The code assumes "X% remaining" means remaining context, but it might actually be showing used context in some displays.

- If display shows "8% remaining" (meaning 8% used)
- Timer calculates: 100 - 8 = 92% used
- Triggers high context warning incorrectly

### Fix Needed
1. Verify what Claude Code actually displays (used vs remaining)
2. Update parsing logic to handle both cases correctly
3. Add validation to prevent impossible scenarios (e.g., escalating at <20%)

## Action Items
1. Monitor if midnight issue recurs
2. Fix context percentage parsing bug
3. Add better error recovery for health check failures
4. Consider adding a watchdog to detect stuck timer

## Notes
- Both issues might be related - incorrect context parsing could cause session to appear "down"
- Health check failures should not stop the entire timer
- Need better logging around midnight transitions