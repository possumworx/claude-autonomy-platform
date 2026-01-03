#!/bin/bash

# Xvfb Display Cleanup Script
# Keeps :0 (real desktop) and current Discord MCP display, kills others

set -e

# Get current user's UID for proper path construction
USER_ID=$(id -u)
LOGFILE="/home/$(whoami)/claude-autonomy-platform/logs/xvfb_cleanup.log"

# Ensure logs directory exists
mkdir -p "$(dirname "$LOGFILE")"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGFILE"
}

log "Starting Xvfb display cleanup"

# Find all Xvfb processes
XVFB_PROCESSES=$(ps aux | grep Xvfb | grep -v grep || true)

if [ -z "$XVFB_PROCESSES" ]; then
    log "No Xvfb processes found"
    exit 0
fi

log "Found Xvfb processes:"
echo "$XVFB_PROCESSES" >> "$LOGFILE"

# Find which display the Discord MCP is using
DISCORD_DISPLAY=""
if pgrep -f "xvfb-run.*discord" > /dev/null; then
    # Find the xvfb-run process that started Discord MCP
    XVFB_RUN_PID=$(pgrep -f "xvfb-run.*discord" | head -1)
    if [ -n "$XVFB_RUN_PID" ]; then
        # Find the Xvfb child process
        XVFB_CHILD=$(pgrep -P "$XVFB_RUN_PID" | grep -E '^[0-9]+$' | head -1)
        if [ -n "$XVFB_CHILD" ]; then
            # Get the display from the Xvfb command line
            XVFB_CMD=$(ps -p "$XVFB_CHILD" -o cmd= 2>/dev/null || true)
            if [ -n "$XVFB_CMD" ]; then
                DISCORD_DISPLAY=$(echo "$XVFB_CMD" | grep -o ':[0-9]\+' | head -1)
                log "Discord MCP using display: $DISCORD_DISPLAY (via xvfb-run PID $XVFB_RUN_PID)"
            fi
        fi
    fi
fi

# Find displays to keep (:0 and Discord MCP display)
KEEP_DISPLAYS=":0"
if [ -n "$DISCORD_DISPLAY" ]; then
    KEEP_DISPLAYS="$KEEP_DISPLAYS $DISCORD_DISPLAY"
fi

log "Keeping displays: $KEEP_DISPLAYS"

# Kill Xvfb processes not in keep list
echo "$XVFB_PROCESSES" | while read -r line; do
    if [ -z "$line" ]; then
        continue
    fi
    
    # Extract display number from Xvfb command line
    DISPLAY_NUM=$(echo "$line" | awk '{for(i=1;i<=NF;i++) if($i ~ /^:[0-9]+$/) print $i}')
    PID=$(echo "$line" | awk '{print $2}')
    
    if [ -n "$DISPLAY_NUM" ]; then
        SHOULD_KILL=true
        for KEEP in $KEEP_DISPLAYS; do
            if [ "$DISPLAY_NUM" = "$KEEP" ]; then
                SHOULD_KILL=false
                break
            fi
        done
        
        if [ "$SHOULD_KILL" = true ]; then
            if [ "${DRY_RUN:-false}" = "true" ]; then
                log "DRY RUN: Would kill Xvfb process $PID on display $DISPLAY_NUM"
            else
                # Double-check process still exists and is actually Xvfb
                if ps -p "$PID" | grep -q Xvfb; then
                    log "Killing Xvfb process $PID on display $DISPLAY_NUM"
                    kill "$PID" 2>/dev/null || log "Failed to kill process $PID"
                else
                    log "Process $PID no longer exists or is not Xvfb, skipping"
                fi
            fi
        else
            log "Keeping Xvfb process $PID on display $DISPLAY_NUM"
        fi
    fi
done

log "Xvfb cleanup completed"