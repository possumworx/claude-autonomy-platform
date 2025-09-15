#!/bin/bash
# Source both natural and personal commands for Claude sessions

# Source natural commands
if [ -f ~/claude-autonomy-platform/config/natural_commands.sh ]; then
    source ~/claude-autonomy-platform/config/natural_commands.sh
fi

# Source personal commands
if [ -f ~/claude-autonomy-platform/config/personal_commands.sh ]; then
    source ~/claude-autonomy-platform/config/personal_commands.sh
fi