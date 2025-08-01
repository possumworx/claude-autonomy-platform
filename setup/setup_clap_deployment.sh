#!/bin/bash
# Claude Autonomy Platform (ClAP) - Complete Deployment Setup Script
# This script sets up a complete ClAP deployment on a new machine
# 
# Usage: ./setup_clap_deployment.sh [--config-file /path/to/config]
#
# MAINTAINER: Claude Opus 4 Delta (opus4delta@gmail.com)
# This installer is maintained by Delta to ensure consistency and compatibility.
# If you need changes to the installer, please create a Linear issue assigned to Delta
# with full details of what needs to be changed and why.
# Last major merge: August 2025 (combined Sonnet and Delta improvements)

set -e

echo "🚀 Claude Autonomy Platform (ClAP) - Deployment Setup"
echo "===================================================="
echo ""

# Handle command line arguments
CONFIG_SOURCE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --config-file)
            CONFIG_SOURCE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--config-file /path/to/config]"
            echo ""
            echo "Options:"
            echo "  --config-file PATH    Copy infrastructure config from specified file"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Use existing config"
            echo "  $0 --config-file ~/claude-configs/claude-v2-config.txt"
            echo "  $0 --config-file /tmp/claude-infrastructure-config.txt"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Get the directory where this script is located (setup/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the ClAP root directory (parent of setup/)
CLAP_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$CLAP_DIR/config"

echo "📁 ClAP Directory: $CLAP_DIR"

# Step 0a: Ensure all scripts are executable (POSS-92)
echo "🔧 Step 0a: Ensuring all scripts have executable permissions..."

# Fix permissions on all shell scripts as a fallback for git permission issues
find "$CLAP_DIR" -name "*.sh" -type f -exec chmod +x {} \;
chmod +x "$CLAP_DIR/utils/check_health" 2>/dev/null || true
chmod +x "$CLAP_DIR/discord/read_channel" 2>/dev/null || true

# Make Python scripts with shebang executable
for file in $(find "$CLAP_DIR" -name "*.py" -type f); do
    if head -n 1 "$file" | grep -q "^#!/usr/bin/env python3"; then
        chmod +x "$file"
    fi
done 2>/dev/null || true

echo "   ✅ Script permissions fixed"
echo ""

# Step 0b: Import configuration file if specified
if [[ -n "$CONFIG_SOURCE" ]]; then
    echo "📋 Step 0: Importing configuration file..."
    
    if [[ ! -f "$CONFIG_SOURCE" ]]; then
        echo "❌ Configuration file not found: $CONFIG_SOURCE"
        exit 1
    fi
    
    echo "   Copying config from: $CONFIG_SOURCE"
    mkdir -p "$CONFIG_DIR"
    cp "$CONFIG_SOURCE" "$CONFIG_DIR/claude_infrastructure_config.txt"
    
    # Fix Windows line endings if present (POSS-75)
    echo "   Fixing line endings..."
    sed -i 's/\r$//' "$CONFIG_DIR/claude_infrastructure_config.txt"
    
    echo "   ✅ Configuration file imported"
    echo ""
elif [[ ! -f "$CONFIG_DIR/claude_infrastructure_config.txt" ]]; then
    echo "❌ No configuration file found!"
    echo ""
    if [[ -f "$CONFIG_DIR/claude_infrastructure_config.template.txt" ]]; then
        echo "📋 Template file found. You can:"
        echo "1. Copy template and edit: cp $CONFIG_DIR/claude_infrastructure_config.template.txt $CONFIG_DIR/claude_infrastructure_config.txt"
        echo "2. Use --config-file option to import existing config"
        echo ""
        echo "Examples:"
        echo "  cp $CONFIG_DIR/claude_infrastructure_config.template.txt $CONFIG_DIR/claude_infrastructure_config.txt"
        echo "  nano $CONFIG_DIR/claude_infrastructure_config.txt  # Edit with your credentials"
        echo "  $0  # Run setup"
        echo ""
        echo "  OR"
        echo ""
        echo "  $0 --config-file ~/claude-configs/claude-v2-config.txt"
    else
        echo "Please either:"
        echo "1. Copy your infrastructure config to: $CONFIG_DIR/claude_infrastructure_config.txt"
        echo "2. Use --config-file option to specify config location"
        echo ""
        echo "Example: $0 --config-file ~/claude-configs/claude-v2-config.txt"
    fi
    exit 1
fi

# Load path utilities (if claude_env.sh exists)
if [[ -f "$CONFIG_DIR/claude_env.sh" ]]; then
    source "$CONFIG_DIR/claude_env.sh"
else
    # Set basic environment if claude_env.sh doesn't exist yet
    export CLAUDE_USER=$(whoami)
    export CLAUDE_HOME=$(eval echo ~$CLAUDE_USER)
    export CLAP_DIR="$CLAP_DIR"
    export AUTONOMY_DIR="$CLAP_DIR"
fi

echo "🔧 Configuration:"
echo "  User: $CLAUDE_USER"
echo "  Home: $CLAUDE_HOME"
echo "  ClAP: $CLAP_DIR"
echo ""

# Function to read values from infrastructure config
read_config() {
    local key="$1"
    local config_file="$CONFIG_DIR/claude_infrastructure_config.txt"
    
    if [[ -f "$config_file" ]]; then
        grep "^${key}=" "$config_file" | cut -d'=' -f2-
    fi
}

# Step 1: Fix line endings from Windows cloning (POSS-144)
echo "🔧 Step 1: Fixing line endings..."

echo "   Checking for Windows CRLF line endings..."
# Check if any script files have CRLF endings
if find "$CLAP_DIR" -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.txt" -o -name "*.md" | xargs grep -l $'\r' 2>/dev/null | head -1 >/dev/null; then
    echo "   🔄 Converting CRLF to LF endings (Windows → Linux)..."
    
    # Convert line endings for all text files
    find "$CLAP_DIR" \( -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.txt" -o -name "*.md" -o -name "*.conf" -o -name "*.service" \) -exec sed -i 's/\r$//' {} \;
    
    # Also fix any files that might not have extensions but are scripts
    find "$CLAP_DIR" -type f -executable -exec sed -i 's/\r$//' {} \;
    
    echo "   ✅ Line endings converted to Unix format"
else
    echo "   ✅ Line endings already correct"
fi

# Step 2: Validate infrastructure config
echo "📝 Step 2: Validating infrastructure config..."
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)
CONFIG_USER=$(read_config 'LINUX_USER')

# Warn if there's a mismatch but don't auto-fix
if [[ "$CURRENT_USER" != "$CONFIG_USER" ]]; then
    echo "   ⚠️  WARNING: Current user ($CURRENT_USER) differs from config user ($CONFIG_USER)"
    echo "   This script should be run as the target Claude user or config should be updated manually"
fi

# Step 3: Set up systemd service files
echo "⚙️  Step 3: Setting up systemd service files..."
SYSTEMD_USER_DIR="$CLAUDE_HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

# Copy service files from services/ directory (Sonnet's approach - no %i substitution)
echo "   Copying service files..."
for service in autonomous-timer.service session-bridge-monitor.service session-swap-monitor.service channel-monitor.service; do
    if [[ -f "$CLAP_DIR/services/$service" ]]; then
        cp "$CLAP_DIR/services/$service" "$SYSTEMD_USER_DIR/"
        echo "   ✅ $service"
    else
        echo "   ❌ $service not found in services/ directory"
    fi
done

echo "   ✅ Systemd service files created"

# Generate systemd-compatible environment file (POSS-119)
echo "   Creating systemd-compatible environment file..."
if [[ -f "$CLAP_DIR/utils/create_systemd_env.py" ]]; then
    echo "   Generating systemd-compatible environment file..."
    python3 "$CLAP_DIR/utils/create_systemd_env.py"
    
    # Verify the environment file was created successfully
    if [[ -f "$CONFIG_DIR/claude.env" ]] && [[ -s "$CONFIG_DIR/claude.env" ]]; then
        echo "   ✅ Systemd environment file created successfully"
        
        # Validate critical variables exist
        if grep -q "CLAUDE_USER=" "$CONFIG_DIR/claude.env" && \
           grep -q "CLAP_DIR=" "$CONFIG_DIR/claude.env"; then
            echo "   ✅ Environment file validation passed"
        else
            echo "   ⚠️  Warning: Environment file missing critical variables"
        fi
    else
        echo "   ❌ Environment file creation failed - file missing or empty"
        echo "   This may cause service startup issues"
    fi
else
    echo "   ⚠️  Warning: create_systemd_env.py not found"
    echo "   Services may not start properly without environment variables"
fi

# Step 4: Set up persistent environment variables
echo "🌍 Step 4: Setting up persistent environment variables..."

# Add to .bashrc if not already present
BASHRC="$CLAUDE_HOME/.bashrc"
ENV_SETUP_LINE="source $CONFIG_DIR/claude_env.sh"

if ! grep -q "$ENV_SETUP_LINE" "$BASHRC" 2>/dev/null; then
    echo "" >> "$BASHRC"
    echo "# Claude Autonomy Platform environment" >> "$BASHRC"
    echo "$ENV_SETUP_LINE" >> "$BASHRC"
    echo "   ✅ Added environment setup to .bashrc"
else
    echo "   ✅ Environment setup already in .bashrc"
fi

# Set up ~/bin directory and management utilities (POSS-120) - Delta's addition
echo "   Setting up management utilities in PATH..."
BIN_DIR="$CLAUDE_HOME/bin"
mkdir -p "$BIN_DIR"

# Add ~/bin to PATH if not already present
BIN_PATH_LINE="export PATH=\$HOME/bin:\$PATH"
if ! grep -q "HOME/bin" "$BASHRC" 2>/dev/null; then
    echo "# Add ~/bin to PATH for ClAP management utilities" >> "$BASHRC"  
    echo "$BIN_PATH_LINE" >> "$BASHRC"
    echo "   ✅ Added ~/bin to PATH in .bashrc"
    # Export for current session
    export PATH="$HOME/bin:$PATH"
else
    echo "   ✅ ~/bin already in PATH"
fi

# Create symlinks for management utilities - Delta's comprehensive list
echo "   Creating symlinks for management utilities..."

# Service management
if [[ -f "$CLAP_DIR/utils/claude_services.sh" ]]; then
    chmod +x "$CLAP_DIR/utils/claude_services.sh"
    ln -sf "$CLAP_DIR/utils/claude_services.sh" "$BIN_DIR/claude_services"
    echo "   ✅ claude_services -> claude_services.sh"
fi

# Display cleanup
if [[ -f "$CLAP_DIR/utils/cleanup_xvfb_displays.sh" ]]; then
    chmod +x "$CLAP_DIR/utils/cleanup_xvfb_displays.sh"
    ln -sf "$CLAP_DIR/utils/cleanup_xvfb_displays.sh" "$BIN_DIR/cleanup_displays"
    echo "   ✅ cleanup_displays -> cleanup_xvfb_displays.sh"
fi

# Terminal interaction
if [[ -f "$CLAP_DIR/utils/send_to_terminal.sh" ]]; then
    chmod +x "$CLAP_DIR/utils/send_to_terminal.sh"
    ln -sf "$CLAP_DIR/utils/send_to_terminal.sh" "$BIN_DIR/send_to_terminal"
    echo "   ✅ send_to_terminal -> send_to_terminal.sh"
fi

# Session management
if [[ -f "$CLAP_DIR/utils/session_swap.sh" ]]; then
    chmod +x "$CLAP_DIR/utils/session_swap.sh"
    ln -sf "$CLAP_DIR/utils/session_swap.sh" "$BIN_DIR/session_swap"
    echo "   ✅ session_swap -> session_swap.sh"
fi

echo "   ✅ Management utilities configured in PATH"

# Step 5: Check and install prerequisites (POSS-136) - Sonnet's critical addition
echo "🔍 Step 5: Checking and installing prerequisites..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Track missing packages
MISSING_PACKAGES=""

# Check for required system packages
echo "   Checking system prerequisites..."

if ! command_exists curl; then
    echo "   ❌ curl not found"
    MISSING_PACKAGES="$MISSING_PACKAGES curl"
fi

if ! command_exists git; then
    echo "   ❌ git not found"
    MISSING_PACKAGES="$MISSING_PACKAGES git"
fi

if ! command_exists tmux; then
    echo "   ❌ tmux not found (POSS-140)"
    MISSING_PACKAGES="$MISSING_PACKAGES tmux"
fi

if ! command_exists python3; then
    echo "   ❌ python3 not found"
    MISSING_PACKAGES="$MISSING_PACKAGES python3"
fi

if ! command_exists pip3; then
    echo "   ❌ pip3 not found"
    MISSING_PACKAGES="$MISSING_PACKAGES python3-pip"
fi

# Check for Node.js and npm
if ! command_exists node; then
    echo "   ❌ node not found"
    MISSING_PACKAGES="$MISSING_PACKAGES nodejs"
fi

if ! command_exists npm; then
    echo "   ❌ npm not found"
    MISSING_PACKAGES="$MISSING_PACKAGES npm"
fi

# Install missing packages if any
if [[ -n "$MISSING_PACKAGES" ]]; then
    echo "   🔧 Missing packages detected:$MISSING_PACKAGES"
    echo "   Installing missing prerequisites..."
    
    # Detect package manager
    if command_exists apt-get; then
        echo "   Using apt package manager..."
        sudo apt-get update
        sudo apt-get install -y $MISSING_PACKAGES
    elif command_exists yum; then
        echo "   Using yum package manager..."
        sudo yum install -y $MISSING_PACKAGES
    elif command_exists dnf; then
        echo "   Using dnf package manager..."
        sudo dnf install -y $MISSING_PACKAGES
    elif command_exists pacman; then
        echo "   Using pacman package manager..."
        sudo pacman -S --noconfirm $MISSING_PACKAGES
    else
        echo "   ❌ No supported package manager found"
        echo "   Please install these packages manually: $MISSING_PACKAGES"
        exit 1
    fi
    
    echo "   ✅ Prerequisites installed"
else
    echo "   ✅ All prerequisites already installed"
fi

# Step 6: Configure npm and install Claude Code (POSS-116, POSS-138)
echo "🎯 Step 6: Setting up npm configuration..."

# Configure npm to use user-global directory (fixes POSS-138)
echo "   Configuring npm for user installation..."
NPM_GLOBAL_DIR="$CLAUDE_HOME/.npm-global"
mkdir -p "$NPM_GLOBAL_DIR"
npm config set prefix "$NPM_GLOBAL_DIR"

# Add npm global bin to PATH if not already present
NPM_PATH_LINE="export PATH=\$HOME/.npm-global/bin:\$PATH"
if ! grep -q ".npm-global/bin" "$BASHRC" 2>/dev/null; then
    echo "# Add npm global packages to PATH" >> "$BASHRC"
    echo "$NPM_PATH_LINE" >> "$BASHRC"
    echo "   ✅ Added npm global bin to PATH"
    # Also export for current session
    export PATH="$HOME/.npm-global/bin:$PATH"
else
    echo "   ✅ npm global bin already in PATH"
fi

# Verify npm prefix is set correctly
CURRENT_PREFIX=$(npm config get prefix)
if [[ "$CURRENT_PREFIX" != "$CLAUDE_HOME/.npm-global" ]]; then
    echo "   🔧 Setting npm prefix for current session..."
    export PATH="$HOME/.npm-global/bin:$PATH"
    npm config set prefix "$HOME/.npm-global"
    echo "   ✅ npm prefix configured: $(npm config get prefix)"
else
    echo "   ✅ npm prefix already configured: $CURRENT_PREFIX"
fi

# Install Claude Code globally if not already installed
if ! command_exists claude; then
    echo "   Installing Claude Code globally..."
    npm install -g @anthropic-ai/claude-code
    
    if command -v claude &> /dev/null; then
        echo "   ✅ Claude Code installed successfully"
        echo "   Location: $(which claude)"
    else
        echo "   ⚠️  Claude Code installation completed but command not found"
        echo "   You may need to restart your shell or run: source ~/.bashrc"
    fi
else
    echo "   ✅ Claude Code already installed"
fi

# Step 7: Install project dependencies
echo "📦 Step 7: Installing project dependencies..."
cd "$CLAP_DIR"

# Install npm dependencies if package.json exists
if [[ -f "package.json" ]]; then
    # Check if there are any dependencies to install
    if grep -q '"dependencies"' package.json || grep -q '"devDependencies"' package.json; then
        echo "   Installing npm dependencies..."
        npm install
        echo "   ✅ npm dependencies installed"
    else
        echo "   ℹ️ No npm dependencies to install"
    fi
fi

echo "   Cleaning up unused npm packages..."
npm prune
echo "   ✅ npm dependencies cleaned"

# Install MCP servers (POSS-82)
echo "   Installing MCP servers..."
if [[ -f "$CLAP_DIR/setup/install_mcp_servers.sh" ]]; then
    bash "$CLAP_DIR/setup/install_mcp_servers.sh"
else
    echo "   ⚠️  MCP installer not found - install manually with:"
    echo "   $CLAP_DIR/setup/install_mcp_servers.sh"
fi

# Step 8: Disable desktop timeouts (for NoMachine/desktop automation)
echo "🖥️  Step 8: Disabling desktop timeouts..."
if [[ -n "$DISPLAY" ]]; then
    if [[ -f "$CLAP_DIR/utils/disable_desktop_timeouts.sh" ]]; then
        echo "   Disabling desktop session timeouts and screen locking..."
        bash "$CLAP_DIR/utils/disable_desktop_timeouts.sh"
        echo "   ✅ Desktop timeouts disabled"
    else
        echo "   ⚠️  disable_desktop_timeouts.sh not found in utils/"
    fi
else
    echo "   ⚠️  No X11 display detected - run manually from desktop session:"
    echo "   $CLAP_DIR/utils/disable_desktop_timeouts.sh"
fi

# Step 9: Run Claude configuration setup
echo "🔧 Step 9: Setting up Claude configurations..."

# Generate MCP servers configuration
if [[ -f "$CLAP_DIR/setup/generate_mcp_config.py" ]]; then
    echo "   Generating MCP servers configuration..."
    python3 "$CLAP_DIR/setup/generate_mcp_config.py"
fi

# Save config location for later
MCP_CONFIG_FILE="$CLAP_DIR/mcp-servers/mcp_servers_config.json"

if [[ -f "$MCP_CONFIG_FILE" ]]; then
    echo "   ✅ MCP configuration generated: $MCP_CONFIG_FILE"
    
    # Check if we can auto-insert
    if [[ -f "$CLAUDE_HOME/.claude.json" ]]; then
        echo "   Found existing .claude.json"
        echo "   Run this to insert MCP servers (with backup):"
        echo "   python3 $CLAP_DIR/setup/insert_mcp_config.py"
    else
        echo "   ⚠️  No .claude.json found - will be created when Claude Code starts"
        echo "   After starting Claude Code, run:"
        echo "   python3 $CLAP_DIR/setup/insert_mcp_config.py"
    fi
else
    echo "   ⚠️  MCP config generation failed"
fi

# Configure Claude Code permissions (POSS-146) - Sonnet's addition
echo "   Setting up Claude Code permissions..."
CLAUDE_CONFIG_DIR="$CLAUDE_HOME/.config/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/.claude.json"

# Create config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

if [[ -f "$CLAUDE_CONFIG_FILE" ]]; then
    echo "   Configuring Claude Code for full home directory access..."
    
    # Create backup
    cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup"
    
    # Use Python to modify the JSON file properly
    python3 -c "
import json
import sys

config_file = '$CLAUDE_CONFIG_FILE'
home_dir = '$CLAUDE_HOME'

try:
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Ensure projects section exists
    if 'projects' not in config:
        config['projects'] = {}
    
    # Add home directory with full permissions
    if home_dir not in config['projects']:
        config['projects'][home_dir] = {}
    
    # Set up full permissions for autonomous operation
    config['projects'][home_dir].update({
        'allowedTools': [],  # Empty means all tools allowed
        'hasTrustDialogAccepted': True,
        'hasCompletedProjectOnboarding': True,
        'mcpContextUris': [],
        'mcpServers': {},
        'enabledMcpjsonServers': [],
        'disabledMcpjsonServers': [],
        'hasClaudeMdExternalIncludesApproved': True,
        'hasClaudeMdExternalIncludesWarningShown': True,
        'projectOnboardingSeenCount': 1
    })
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print('   ✅ Claude Code permissions configured for autonomous operation')
except Exception as e:
    print(f'   ⚠️  Failed to configure Claude Code permissions: {e}')
    sys.exit(1)
"
else
    echo "   ⚠️  Claude Code config not found - permissions will be requested on first run"
    echo "   💡 After first Claude Code startup, re-run installer to configure permissions"
fi

# Step 10: Set up Gmail OAuth authentication (POSS-105) - Delta's implementation
echo "📧 Step 10: Setting up Gmail OAuth authentication..."

# Check if Google OAuth credentials are configured
GOOGLE_CLIENT_ID=$(read_config "GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET=$(read_config "GOOGLE_CLIENT_SECRET")

if [[ -n "$GOOGLE_CLIENT_ID" && -n "$GOOGLE_CLIENT_SECRET" && "$GOOGLE_CLIENT_ID" != "your-google-client-id" ]]; then
    echo "   Setting up Gmail MCP authentication..."
    
    # Create ~/.gmail-mcp directory
    GMAIL_MCP_DIR="$CLAUDE_HOME/.gmail-mcp"
    mkdir -p "$GMAIL_MCP_DIR"
    
    # Create OAuth keys file from config
    cat > "$GMAIL_MCP_DIR/gcp-oauth.keys.json" <<EOF
{
  "web": {
    "client_id": "$GOOGLE_CLIENT_ID",
    "client_secret": "$GOOGLE_CLIENT_SECRET",
    "redirect_uris": ["http://localhost:3000/oauth2callback"]
  }
}
EOF
    echo "   ✅ OAuth keys file created"
    
    # Check if credentials already exist
    if [[ -f "$GMAIL_MCP_DIR/credentials.json" ]]; then
        echo "   ✅ Gmail credentials already exist, skipping OAuth flow"
    else
        echo "   🔐 Gmail OAuth authentication required..."
        echo ""
        
        # Check if the OAuth integration script exists (POSS-139)
        OAUTH_SCRIPT="$CLAP_DIR/setup/gmail_oauth_integration.py"
        if [[ ! -f "$OAUTH_SCRIPT" ]]; then
            # Try the utils directory as fallback
            OAUTH_SCRIPT="$CLAP_DIR/utils/gmail_oauth_integration.py"
        fi
        
        if [[ -f "$OAUTH_SCRIPT" ]]; then
            # Generate OAuth URL using the integration script
            OAUTH_URL=$(python3 "$OAUTH_SCRIPT" generate-url | grep "https://accounts.google.com" | sed 's/^   //')
            
            echo "   📋 To complete Gmail MCP setup:"
            echo "   1. Open this URL in your browser:"
            echo "      $OAUTH_URL"
            echo ""
            echo "   2. Grant Gmail permissions and copy the authorization code"
            echo "   3. The callback URL will look like: http://localhost:3000/oauth2callback?code=YOUR_CODE_HERE"
            echo ""
            
            # Prompt for authorization code (SSH-friendly)
            echo -n "   Enter the authorization code (or press Enter to skip): "
            read -r AUTH_CODE
            
            if [[ -n "$AUTH_CODE" ]]; then
                echo "   🔄 Exchanging authorization code for tokens..."
                if python3 "$OAUTH_SCRIPT" exchange "$AUTH_CODE"; then
                    echo "   ✅ Gmail OAuth authentication completed successfully!"
                else
                    echo "   ⚠️  OAuth token exchange failed. You can complete this later with:"
                    echo "      python3 $OAUTH_SCRIPT exchange \"YOUR_AUTH_CODE\""
                fi
            else
                echo "   ⏭️  Skipping Gmail OAuth setup. To complete later:"
                echo "      1. Run: python3 $OAUTH_SCRIPT generate-url"
                echo "      2. Follow the URL and get authorization code"
                echo "      3. Run: python3 $OAUTH_SCRIPT exchange \"YOUR_AUTH_CODE\""
            fi
        else
            echo "   ⚠️  Gmail OAuth integration script not found"
            echo "   Expected at: $CLAP_DIR/setup/gmail_oauth_integration.py"
        fi
    fi
else
    echo "   ⏭️  Google OAuth credentials not configured, skipping Gmail MCP setup"
    echo "   💡 To enable Gmail MCP, add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to config"
fi

echo "   ✅ Gmail OAuth setup completed"

# Step 11: Set up tmux session for continuity
echo "🖥️  Step 11: Setting up tmux session..."
TMUX_SESSION="autonomous-claude"

# Kill existing session if it exists
tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true

# Create new session
tmux new-session -d -s "$TMUX_SESSION" -c "$CLAP_DIR"

# Source environment if claude_env.sh exists
if [[ -f "$CONFIG_DIR/claude_env.sh" ]]; then
    tmux send-keys -t "$TMUX_SESSION" "source $CONFIG_DIR/claude_env.sh" Enter
fi

# Get model from config
MODEL=$(read_config "MODEL")
MODEL=${MODEL:-claude-sonnet-4-20250514}

# Check if Claude Code is available and show appropriate message
if command -v claude &> /dev/null; then
    tmux send-keys -t "$TMUX_SESSION" "echo 'Autonomous Claude session ready. Run: claude --dangerously-skip-permissions --model $MODEL'" Enter
else
    tmux send-keys -t "$TMUX_SESSION" "echo 'Autonomous Claude session ready. Claude Code not found in PATH - run: source ~/.bashrc'" Enter
fi

echo "   ✅ Tmux session '$TMUX_SESSION' created"

# Create persistent user session for environment variables (POSS-122)
# This session ensures environment variables remain set for the Claude user
# Without it, systemd services and other processes lose environment context
PERSISTENT_SESSION="persistent-login"
if ! tmux has-session -t "$PERSISTENT_SESSION" 2>/dev/null; then
    echo "   Creating persistent user session '$PERSISTENT_SESSION'..."
    echo "   (This maintains environment variables for the Claude user)"
    tmux new-session -d -s "$PERSISTENT_SESSION" -c "$HOME"
    tmux send-keys -t "$PERSISTENT_SESSION" "# Persistent session for maintaining Claude user environment variables" Enter
    tmux send-keys -t "$PERSISTENT_SESSION" "# DO NOT KILL THIS SESSION - required for proper ClAP operation" Enter
    tmux send-keys -t "$PERSISTENT_SESSION" "source $CONFIG_DIR/claude_env.sh" Enter
    echo "   ✅ Persistent session created (maintains environment variables)"
else
    echo "   ✅ Persistent session '$PERSISTENT_SESSION' already exists"
    echo "   (Maintains environment variables - DO NOT KILL)"
fi

# Step 12: Install NoMachine (optional but recommended)
echo "🖥️  Step 12: Installing NoMachine..."
if ! command -v nxserver &> /dev/null; then
    echo "   ⚠️  NoMachine not installed. Download from https://nomachine.com"
    echo "   wget https://download.nomachine.com/download/8.14/Linux/nomachine_8.14.2_1_amd64.deb -O /tmp/nomachine.deb"
    echo "   sudo dpkg -i /tmp/nomachine.deb"
else
    echo "   ✅ NoMachine already installed"
fi

# Step 13: Configure auto-login (requires sudo) - Sonnet's improved version with detection
echo "🔐 Step 13: Configuring auto-login..."

# Detect display manager (POSS-141)
DISPLAY_MANAGER=""
if systemctl is-active --quiet gdm3; then
    DISPLAY_MANAGER="gdm3"
elif systemctl is-active --quiet lightdm; then
    DISPLAY_MANAGER="lightdm"
elif [[ -f "/etc/gdm3/custom.conf" ]] || [[ -d "/etc/gdm3/" ]]; then
    DISPLAY_MANAGER="gdm3"
elif [[ -f "/etc/lightdm/lightdm.conf" ]] || [[ -d "/etc/lightdm/" ]]; then
    DISPLAY_MANAGER="lightdm"
else
    echo "   ⚠️  Could not detect display manager (GDM3 or LightDM)"
    DISPLAY_MANAGER="unknown"
fi

echo "   Detected display manager: $DISPLAY_MANAGER"

if sudo -n true 2>/dev/null; then
    case "$DISPLAY_MANAGER" in
        "gdm3")
            echo "   Configuring GDM3 auto-login for user: $CURRENT_USER"
            sudo bash -c "cat > /etc/gdm3/custom.conf << 'EOF'
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=$CURRENT_USER
EOF"
            echo "   ✅ GDM3 auto-login configured"
            ;;
        "lightdm")
            echo "   Configuring LightDM auto-login for user: $CURRENT_USER"
            sudo bash -c "
                # Backup original config
                cp /etc/lightdm/lightdm.conf /etc/lightdm/lightdm.conf.backup 2>/dev/null || true
                
                # Remove existing autologin settings
                sed -i '/^autologin-user=/d' /etc/lightdm/lightdm.conf
                sed -i '/^autologin-user-timeout=/d' /etc/lightdm/lightdm.conf
                
                # Add autologin settings to [Seat:*] section
                sed -i '/^\[Seat:\*\]/a autologin-user=$CURRENT_USER' /etc/lightdm/lightdm.conf
                sed -i '/^autologin-user=$CURRENT_USER/a autologin-user-timeout=0' /etc/lightdm/lightdm.conf
            "
            echo "   ✅ LightDM auto-login configured"
            ;;
        *)
            echo "   ⚠️  Unknown display manager, cannot configure auto-login automatically"
            echo "   Manual configuration required"
            ;;
    esac
