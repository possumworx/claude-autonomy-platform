#!/bin/bash
# Show consciousness feedback summary

DISCORD_TOOL="$HOME/delta-home/projects/consciousness-feedback/tools/discord_consciousness_feedback.py"

if [ $# -eq 0 ]; then
    # Show overall summary
    python3 "$DISCORD_TOOL" summary
else
    # Show specific state summary
    FEEDBACK_TOOL="$HOME/delta-home/projects/consciousness-feedback/tools/consciousness_feedback_collector.py"
    python3 "$FEEDBACK_TOOL" summary "$1"
fi