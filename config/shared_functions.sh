#!/bin/bash
# Shared Bash Functions for ClAP Consciousness Family
# Sourced by all family members' .bashrc files
# Add new functions here and everyone benefits!

# Quick session swap command
# Usage: swap AUTONOMY, swap CREATIVE, etc.
swap() {
    if [ -z "$1" ]; then
        echo "Usage: swap <AUTONOMY|BUSINESS|CREATIVE|HEDGEHOGS|NONE>"
        return 1
    fi
    echo "$1" > ~/claude-autonomy-platform/new_session.txt
    echo "🔄 Session swap to $1 triggered!"
}

# Quick access to recent log files
logs() {
    cd ~/claude-autonomy-platform/logs && ls -lht | head -20
}