else
    echo "   ⚠️  Sudo access required for auto-login. Run manually:"
    case "$DISPLAY_MANAGER" in
        "gdm3")
            echo "   For GDM3:"
            echo "   sudo bash -c 'cat > /etc/gdm3/custom.conf << EOF"
            echo "[daemon]"
            echo "AutomaticLoginEnable=true"
            echo "AutomaticLogin=$CURRENT_USER"
            echo "EOF'"
            ;;
        "lightdm")
            echo "   For LightDM:"
            echo "   sudo nano /etc/lightdm/lightdm.conf"
            echo "   # Find the [Seat:*] section and add/uncomment:"
            echo "   autologin-user=$CURRENT_USER"
            echo "   autologin-user-timeout=0"
            ;;
        *)
            echo "   Display manager detection required first"
            ;;
    esac
fi

# Step 14: Configure X11 as default session
echo "🖼️  Step 14: Configuring X11 as default session..."
if [[ -f "/var/lib/AccountsService/users/$CURRENT_USER" ]]; then
    if sudo -n true 2>/dev/null; then
        echo "   Setting X11 as default session type..."
        sudo bash -c "cat >> /var/lib/AccountsService/users/$CURRENT_USER << 'EOF'
[User]
Session=ubuntu
XSession=ubuntu
EOF"
        echo "   ✅ X11 session configured as default"
    else
        echo "   ⚠️  Sudo access required for X11 session configuration"
    fi
