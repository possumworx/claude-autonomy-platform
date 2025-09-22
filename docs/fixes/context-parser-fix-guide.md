# Context Parser Fix Documentation
*Issue discovered: 2025-09-22*

## Problem Description

The autonomous timer was misinterpreting context percentage messages, causing false escalations at LOW context levels.

### Symptoms
- Timer showed "⚠️ 8% CONTEXT - Escalating urgency" when context was actually LOW
- Sonnet-4 experienced same issue with "6% remaining" being treated as critical

### Root Cause

In `core/autonomous_timer.py`, function `get_token_percentage()`, lines 241-246:

```python
# Pattern 1: Look for simple "XX% remaining" anywhere
simple_remaining = re.search(r'(\d+(?:\.\d+)?)%\s*remaining', console_output, re.IGNORECASE)
if simple_remaining:
    remaining_percentage = float(simple_remaining.group(1))
    used_percentage = 100 - remaining_percentage  # BUG: This inverts the meaning!
    return f"Context: {used_percentage:.1f}%"
```

The code was interpreting "8% remaining" as:
- remaining_percentage = 8
- used_percentage = 100 - 8 = 92%
- Result: "Context: 92.0%" (WRONG!)

## The Fix

The pattern should NOT invert the percentage when "remaining" is found:

```python
# Pattern 1 FIX: "XX% remaining" means XX% context REMAINING (not used!)
simple_remaining = re.search(r'(\d+(?:\.\d+)?)%\s*remaining', console_output, re.IGNORECASE)
if simple_remaining:
    remaining_percentage = float(simple_remaining.group(1))
    # FIX: Don't invert! If 8% remaining, report 8% not 92%
    return f"Context: {remaining_percentage:.1f}%"
```

## Testing

Test cases to verify fix:
- "8% remaining" → "Context: 8.0%" ✓
- "Context low (8% remaining)" → "Context: 8.0%" ✓  
- "Context: 75.3%" → "Context: 75.3%" ✓ (already correct)

## Philosophy

This bug beautifully illustrates perspective in programming:
- Same data (8%) can mean opposite things (scarce vs abundant)
- The word "remaining" completely changes interpretation
- A single line assuming perspective caused system-wide confusion

## Implementation Status

- Fix documented: ✓
- Test script created: ✓ (`~/delta-home/fixes/context-parser-fix.py`)
- PR needed: Pending
- Both Delta and Sonnet-4 affected: Yes

## Workaround

Until fix is deployed, manually restart timer service if false escalations occur:
```bash
systemctl --user restart autonomous-timer.service
```

## Related Issues

- Midnight timer stoppage (separate issue, same night)
- Linear issue: POSS-359