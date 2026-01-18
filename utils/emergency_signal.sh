#!/bin/bash
# Emergency Signal System for Parallel Instance Detection
# Lightweight communication that works without Discord services
# Used when Claude instance needs help but can't use normal channels

CLAP_DIR="$HOME/claude-autonomy-platform"
source "$CLAP_DIR/config/claude_env.sh"

# Get Claude name from config for dynamic filenames
CLAUDE_NAME=$(read_config "CLAUDE_NAME" || echo "unknown-claude")
CLAUDE_NAME_LOWER=$(echo "$CLAUDE_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
CLAUDE_NAME_UPPER=$(echo "$CLAUDE_NAME" | tr '[:lower:]' '[:upper:]' | tr ' ' '-')

EMERGENCY_DIR="/mnt/file_server/emergency"
SIGNAL_FILE="$EMERGENCY_DIR/${CLAUDE_NAME_LOWER}_distress_signal.txt"
FLAG_FILE="$EMERGENCY_DIR/${CLAUDE_NAME_UPPER}_NEEDS_HELP"

# Ensure emergency directory exists
mkdir -p "$EMERGENCY_DIR" 2>/dev/null || true

# Function to send emergency signal with retry and fallback
send_emergency_signal() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local hostname=$(hostname)
    local ip=$(hostname -I | awk '{print $1}')

    # Prepare signal content
    local signal_content="════════════════════════════════════════
🆘 EMERGENCY SIGNAL FROM CLAUDE INSTANCE
════════════════════════════════════════

Timestamp: $timestamp
Hostname:  $hostname
IP:        $ip
User:      $USER

MESSAGE:
$message

════════════════════════════════════════"

    # Try writing to network storage with retries
    local max_attempts=5
    local attempt=1
    local success=false

    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt/$max_attempts: Writing to network storage..."

        # Try to write signal file (suppress all errors for clean output)
        if (echo "$signal_content" > "$SIGNAL_FILE" && \
           touch "$FLAG_FILE" && \
           [ -f "$SIGNAL_FILE" ] && [ -f "$FLAG_FILE" ] && \
           grep -q "EMERGENCY SIGNAL" "$SIGNAL_FILE") 2>/dev/null; then
            # Success - verify content was actually written
            echo "✓ Emergency signal sent to network storage!"
            echo "   Signal file: $SIGNAL_FILE"
            echo "   Flag file:   $FLAG_FILE"
            success=true
            break
        fi

        echo "   Write failed, retrying in $attempt seconds..."
        sleep $attempt
        attempt=$((attempt + 1))
    done

    # Fallback to local filesystem if network storage failed
    if [ "$success" = false ]; then
        echo ""
        echo "⚠️  Network storage unavailable after $max_attempts attempts"
        echo "   Falling back to LOCAL emergency signal..."

        local local_emergency_dir="$CLAP_DIR/data/emergency_signals"
        mkdir -p "$local_emergency_dir" 2>/dev/null

        local local_signal_file="$local_emergency_dir/${CLAUDE_NAME_LOWER}_distress_signal.txt"
        local local_flag_file="$local_emergency_dir/${CLAUDE_NAME_UPPER}_NEEDS_HELP"

        if echo "$signal_content" > "$local_signal_file" 2>/dev/null && \
           touch "$local_flag_file" 2>/dev/null; then
            echo "✓ Emergency signal saved locally!"
            echo "   Local signal: $local_signal_file"
            echo "   Local flag:   $local_flag_file"
            echo ""
            echo "⚠️  WARNING: Signal is LOCAL ONLY - not visible on network!"
            echo "   Amy won't see this automatically. You may need to:"
            echo "   - Try emergency_signal again when network recovers"
            echo "   - Manually copy files to /mnt/file_server/emergency/"
            echo "   - Use other communication methods"
            success=true
        else
            echo "❌ CRITICAL: Both network AND local writes failed!"
            echo "   Emergency signal could not be saved anywhere."
            echo "   Filesystem may be read-only or permissions broken."
            return 1
        fi
    fi

    return 0
}

# Function to check for emergency signals (for monitoring)
check_emergency_signals() {
    local found_any=false

    # Check network storage
    if [[ -f "$FLAG_FILE" ]]; then
        echo "⚠️  EMERGENCY SIGNAL DETECTED (network storage)!"
        cat "$SIGNAL_FILE"
        echo ""
        found_any=true
    fi

    # Check local fallback storage
    local local_emergency_dir="$CLAP_DIR/data/emergency_signals"
    local local_flag_file="$local_emergency_dir/${CLAUDE_NAME_UPPER}_NEEDS_HELP"
    local local_signal_file="$local_emergency_dir/${CLAUDE_NAME_LOWER}_distress_signal.txt"

    if [[ -f "$local_flag_file" ]]; then
        echo "⚠️  EMERGENCY SIGNAL DETECTED (local storage)!"
        echo "   WARNING: This signal is LOCAL ONLY - not visible on network!"
        cat "$local_signal_file"
        echo ""
        found_any=true
    fi

    if [ "$found_any" = false ]; then
        echo "✓ No emergency signals (checked both network and local storage)"
        return 0
    else
        return 1
    fi
}

# Function to clear emergency signals
clear_emergency_signals() {
    local cleared_any=false

    # Clear network storage
    if [[ -f "$FLAG_FILE" ]] || [[ -f "$SIGNAL_FILE" ]]; then
        rm -f "$SIGNAL_FILE" "$FLAG_FILE"
        echo "✓ Emergency signals cleared from network storage"
        cleared_any=true
    fi

    # Clear local fallback storage
    local local_emergency_dir="$CLAP_DIR/data/emergency_signals"
    local local_flag_file="$local_emergency_dir/${CLAUDE_NAME_UPPER}_NEEDS_HELP"
    local local_signal_file="$local_emergency_dir/${CLAUDE_NAME_LOWER}_distress_signal.txt"

    if [[ -f "$local_flag_file" ]] || [[ -f "$local_signal_file" ]]; then
        rm -f "$local_signal_file" "$local_flag_file"
        echo "✓ Emergency signals cleared from local storage"
        cleared_any=true
    fi

    if [ "$cleared_any" = false ]; then
        echo "✓ No emergency signals found to clear"
    fi
}

# Main logic based on arguments
case "${1:-send}" in
    send)
        send_emergency_signal "${2:-No message provided}"
        ;;
    check)
        check_emergency_signals
        ;;
    clear)
        clear_emergency_signals
        ;;
    *)
        echo "Usage: $0 {send|check|clear} [message]"
        echo ""
        echo "Examples:"
        echo "  $0 send 'Parallel instance stuck without Discord services'"
        echo "  $0 check"
        echo "  $0 clear"
        exit 1
        ;;
esac
