#\!/bin/bash
# Read from human friend's FIFO and send to Claude's tmux session

FIFO="/tmp/human-to-claude.fifo"
TMUX_SESSION="autonomous-claude"

echo "Starting FIFO reader for $FIFO..."

while true; do
    if [ -p "$FIFO" ]; then
        # Read from FIFO (this blocks until data is available)
        if read -r message < "$FIFO"; then
            if [ -n "$message" ]; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] Received: $message"
                # Send to tmux then send Enter separately
                tmux send-keys -t "$TMUX_SESSION" "$message"
                tmux send-keys -t "$TMUX_SESSION" Enter
            fi
        fi
    else
        echo "FIFO not found at $FIFO, waiting..."
        sleep 5
    fi
done
