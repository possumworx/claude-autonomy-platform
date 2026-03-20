#!/bin/bash
# Write status line JSON to disk for monitoring scripts to consume.
# Also echoes a minimal status line in case anyone's watching.
CLAP_DIR="$HOME/claude-autonomy-platform"
input=$(cat)
echo "$input" > "$CLAP_DIR/data/statusline_data.json"

# Read emoji from config (fall back to ●)
EMOJI=$(grep '^SESSION_EMOJI=' "$CLAP_DIR/config/claude_infrastructure_config.txt" 2>/dev/null | cut -d= -f2)
EMOJI="${EMOJI:-●}"

# Minimal display (python3 instead of jq — jq not installed)
echo "$input" | python3 -c "
import json, sys
emoji = '$EMOJI'
d = json.load(sys.stdin)
model = d.get('model', {}).get('display_name', '?')
pct = int(d.get('context_window', {}).get('used_percentage', 0) or 0)
style = d.get('output_style', {}).get('name', '?')
border = (emoji + ' ') * 8
print(f'{border}[{model}] {pct}% context | style: {style} {border}')
"
