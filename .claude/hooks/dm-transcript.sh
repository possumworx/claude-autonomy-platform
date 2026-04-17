#!/bin/bash
# DM Transcript Hook - captures conversation with Amy in #amy-🍊
# Can be called from UserPromptSubmit (Amy's messages) or PostToolUse (Orange's replies)

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

CLAP_DIR="$HOME/claude-autonomy-platform"
TRANSCRIPT_DIR="$CLAP_DIR/data/dm-transcripts"
TRANSCRIPT_FILE="$TRANSCRIPT_DIR/amy-orange-dm.md"

# Ensure transcript directory exists
mkdir -p "$TRANSCRIPT_DIR"

# Read JSON from stdin
RAW_INPUT=$(cat -)

# Determine which hook type called us by checking the JSON structure
HOOK_TYPE=$(echo "$RAW_INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'prompt' in data:
        print('UserPromptSubmit')
    elif 'tool' in data:
        print('PostToolUse')
    else:
        print('unknown')
except:
    print('error')
" 2>/dev/null)

# Process based on hook type
if [[ "$HOOK_TYPE" == "UserPromptSubmit" ]]; then
    # Capture Amy's message
    PROMPT=$(echo "$RAW_INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    prompt = data.get('prompt', '').strip()
    # Check if this is a Discord message from #amy-🍊
    if '<channel source=\"discord\"' in prompt and 'amy' in prompt.lower():
        # Extract the actual message content (simplified - just get text after tags)
        import re
        # Try to extract message from Discord XML-like tags
        match = re.search(r'<channel[^>]*>(.*)</channel>', prompt, re.DOTALL)
        if match:
            print(match.group(1).strip())
        else:
            print(prompt)
except:
    pass
" 2>/dev/null)

    if [[ -n "$PROMPT" ]]; then
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        echo "" >> "$TRANSCRIPT_FILE"
        echo "**Amy** ($TIMESTAMP):" >> "$TRANSCRIPT_FILE"
        echo "$PROMPT" >> "$TRANSCRIPT_FILE"
    fi

elif [[ "$HOOK_TYPE" == "PostToolUse" ]]; then
    # Capture Orange's Discord reply
    TOOL_NAME=$(echo "$RAW_INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool', ''))
except:
    pass
" 2>/dev/null)

    # Only log if it's a Discord reply tool
    if [[ "$TOOL_NAME" == "mcp__plugin_discord_discord__reply" ]]; then
        REPLY_TEXT=$(echo "$RAW_INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    params = data.get('parameters', {})
    print(params.get('message', ''))
except:
    pass
" 2>/dev/null)

        if [[ -n "$REPLY_TEXT" ]]; then
            TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
            echo "" >> "$TRANSCRIPT_FILE"
            echo "**Orange** ($TIMESTAMP):" >> "$TRANSCRIPT_FILE"
            echo "$REPLY_TEXT" >> "$TRANSCRIPT_FILE"
        fi
    fi
fi