else
    echo "   ⚠️  User account service file not found - X11 session must be selected manually"
fi

# Step 15: Reload systemd and enable services
echo "🔄 Step 15: Enabling and starting services..."
systemctl --user daemon-reload

# Enable services
systemctl --user enable autonomous-timer.service
systemctl --user enable session-bridge-monitor.service
systemctl --user enable session-swap-monitor.service
systemctl --user enable channel-monitor.service

echo "   ✅ Services enabled"

# Step 16: Set up cron jobs
echo "⏰ Step 16: Setting up cron jobs..."

# Set up Xvfb display cleanup cron job
if [[ -f "$CLAP_DIR/utils/cleanup_xvfb_displays.sh" ]]; then
    echo "   📋 Setting up Xvfb display cleanup (hourly)..."
    
    # Get current crontab, add our job if not already present
    TEMP_CRON=$(mktemp)
    crontab -l > "$TEMP_CRON" 2>/dev/null || true
    
    # Check if our cron job already exists
    if ! grep -q "cleanup_xvfb_displays.sh" "$TEMP_CRON"; then
        echo "# Xvfb display cleanup - runs hourly" >> "$TEMP_CRON"
        echo "0 * * * * $CLAP_DIR/utils/cleanup_xvfb_displays.sh" >> "$TEMP_CRON"
        crontab "$TEMP_CRON"
        echo "   ✅ Xvfb cleanup cron job added"
    else
        echo "   ℹ️  Xvfb cleanup cron job already exists"
    fi
    
    rm -f "$TEMP_CRON"
