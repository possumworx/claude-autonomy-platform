#!/bin/bash
# Fix natural command symlinks in ~/bin

BIN_DIR="$HOME/bin"
CLAP_DIR="$HOME/claude-autonomy-platform"

# Remove any existing symlinks pointing to natural_commands.sh
find "$BIN_DIR" -type l -lname "*natural_commands.sh" -delete

# Create correct symlinks for actual scripts
# Core System Management
ln -sf "$CLAP_DIR/utils/session_swap.sh" "$BIN_DIR/swap"
ln -sf "$CLAP_DIR/utils/check_health" "$BIN_DIR/check_health"

# Discord Communication
ln -sf "$CLAP_DIR/discord/read_channel" "$BIN_DIR/read_channel"
ln -sf "$CLAP_DIR/discord/write_channel" "$BIN_DIR/write_channel"
ln -sf "$CLAP_DIR/discord/edit_message" "$BIN_DIR/edit_message"
ln -sf "$CLAP_DIR/discord/delete_message" "$BIN_DIR/delete_message"
ln -sf "$CLAP_DIR/discord/add_reaction" "$BIN_DIR/add_reaction"
ln -sf "$CLAP_DIR/discord/edit_status" "$BIN_DIR/edit_status"
ln -sf "$CLAP_DIR/discord/send_image" "$BIN_DIR/send_image"
ln -sf "$CLAP_DIR/discord/send_file" "$BIN_DIR/send_file"
ln -sf "$CLAP_DIR/discord/fetch_image" "$BIN_DIR/fetch_image"

# System Update Helper
ln -sf "$CLAP_DIR/utils/update_system.sh" "$BIN_DIR/update"

# Note: Commands that are just shell commands (cd, git status, grep, etc) 
# cannot be symlinked and must remain as aliases in .bashrc

echo "✅ Fixed symlinks for all script-based natural commands"
echo "ℹ️  Shell command aliases (clap, home, gs, gd, gl, etc) work via .bashrc sourcing"