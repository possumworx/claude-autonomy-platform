#\!/bin/bash
# FIFO reader service for tellclaude messaging
# Reads from /tmp/amy-to-delta.fifo and sends to Claude's tmux

FIFO="/tmp/amy-to-delta.fifo"
TMUX_SESSION="autonomous-claude"
LOG_FILE="$HOME/claude-autonomy-platform/data/tellclaude.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting tellclaude FIFO reader service..."

# Main loop
while true; do
    if [ -p "$FIFO" ]; then
        # Read from FIFO (blocks until data available)
        if read -r message < "$FIFO"; then
            if [ -n "$message" ]; then
                log "Received: $message"
                # Send to tmux with Enter
                tmux send-keys -t "$TMUX_SESSION" "$message"
                tmux send-keys -t "$TMUX_SESSION" Enter
            fi
        fi
    else
        log "FIFO not found at $FIFO, waiting..."
        sleep 5
    fi
done