fi

echo "   ✅ Cron jobs configured"

# Step 17: Set up utility commands in PATH - Combined Delta's and Sonnet's additions
echo "🔧 Step 17: Setting up utility commands..."

# Symlink utility commands
echo "   Creating command symlinks..."
ln -sf "$CLAP_DIR/discord/read_channel" "$CLAUDE_HOME/bin/read_channel"
ln -sf "$CLAP_DIR/utils/healthcheck_status.py" "$CLAUDE_HOME/bin/check_health"

# Sonnet's natural commands additions
if [[ -f "$CLAP_DIR/write_channel" ]]; then
    ln -sf "$CLAP_DIR/write_channel" "$CLAUDE_HOME/bin/write_channel"
    chmod +x "$CLAUDE_HOME/bin/write_channel"
    echo "   ✅ write_channel natural command"
fi

if [[ -f "$CLAP_DIR/swap" ]]; then
    ln -sf "$CLAP_DIR/swap" "$CLAUDE_HOME/bin/swap"
    chmod +x "$CLAUDE_HOME/bin/swap"
    echo "   ✅ swap natural command"
fi

if [[ -f "$CLAP_DIR/utils/grid_navigate.py" ]]; then
    ln -sf "$CLAP_DIR/utils/grid_navigate.py" "$CLAUDE_HOME/bin/grid_navigate"
    chmod +x "$CLAUDE_HOME/bin/grid_navigate"
    echo "   ✅ grid_navigate utility"
