#!/bin/bash
# Setup Natural Command Symlinks
# This script creates symlinks in ~/bin for all commands defined in natural_commands.sh
# ensuring they're accessible in PATH for Claude Code sessions

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$(dirname "$SCRIPT_DIR")"

# Source path utilities
source "$SCRIPT_DIR/claude_paths.sh"

# Paths
NATURAL_COMMANDS="$CLAP_DIR/config/natural_commands.sh"
BIN_DIR="$HOME/bin"

echo -e "${GREEN}Setting up natural command symlinks...${NC}"

# Create ~/bin if it doesn't exist
if [ ! -d "$BIN_DIR" ]; then
    echo "Creating $BIN_DIR directory..."
    mkdir -p "$BIN_DIR"
fi

# Parse natural_commands.sh and create symlinks
echo "Parsing $NATURAL_COMMANDS..."

# Extract alias definitions and create symlinks
while IFS= read -r line; do
    # Skip comments and empty lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$line" ]] && continue
    
    # Parse alias lines: alias name='command'
    if [[ "$line" =~ ^alias[[:space:]]+([^=]+)=[\'\"]([^\'\"]+)[\'\"] ]]; then
        alias_name="${BASH_REMATCH[1]}"
        command_path="${BASH_REMATCH[2]}"
        
        # Skip if command contains shell constructs (pipes, etc)
        if [[ "$command_path" =~ [\|\;] ]]; then
            echo -e "${YELLOW}Skipping complex command: $alias_name${NC}"
            continue
        fi
        
        # Expand ~ to $HOME
        command_path="${command_path/#\~/$HOME}"
        
        # Extract just the executable path (before any arguments)
        executable_path=$(echo "$command_path" | awk '{print $1}')
        
        # Check if it's a ClAP utility
        if [[ "$executable_path" =~ claude-autonomy-platform ]]; then
            # Check if the target exists
            if [ -f "$executable_path" ]; then
                symlink_path="$BIN_DIR/$alias_name"
                
                # Create or update symlink
                if [ -L "$symlink_path" ]; then
                    # Remove existing symlink
                    rm "$symlink_path"
                    echo "Updating symlink: $alias_name"
                else
                    echo "Creating symlink: $alias_name"
                fi
                
                ln -s "$executable_path" "$symlink_path"
            else
                echo -e "${YELLOW}Warning: Target not found for $alias_name: $executable_path${NC}"
            fi
        else
            echo -e "${YELLOW}Skipping non-ClAP command: $alias_name${NC}"
        fi
    fi
done < "$NATURAL_COMMANDS"

echo -e "${GREEN}✓ Natural command symlinks setup complete!${NC}"
echo ""
echo "The following commands are now available in PATH:"
ls -la "$BIN_DIR" | grep -- '->' | grep 'claude-autonomy-platform' | awk '{print "  " $9}'