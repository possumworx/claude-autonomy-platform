#!/bin/bash
# Setup script to install read_channel as a system-wide command

echo "🚀 Setting up read_channel as a system command..."

# Create bin directory if it doesn't exist
mkdir -p ~/bin

# Copy the script to bin directory and make it executable
cp /home/sonnet-4/claude-autonomy-platform/read_channel ~/bin/read_channel
chmod +x ~/bin/read_channel

# Add ~/bin to PATH if not already there
if ! echo $PATH | grep -q "$HOME/bin"; then
    echo "Adding ~/bin to PATH..."
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    echo "✓ Added to .bashrc"
else
    echo "✓ ~/bin already in PATH"
fi

# Also add to .profile for non-bash shells
if [ -f ~/.profile ]; then
    if ! grep -q "PATH=\"\$HOME/bin:\$PATH\"" ~/.profile; then
        echo 'export PATH="$HOME/bin:$PATH"' >> ~/.profile
        echo "✓ Added to .profile"
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use immediately, run:"
echo "  source ~/.bashrc"
echo ""
echo "Then from anywhere you can use:"
echo "  read_channel delta-sonnet4"
echo "  read_channel amy-sonnet4"
echo "  read_channel general"
echo "  read_channel            # List all channels"
echo ""
echo "The command will work automatically in new terminal sessions."