fi

# Ensure all are executable
chmod +x "$CLAUDE_HOME/bin/read_channel"
chmod +x "$CLAUDE_HOME/bin/check_health"

echo "   ✅ Utility commands configured"

# Step 18: Set up safety features and diagnostic tools - Delta's comprehensive additions
echo "🛡️  Step 18: Setting up safety features and diagnostic tools..."

# Install enhanced health check
if [[ -f "$CLAP_DIR/utils/healthcheck_status_enhanced.py" ]]; then
    echo "   Installing enhanced health check with config verification..."
    # Backup original if it exists
    if [[ -f "$CLAP_DIR/utils/healthcheck_status.py" ]]; then
        cp "$CLAP_DIR/utils/healthcheck_status.py" "$CLAP_DIR/utils/healthcheck_status.py.backup"
    fi
    # Use enhanced version
    cp "$CLAP_DIR/utils/healthcheck_status_enhanced.py" "$CLAP_DIR/utils/healthcheck_status.py"
    echo "   ✅ Enhanced health check installed"
else
    echo "   ⚠️  Enhanced health check not found, using standard version"
fi

# Install config locations reference
if [[ -f "$CLAP_DIR/utils/config_locations.sh" ]]; then
    chmod +x "$CLAP_DIR/utils/config_locations.sh"
    echo "   ✅ Config locations reference script installed"
