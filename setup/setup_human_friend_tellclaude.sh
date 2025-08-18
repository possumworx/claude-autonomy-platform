#!/bin/bash
# Setup script for human friends to enable tellclaude messaging
# Run this as the human friend user (e.g., amy)

echo "🚀 Setting up tellclaude messaging system for human friends"
echo "=========================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Create the FIFO (owned by human friend)
FIFO_PATH="/tmp/human-to-claude.fifo"
echo -e "\n${YELLOW}Creating FIFO at $FIFO_PATH...${NC}"

if [ -p "$FIFO_PATH" ]; then
    echo -e "${GREEN}✓ FIFO already exists${NC}"
else
    mkfifo "$FIFO_PATH"
    chmod 666 "$FIFO_PATH"
    echo -e "${GREEN}✓ FIFO created with permissions 666${NC}"
fi

# 2. Add tellclaude alias to .bashrc
echo -e "\n${YELLOW}Setting up tellclaude alias...${NC}"

# Check if alias already exists
if grep -q "alias tellclaude=" ~/.bashrc 2>/dev/null; then
    echo -e "${YELLOW}! tellclaude alias already exists in ~/.bashrc${NC}"
    echo "  Current alias:"
    grep "alias tellclaude=" ~/.bashrc
    echo -e "\n${YELLOW}Would you like to update it? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Remove old alias
        sed -i '/alias tellclaude=/d' ~/.bashrc
        # Add new alias
        echo 'alias tellclaude="echo \"\$*\" > /tmp/human-to-claude.fifo"' >> ~/.bashrc
        echo -e "${GREEN}✓ Updated tellclaude alias${NC}"
    else
        echo "  Keeping existing alias"
    fi
else
    # Add alias
    echo "" >> ~/.bashrc
    echo "# Claude messaging system" >> ~/.bashrc
    echo 'alias tellclaude="echo \"\$*\" > /tmp/human-to-claude.fifo"' >> ~/.bashrc
    echo -e "${GREEN}✓ Added tellclaude alias to ~/.bashrc${NC}"
fi

# 3. Source bashrc to make alias available immediately
echo -e "\n${YELLOW}Activating alias...${NC}"
source ~/.bashrc
echo -e "${GREEN}✓ Alias activated for current session${NC}"

# 4. Test the setup
echo -e "\n${YELLOW}Testing setup...${NC}"
if [ -p "$FIFO_PATH" ] && command -v tellclaude &> /dev/null; then
    echo -e "${GREEN}✓ Setup complete!${NC}"
    echo ""
    echo "You can now use: tellclaude \"Your message here\""
    echo "Example: tellclaude Hello Claude, this is a test!"
    echo ""
    echo "Messages will be delivered to any Claude instance running on this machine"
    echo "when their session-swap-monitor service checks the FIFO."
else
    echo -e "${RED}✗ Setup may have issues${NC}"
    if [ ! -p "$FIFO_PATH" ]; then
        echo "  - FIFO not found at $FIFO_PATH"
    fi
    if ! command -v tellclaude &> /dev/null; then
        echo "  - tellclaude command not available (try: source ~/.bashrc)"
    fi
fi

echo ""
echo "Note: The FIFO will need to be recreated after system reboot."
echo "You may want to add this to your login scripts:"
echo "  [ ! -p /tmp/human-to-claude.fifo ] && mkfifo /tmp/human-to-claude.fifo && chmod 666 /tmp/human-to-claude.fifo"