#!/bin/bash
# Hook script triggered on PostToolUse for Write
# Checks if the file is new_session.txt, and if so, exports the transcript

CLAP_DIR="$HOME/claude-autonomy-platform"
LOG_FILE="$CLAP_DIR/logs/hook_export.log"

# Read JSON input from stdin and extract file_path using Python (jq not always available)
FILE_PATH=$(python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('file_path', ''))
except:
    print('')
")

# Log the hook trigger
echo "[$(date -Iseconds)] Hook triggered for file: $FILE_PATH" >> "$LOG_FILE"

# Check if this is a write to new_session.txt
if [[ "$FILE_PATH" == */new_session.txt ]] || [[ "$FILE_PATH" == *new_session.txt ]]; then
    echo "[$(date -Iseconds)] Detected session swap trigger, exporting transcript..." >> "$LOG_FILE"

    # Run the export script
    "$CLAP_DIR/utils/export_transcript.py" >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "[$(date -Iseconds)] Transcript export successful" >> "$LOG_FILE"
    else
        echo "[$(date -Iseconds)] Transcript export FAILED" >> "$LOG_FILE"
    fi
fi

exit 0