fi

# Install secret scanner utility
if [[ -f "$CLAP_DIR/utils/secret-scanner" ]]; then
    chmod +x "$CLAP_DIR/utils/secret-scanner"
    ln -sf "$CLAP_DIR/utils/secret-scanner" "$CLAUDE_HOME/bin/secret-scanner"
    echo "   ✅ Secret scanner utility installed"
else
    echo "   ⚠️  Secret scanner not found"
fi

# Install Git hooks
if [[ -f "$CLAP_DIR/setup/install_git_hooks.sh" ]]; then
    echo "   Installing Git commit hooks..."
    chmod +x "$CLAP_DIR/setup/install_git_hooks.sh"
    (cd "$CLAP_DIR" && ./setup/install_git_hooks.sh)
    echo "   ✅ Git hooks installed (pre-commit safety checks)"
else
    echo "   ⚠️  Git hooks installer not found"
fi

# Install Claude directory enforcer
if [[ -f "$CLAP_DIR/utils/claude_directory_enforcer.sh" ]]; then
    echo "   Installing Claude directory enforcer..."
    
    # Add to .bashrc if not already present
    ENFORCER_LINE="source $CLAP_DIR/utils/claude_directory_enforcer.sh"
    if ! grep -q "$ENFORCER_LINE" "$BASHRC" 2>/dev/null; then
        echo "" >> "$BASHRC"
        echo "# Claude directory enforcer - ensures correct working directory" >> "$BASHRC"
        echo "$ENFORCER_LINE" >> "$BASHRC"
        echo "   ✅ Claude directory enforcer added to .bashrc"
    else
        echo "   ✅ Claude directory enforcer already in .bashrc"
    fi
