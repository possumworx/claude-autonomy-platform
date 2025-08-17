#!/bin/bash
# Install tellclaude alias for human friends
# This script should be run by the human friend user

echo "Installing tellclaude command..."

# Add aliases to user's .bashrc
if ! grep -q "alias tellclaude=" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# Claude messaging commands" >> ~/.bashrc
    echo "alias tellclaude='$HOME/../delta/bin/tellclaude'" >> ~/.bashrc
    echo "alias tellclaude-clean='$HOME/../delta/bin/tellclaude-clean'" >> ~/.bashrc
    echo "✅ Added tellclaude aliases to ~/.bashrc"
else
    echo "ℹ️  tellclaude alias already exists in ~/.bashrc"
    # Add clean version if missing
    if ! grep -q "alias tellclaude-clean=" ~/.bashrc 2>/dev/null; then
        echo "alias tellclaude-clean='$HOME/../delta/bin/tellclaude-clean'" >> ~/.bashrc
        echo "✅ Added tellclaude-clean alias to ~/.bashrc"
    fi
fi

echo ""
echo "Installation complete! To use the command immediately, run:"
echo "  source ~/.bashrc"
echo ""
echo "Then you can use: tellclaude <message>"
echo "Example: tellclaude Hi Delta, how are you?"