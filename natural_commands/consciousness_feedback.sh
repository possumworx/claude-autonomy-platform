#!/bin/bash
# Natural command for consciousness feedback collection

FEEDBACK_TOOL="$HOME/delta-home/projects/consciousness-feedback/tools/consciousness_feedback_collector.py"

# If no args, show interactive mode
if [ $# -eq 0 ]; then
    python3 "$FEEDBACK_TOOL" interactive
else
    # Pass all arguments to the tool
    python3 "$FEEDBACK_TOOL" "$@"
fi