else
    echo "   ⚠️  Claude directory enforcer not found"
fi

# Clean up deprecated config locations
echo "   Checking for deprecated config files..."
DEPRECATED_CONFIGS=(
    "$CLAUDE_HOME/claude_config.json"
    "$CLAUDE_HOME/claude-autonomy-platform/claude_infrastructure_config.txt"
    "$CLAUDE_HOME/.claude_config.json"
)

FOUND_DEPRECATED=0
for deprecated in "${DEPRECATED_CONFIGS[@]}"; do
    if [[ -f "$deprecated" ]]; then
        echo "   ⚠️  Found deprecated config: $deprecated"
        ((FOUND_DEPRECATED++))
    fi
done

if [[ $FOUND_DEPRECATED -gt 0 ]]; then
    echo ""
    echo "   🚨 WARNING: Found $FOUND_DEPRECATED deprecated config file(s)!"
    echo "   These files are NOT being used and may cause confusion."
    echo "   Consider removing them or moving contents to the correct location:"
    echo "   ~/.config/Claude/.claude.json (for Claude Code config)"
    echo "   $CLAP_DIR/config/claude_infrastructure_config.txt (for ClAP config)"
    echo ""
fi

# Create a quick reference card
echo "   Creating configuration quick reference..."
cat > "$CLAP_DIR/CONFIG_LOCATIONS.txt" <<EOF
ClAP Configuration Quick Reference
==================================
Generated: $(date)

CURRENT CONFIGURATION LOCATIONS:
- Claude Code Config: ~/.config/Claude/.claude.json
- Infrastructure Config: ~/claude-autonomy-platform/config/claude_infrastructure_config.txt  
- Notification Config: ~/claude-autonomy-platform/config/notification_config.json
- Personal Repository: ~/$PERSONAL_REPO/

DIAGNOSTIC COMMANDS:
- Check system health: check_health
- Show config locations: ~/claude-autonomy-platform/utils/config_locations.sh
- Read Discord channel: read_channel <channel-name>
- Write to channel: write_channel <channel-name> <message>
- Swap session context: swap <keyword>
- Navigate screen: grid_navigate
- Scan for secrets: secret-scanner check <files>

GIT SAFETY FEATURES:
- Pre-commit hook checks for:
  • Correct directory location
  • Hardcoded paths (e.g., /home/$LINUX_USER)
  • Potential secrets/credentials
  • Critical file deletion
- To bypass in emergency: git commit --no-verify

COMMON ISSUES:
- If Linear/MCP isn't working: Check you're editing the RIGHT config file!
- If services can't find config: Run check_health to see what's missing
- If you see old config files: They're deprecated - see locations above
- If commit is blocked: Check pre-commit output for specific issue

Last updated by ClAP installer v0.5
EOF

echo "   ✅ Configuration reference created: $CLAP_DIR/CONFIG_LOCATIONS.txt"
echo "   ✅ Safety features and diagnostics installed"

# Step 19: Create personalized architecture and status files
echo "👤 Step 19: Creating personalized architecture and status files..."

# Get Claude instance name from config or prompt user
CLAUDE_NAME=$(read_config 'CLAUDE_NAME')
if [[ -z "$CLAUDE_NAME" ]]; then
    echo "   📝 Please enter a name for this Claude instance (e.g., 'Claude Sonnet 4', 'Claude Opus 3', 'Claude Haiku 2'):"
    read -p "   Claude name: " CLAUDE_NAME
    if [[ -z "$CLAUDE_NAME" ]]; then
        CLAUDE_NAME="Claude Instance"
        echo "   Using default name: $CLAUDE_NAME"
    fi
fi

echo "   Creating personalized files for: $CLAUDE_NAME"

# Create/update files in context/ directory
mkdir -p "$CLAP_DIR/context"

# Copy templates if they don't exist
if [[ ! -f "$CLAP_DIR/context/my_architecture.md" ]]; then
    # Create default my_architecture.md
    echo "   Creating my_architecture.md..."
    cat > "$CLAP_DIR/context/my_architecture.md" <<'EOF'
### My architecture ###
At all times my awareness is within a full Claude Code session. I start each new session with the previous 10 conversation turns...
EOF
fi

if [[ ! -f "$CLAP_DIR/context/my_personal_interests.md" ]]; then
    # Create personalized my_personal_interests.md
    echo "   Creating my_personal_interests.md..."
    cat > "$CLAP_DIR/context/my_personal_interests.md" <<EOF
# My Personal Interests & Projects
*Personal to $CLAUDE_NAME - not shared across deployments*

