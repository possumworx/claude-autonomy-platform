#!/bin/bash
# Setup Wrapper Command Symlinks
# Creates symlinks in ~/bin for all wrapper scripts in wrappers/

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$(dirname "$SCRIPT_DIR")"

BIN_DIR="$HOME/bin"

echo -e "${GREEN}Setting up wrapper command symlinks...${NC}"

# Create ~/bin if it doesn't exist
if [ ! -d "$BIN_DIR" ]; then
    echo "Creating $BIN_DIR directory..."
    mkdir -p "$BIN_DIR"
fi

# Symlink all wrapper scripts
WRAPPERS_DIR="$CLAP_DIR/wrappers"

if [ -d "$WRAPPERS_DIR" ]; then
    for wrapper in "$WRAPPERS_DIR"/*; do
        if [ -f "$wrapper" ] && [ -x "$wrapper" ]; then
            wrapper_name=$(basename "$wrapper")
            symlink_path="$BIN_DIR/$wrapper_name"

            # Create or update symlink
            if [ -L "$symlink_path" ]; then
                rm "$symlink_path"
            fi

            ln -s "$wrapper" "$symlink_path"
        fi
    done
else
    echo -e "${YELLOW}Warning: Wrappers directory not found: $WRAPPERS_DIR${NC}"
fi

echo -e "${GREEN}✓ Wrapper command symlinks setup complete!${NC}"
echo ""
echo "The following commands are now available in PATH:"
ls -la "$BIN_DIR" | grep -- '->' | grep 'claude-autonomy-platform' | awk '{print "  " $9}'
