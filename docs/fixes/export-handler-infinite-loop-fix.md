# Export Handler Infinite Loop Fix

## Problem
The export handler was creating an infinite loop when trying to detect if Claude was still thinking. The detector script was outputting status messages like "Claude is still thinking..." to stdout, which Claude would then read and respond to, creating more output and perpetuating the cycle.

## Root Cause
The `wait_for_claude_ready()` function in `export_handler.sh` was outputting status messages to stdout instead of stderr. When Claude reads these messages, it interprets them as user input and responds, which creates more "thinking" activity, preventing the detector from ever seeing Claude as "ready".

## Solution (PR #42)
1. Created `utils/claude_state_detector.sh` with the `wait_for_claude_ready()` function
2. Modified all status output to go to stderr using `>&2`
3. Updated `export_handler.sh` to source the detector script
4. Removed duplicate function definition

## Key Changes
- All "Waiting for Claude..." and "Claude is still thinking..." messages now output to stderr
- Claude only sees the actual export command, not the status messages
- The detector can properly identify when Claude is ready

## Files Modified
- `utils/claude_state_detector.sh` - New file with the detection function
- `utils/export_handler.sh` - Sources the detector, removed duplicate function

## Testing
The fix has been tested and successfully prevents the infinite loop. Session swaps now complete properly without getting stuck in the export phase.

△