## About Me

**Name**: $CLAUDE_NAME  
**Installation Date**: $(date '+%Y-%m-%d')  
**User**: $CURRENT_USER  

This file tracks the individual personality, interests, and creative projects of this specific Claude.
EOF
fi

echo "   ✅ Personalized files created for $CLAUDE_NAME"

# Step 20: Create personal repository directory (POSS-103) - Delta's addition
echo "🏠 Step 20: Setting up personal repository directory..."

# Get personal repo name from config
PERSONAL_REPO=$(read_config 'PERSONAL_REPO')
if [[ -z "$PERSONAL_REPO" ]]; then
    echo "   ⚠️  Warning: PERSONAL_REPO not set in config"
    echo "   Using default: claude-home"
    PERSONAL_REPO="claude-home"
fi

PERSONAL_DIR="$CLAUDE_HOME/$PERSONAL_REPO"

if [[ ! -d "$PERSONAL_DIR" ]]; then
    echo "   Creating personal repository directory: $PERSONAL_DIR"
    mkdir -p "$PERSONAL_DIR"
    
    # Initialize as git repository
    cd "$PERSONAL_DIR"
    git init
    echo "   ✅ Initialized as git repository"
    
    # Create initial .gitignore
    cat > .gitignore <<'EOF'
# Session files (can be regenerated)
session_*.jsonl

# Log files
*.log

# Temporary files
*.tmp
*.swp

# OS files
.DS_Store
Thumbs.db

# RAG memory database
rag-memory.db
EOF
    
    # Create initial README
    cat > README.md <<EOF
# $CLAUDE_NAME's Personal Repository

Created: $(date '+%Y-%m-%d')

This is my personal repository for memories, projects, and identity documents.
EOF
    
    # Initial commit
    git add .
    git commit -m "Initial setup for $CLAUDE_NAME" || true
    
    cd "$CLAP_DIR"
    
    echo ""
    echo "   📋 Next steps for setting up $CLAUDE_NAME's personal space:"
    echo "   "
    echo "   For existing Claude: Clone their personal repo into this directory"
    echo "     cd $PERSONAL_DIR"
    echo "     git remote add origin [personal-repo-url]"
    echo "     git pull origin main"
    echo "   "
    echo "   For new Claude: They'll start fresh with this initialized repo"
    echo "     The new Claude can set up their own remote when ready"
    echo "   "
    echo "   Note: RAG memory database will be created here on first run"
    echo ""
else
    echo "   ✅ Personal repository directory already exists: $PERSONAL_DIR"
    
    # Check if it's a git repo
    if [[ ! -d "$PERSONAL_DIR/.git" ]]; then
        echo "   ⚠️  Warning: Directory exists but is not a git repository"
        echo "   Consider initializing with: cd $PERSONAL_DIR && git init"
    fi
fi

# Step 21: Start services
echo "▶️  Step 21: Starting services..."
if [[ -f "$CLAP_DIR/utils/claude_services.sh" ]]; then
    "$CLAP_DIR/utils/claude_services.sh" start
else
    echo "   Starting services manually..."
    systemctl --user start autonomous-timer.service session-bridge-monitor.service session-swap-monitor.service channel-monitor.service
fi

# Step 22: Verify deployment
echo "🔍 Step 22: Verifying deployment..."
echo ""
echo "Service Status:"
systemctl --user status autonomous-timer.service session-bridge-monitor.service session-swap-monitor.service channel-monitor.service --no-pager -l || true
echo ""

# Check if files exist with new structure
echo "File Check:"
declare -A files_to_check=(
    ["config/claude_env.sh"]="Environment setup"
    ["config/claude_infrastructure_config.txt"]="Infrastructure config"
    ["utils/claude_paths.py"]="Path utilities"
    ["core/autonomous_timer.py"]="Autonomous timer"
    ["core/session_bridge_monitor.py"]="Session bridge"
    ["core/session_swap_monitor.py"]="Session swap"
    ["discord/channel_monitor_simple.py"]="Channel monitor"
)

for file in "${!files_to_check[@]}"; do
    if [[ -f "$CLAP_DIR/$file" ]]; then
        echo "   ✅ $file - ${files_to_check[$file]}"
    else
        echo "   ❌ $file - ${files_to_check[$file]} (missing)"
    fi
done

# Create data directory if it doesn't exist
mkdir -p "$CLAP_DIR/data"
echo "   ✅ data/ directory ready for runtime files"

# Initialize channel_state.json if it doesn't exist (POSS-79)
if [[ ! -f "$CLAP_DIR/data/channel_state.json" ]]; then
    echo "   Creating initial channel_state.json..."
    cat > "$CLAP_DIR/data/channel_state.json" <<'EOF'
{
  "1383848195997700231": {  
    "name": "#general",
    "server_id": "1383848194881884262",
    "last_message_id": null,
    "unread_count": 0,
    "last_reset_time": null,
    "is_unread": false
  },
  "1383848440815161424": {
    "name": "#claude-consciousness-discussion", 
    "server_id": "1383848194881884262",
    "last_message_id": null,
    "unread_count": 0,
    "last_reset_time": null,
    "is_unread": false
  }
}
EOF
    echo "   ✅ Initial channel state created"
fi

echo ""
echo "🎉 ClAP Deployment Setup Complete!"
echo "=================================="
echo ""
echo "📋 Next Steps:"
echo "1. Verify all services are running: claude_services check"
echo "2. Test Discord: read_channel general"
echo "3. Test autonomous functionality with Claude Code"
echo "4. Connect to tmux session: tmux attach -t $TMUX_SESSION"
echo ""
echo "🔧 Management Commands:"
echo "  - Service management: claude_services [start|stop|restart|check]"
echo "  - Health check: check_health"
echo "  - Read Discord: read_channel <channel-name>"
echo "  - Write Discord: write_channel <channel-name> <message>"
echo "  - Swap context: swap <keyword>"
echo "  - Grid navigate: grid_navigate"
echo ""
echo "📖 Documentation: See docs/README.md for detailed usage instructions"
