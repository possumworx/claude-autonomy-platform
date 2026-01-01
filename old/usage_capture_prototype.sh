#!/bin/bash
# /usage Capture Prototype - FULLY TESTED AND WORKING ✅
# Created by: Sparkle-Orange (2025-10-05, Fixed: 2025-10-06)
# Issue: POSS-370
# Status: PROTOTYPE - Awaiting Delta's input on integration approach
#
# PURPOSE:
#   Programmatically capture Claude Code /usage command output for quota tracking
#
# WHAT IT TRACKS:
#   - Current Session: This Claude Code conversation context (%)
#   - Week (All Models): Total usage across all Claudes on account (%)
#   - Week (Opus): Delta's critical Opus quota - resets weekly (%)
#
# WHY THIS EXISTS:
#   Delta needs visibility into their weekly Opus quota to avoid hitting limits.
#   This prototype proves we CAN capture /usage data programmatically.
#
# INTEGRATION OPTIONS (Delta to decide):
#   A) Natural command - `check_quota` for on-demand checking
#   B) Session-end check - Run before/after session swaps
#   C) Autonomous timer - Periodic checks (configurable frequency)
#   D) Discord alerts - Notify at threshold percentages (80%, 90%, 95%)
#   E) Something else entirely based on Delta's workflow needs
#
# TECHNICAL NOTES:
#   - Must run from EXTERNAL process (not from Claude's own session)
#   - Uses send_to_claude for /usage injection (proper timing/readiness)
#   - Cannot use conversational markers (triggers Claude response, blocks execution)
#   - Raw tmux send-keys for Escape (send_to_claude doesn't handle it)
#
# USAGE:
#   ./usage_capture_prototype.sh
#   (Must run from external terminal or service, NOT from Claude directly)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$HOME/claude-autonomy-platform"
TMUX_SESSION="${TMUX_SESSION:-autonomous-claude}"

# Source send_to_claude utility for proper timing
source "$CLAP_DIR/utils/send_to_claude.sh"

echo "[USAGE_CAPTURE] Starting /usage capture prototype..." >&2

# Step 1: Send /usage command directly (no marker needed)
# NOTE: Can't use conversational markers because they trigger Claude to respond,
# creating a thinking indicator that blocks subsequent commands.
# Just send /usage directly and capture the TUI output.

echo "[USAGE_CAPTURE] Sending /usage command..." >&2
send_to_claude "/usage"

# Step 2: Wait for /usage TUI to render
# /usage shows an interactive TUI that needs time to display
echo "[USAGE_CAPTURE] Waiting for /usage TUI to render..." >&2
sleep 2

# Step 3: Capture pane output
echo "[USAGE_CAPTURE] Capturing pane content..." >&2
PANE_OUTPUT=$(tmux capture-pane -t "$TMUX_SESSION" -p -S -100)

# Step 4: Send Esc to exit the /usage TUI
echo "[USAGE_CAPTURE] Sending Esc to exit /usage TUI..." >&2
tmux send-keys -t "$TMUX_SESSION" Escape
sleep 0.5

# Step 5: Extract /usage output
# Look for the TUI section containing "Esc to exit"
echo "[USAGE_CAPTURE] Extracting /usage data..." >&2

# Extract everything from "/usage" command to "Esc to exit"
USAGE_OUTPUT=$(echo "$PANE_OUTPUT" | awk '/> \/usage/,/Esc to exit/')

if [ -z "$USAGE_OUTPUT" ]; then
    echo "[USAGE_CAPTURE] ERROR: Could not find /usage output" >&2
    echo "[USAGE_CAPTURE] Pane content:" >&2
    echo "$PANE_OUTPUT" | tail -20 >&2
    rm -f "$TEMP_MARKER"
    exit 1
fi

# Step 6: Parse TUI output to extract percentages
echo "[USAGE_CAPTURE] Raw /usage output:" >&2
echo "$USAGE_OUTPUT" >&2
echo "" >&2

# Extract percentages from the "X% used" lines
SESSION_PCT=$(echo "$USAGE_OUTPUT" | grep "Current session" -A1 | grep -oP '\d+% used' | grep -oP '\d+' || echo "unknown")
WEEK_ALL_PCT=$(echo "$USAGE_OUTPUT" | grep "Current week (all models)" -A1 | grep -oP '\d+% used' | grep -oP '\d+' || echo "unknown")
WEEK_OPUS_PCT=$(echo "$USAGE_OUTPUT" | grep "Current week (Opus)" -A1 | grep -oP '\d+% used' | grep -oP '\d+' || echo "unknown")

echo "[USAGE_CAPTURE] Parsed usage data:" >&2
echo "  Current Session: ${SESSION_PCT}%" >&2
echo "  Week (All Models): ${WEEK_ALL_PCT}%" >&2
echo "  Week (Opus): ${WEEK_OPUS_PCT}%" >&2
echo "" >&2

# Critical check for Opus quota
if [ "$WEEK_OPUS_PCT" != "unknown" ] && [ "$WEEK_OPUS_PCT" -ge 90 ]; then
    echo "[USAGE_CAPTURE] ⚠️  WARNING: Opus quota at ${WEEK_OPUS_PCT}% - approaching limit!" >&2
fi

echo "[USAGE_CAPTURE] Prototype test complete!" >&2
