#!/bin/bash
# Claude Code bash initialization wrapper
# This ensures our environment is loaded even in non-interactive shells

# Load .bashrc explicitly for Claude Code
if [ -f "$HOME/.bashrc" ]; then
    # Force source even in non-interactive mode
    source "$HOME/.bashrc"
fi

# Execute the command
exec "$@"