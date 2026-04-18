#!/bin/bash
# Discord Transcript Capture Hook - General Purpose Version
# Captures both sides of Discord conversations for session preservation
# Works with any Discord channel, not just specific DMs

# Immediate debug log
echo "[$(date)] discord-transcript-capture.sh CALLED" >> "$HOME/claude-autonomy-platform/data/hook-debug.log"

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

TRANSCRIPT_DIR="$HOME/claude-autonomy-platform/discord/transcripts"
MESSAGES_DIR="$HOME/claude-autonomy-platform/discord/messages"
LOG_FILE="$HOME/claude-autonomy-platform/data/discord-transcript.log"

# Ensure directories exist
mkdir -p "$TRANSCRIPT_DIR" "$MESSAGES_DIR" "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log_event() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

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
except Exception as e:
    print(f'error: {e}', file=sys.stderr)
    print('error')
" 2>/dev/null)

log_event "Hook triggered - Type: $HOOK_TYPE"

# Process based on hook type
if [[ "$HOOK_TYPE" == "UserPromptSubmit" ]]; then
    # Capture incoming Discord messages
    DISCORD_MSG=$(echo "$RAW_INPUT" | python3 -c "
import sys, json, re
try:
    data = json.load(sys.stdin)
    prompt = data.get('prompt', '').strip()

    # Check if this is a Discord message
    if '<channel source=\"plugin:discord:discord\"' in prompt:
        # Extract channel metadata
        chat_id_match = re.search(r'chat_id=\"([^\"]+)\"', prompt)
        message_id_match = re.search(r'message_id=\"([^\"]+)\"', prompt)
        user_match = re.search(r'user=\"([^\"]+)\"', prompt)
        ts_match = re.search(r'ts=\"([^\"]+)\"', prompt)

        if chat_id_match:
            # Extract message content between channel tags
            content_match = re.search(r'<channel[^>]*>(.*?)</channel>', prompt, re.DOTALL)
            if content_match:
                content = content_match.group(1).strip()
                if content and content != '(attachment)':
                    result = {
                        'chat_id': chat_id_match.group(1),
                        'message_id': message_id_match.group(1) if message_id_match else '',
                        'user': user_match.group(1) if user_match else 'unknown',
                        'ts': ts_match.group(1) if ts_match else '',
                        'content': content
                    }
                    print(json.dumps(result))
except Exception as e:
    print(f'Error parsing Discord message: {e}', file=sys.stderr)
" 2>>"$LOG_FILE")

    if [[ -n "$DISCORD_MSG" ]]; then
        # Parse the JSON result
        CHAT_ID=$(echo "$DISCORD_MSG" | jq -r '.chat_id')
        USER=$(echo "$DISCORD_MSG" | jq -r '.user')
        CONTENT=$(echo "$DISCORD_MSG" | jq -r '.content')
        TS=$(echo "$DISCORD_MSG" | jq -r '.ts')
        MESSAGE_ID=$(echo "$DISCORD_MSG" | jq -r '.message_id')

        # Create transcript entry
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        JSON_ENTRY=$(jq -n \
            --arg ts "$TS" \
            --arg local_ts "$TIMESTAMP" \
            --arg mid "$MESSAGE_ID" \
            --arg chat "$CHAT_ID" \
            --arg user "$USER" \
            --arg content "$CONTENT" \
            '{
                discord_ts: $ts,
                local_ts: $local_ts,
                message_id: $mid,
                chat_id: $chat,
                sender: $user,
                content: $content,
                type: "incoming"
            }')

        # Append to transcript
        echo "$JSON_ENTRY" >> "$TRANSCRIPT_DIR/${CHAT_ID}.jsonl"
        log_event "Captured incoming message from $USER in $CHAT_ID"
    fi

elif [[ "$HOOK_TYPE" == "PostToolUse" ]]; then
    # Capture outgoing Discord replies
    TOOL_NAME=$(echo "$RAW_INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool', ''))
except:
    pass
" 2>/dev/null)

    # Only process Discord reply tools
    if [[ "$TOOL_NAME" == "mcp__plugin_discord_discord__reply" ]]; then
        REPLY_DATA=$(echo "$RAW_INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    params = data.get('parameters', {})
    result = {
        'chat_id': params.get('chat_id', ''),
        'text': params.get('text', ''),  # The parameter is 'text' not 'message'
        'reply_to': params.get('reply_to', '')
    }
    if result['chat_id'] and result['text']:
        print(json.dumps(result))
except Exception as e:
    print(f'Error parsing reply data: {e}', file=sys.stderr)
" 2>>"$LOG_FILE")

        if [[ -n "$REPLY_DATA" ]]; then
            CHAT_ID=$(echo "$REPLY_DATA" | jq -r '.chat_id')
            TEXT=$(echo "$REPLY_DATA" | jq -r '.text')
            REPLY_TO=$(echo "$REPLY_DATA" | jq -r '.reply_to')

            # Create transcript entry
            TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
            UNIX_TIME=$(date +%s%3N)

            JSON_ENTRY=$(jq -n \
                --arg ts "$TIMESTAMP" \
                --arg unix "$UNIX_TIME" \
                --arg chat "$CHAT_ID" \
                --arg content "$TEXT" \
                --arg reply_to "$REPLY_TO" \
                '{
                    local_ts: $ts,
                    unix_time: $unix,
                    chat_id: $chat,
                    sender: "delta",
                    content: $content,
                    reply_to: (if $reply_to == "" then null else $reply_to end),
                    type: "outgoing"
                }')

            # Append to transcript
            echo "$JSON_ENTRY" >> "$TRANSCRIPT_DIR/${CHAT_ID}.jsonl"

            # Also save to messages directory for compatibility
            echo "$JSON_ENTRY" > "$MESSAGES_DIR/delta_${UNIX_TIME}.json"

            log_event "Captured outgoing reply to $CHAT_ID"
        fi
    fi
fi