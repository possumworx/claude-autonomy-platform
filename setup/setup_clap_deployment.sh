#!/bin/bash
# Claude Autonomy Platform (ClAP) - Complete Deployment Setup Script
# This script sets up a complete ClAP deployment on a new machine
# 
# Usage: ./setup_clap_deployment.sh [--config-file /path/to/config]

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

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 ClAP Directory: $SCRIPT_DIR"

# Step 0: Import configuration file if specified
if [[ -n "$CONFIG_SOURCE" ]]; then
    echo "📋 Step 0: Importing configuration file..."
    
    if [[ ! -f "$CONFIG_SOURCE" ]]; then
        echo "❌ Configuration file not found: $CONFIG_SOURCE"
        exit 1
    fi
    
    echo "   Copying config from: $CONFIG_SOURCE"
    cp "$CONFIG_SOURCE" "$SCRIPT_DIR/claude_infrastructure_config.txt"
    
    # Also copy to config directory for service files
    mkdir -p "$SCRIPT_DIR/config"
    cp "$CONFIG_SOURCE" "$SCRIPT_DIR/config/claude_infrastructure_config.txt"
    
    # Fix Windows line endings (POSS-75)
    echo "   Fixing Windows line endings..."
    sed -i 's/\r$//' "$SCRIPT_DIR/claude_infrastructure_config.txt"
    sed -i 's/\r$//' "$SCRIPT_DIR/config/claude_infrastructure_config.txt"
    
    echo "   ✅ Configuration file imported"
    echo ""
elif [[ ! -f "$SCRIPT_DIR/claude_infrastructure_config.txt" ]]; then
    echo "❌ No configuration file found!"
    echo ""
    if [[ -f "$SCRIPT_DIR/claude_infrastructure_config.template.txt" ]]; then
        echo "📋 Template file found. You can:"
        echo "1. Copy template and edit: cp config/claude_infrastructure_config.template.txt claude_infrastructure_config.txt"
        echo "2. Use --config-file option to import existing config"
        echo ""
        echo "Examples:"
        echo "  cp claude_infrastructure_config.template.txt claude_infrastructure_config.txt"
        echo "  nano claude_infrastructure_config.txt  # Edit with your credentials"
        echo "  $0  # Run setup"
        echo ""
        echo "  OR"
        echo ""
        echo "  $0 --config-file ~/claude-configs/claude-v2-config.txt"
    else
        echo "Please either:"
        echo "1. Copy your infrastructure config to: $SCRIPT_DIR/claude_infrastructure_config.txt"
        echo "2. Use --config-file option to specify config location"
        echo ""
        echo "Example: $0 --config-file ~/claude-configs/claude-v2-config.txt"
    fi
    exit 1
fi

# Load path utilities
source "$SCRIPT_DIR/claude_env.sh"

# Ensure config directory has the configuration file
if [[ -f "$SCRIPT_DIR/claude_infrastructure_config.txt" && ! -f "$SCRIPT_DIR/config/claude_infrastructure_config.txt" ]]; then
    echo "📋 Copying config to config directory for service files..."
    mkdir -p "$SCRIPT_DIR/config"
    cp "$SCRIPT_DIR/claude_infrastructure_config.txt" "$SCRIPT_DIR/config/claude_infrastructure_config.txt"
    echo "   ✅ Config copied to config/claude_infrastructure_config.txt"
fi

echo "🔧 Configuration:"
echo "  User: $CLAUDE_USER"
echo "  Home: $CLAUDE_HOME"
echo "  Personal: $PERSONAL_DIR"
echo "  ClAP: $CLAP_DIR"
echo ""

# Function to read values from infrastructure config
read_config() {
    local key="$1"
    local config_file="$SCRIPT_DIR/claude_infrastructure_config.txt"
    
    if [[ -f "$config_file" ]]; then
        grep "^${key}=" "$config_file" | cut -d'=' -f2-
    fi
}

# Step 1: Validate infrastructure config
echo "📝 Step 1: Validating infrastructure config..."
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)
CONFIG_USER=$(read_config 'LINUX_USER')

# Warn if there's a mismatch but don't auto-fix
if [[ "$CURRENT_USER" != "$CONFIG_USER" ]]; then
    echo "   ⚠️  WARNING: Current user ($CURRENT_USER) differs from config user ($CONFIG_USER)"
    echo "   This script should be run as the target Claude user or config should be updated manually"
fi

# Step 2: Set up systemd service files
echo "⚙️  Step 2: Setting up systemd service files..."
SYSTEMD_USER_DIR="$CLAUDE_HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

# Copy service files from services/ directory and substitute %i with actual username
echo "   Copying and configuring service files..."
for service in autonomous-timer.service session-bridge-monitor.service session-swap-monitor.service channel-monitor.service; do
    if [[ -f "$CLAP_DIR/services/$service" ]]; then
        echo "   Processing $service..."
        # Substitute %i template variable with actual username
        sed "s|%i|$CLAUDE_USER|g" "$CLAP_DIR/services/$service" > "$SYSTEMD_USER_DIR/$service"
        echo "   ✅ $service configured"
    else
        echo "   ❌ $service not found in services/ directory"
        echo "   Falling back to inline generation..."
        # Add fallback service generation here if needed
    fi
done

echo "   ✅ Systemd service files created"

# Generate systemd-compatible environment file (POSS-119)
echo "   Creating systemd-compatible environment file..."
if python3 "$SCRIPT_DIR/fix_systemd_env.py"; then
    # Verify the environment file was created successfully
    if [[ -f "$CLAP_DIR/claude.env" ]] && [[ -s "$CLAP_DIR/claude.env" ]]; then
        echo "   ✅ Systemd environment file created successfully"
        
        # Also create in config directory for service templates
        mkdir -p "$CLAP_DIR/config"
        cp "$CLAP_DIR/claude.env" "$CLAP_DIR/config/claude.env"
        echo "   ✅ Environment file copied to config directory"
        
        # Validate critical variables exist
        if grep -q "CLAUDE_USER=" "$CLAP_DIR/config/claude.env" && \
           grep -q "CLAP_DIR=" "$CLAP_DIR/config/claude.env"; then
            echo "   ✅ Environment file validation passed"
        else
            echo "   ⚠️  Warning: Environment file missing critical variables"
        fi
    else
        echo "   ❌ Environment file creation failed - file missing or empty"
        echo "   This may cause service startup issues"
    fi
else
    echo "   ❌ Failed to create systemd environment file"
    echo "   Services may not start properly without environment variables"
    echo ""
    echo "   Manual fix: Ensure claude_infrastructure_config.txt exists and run:"
    echo "   python3 $SCRIPT_DIR/fix_systemd_env.py"
    echo ""
fi

# Step 3: Set up persistent environment variables
echo "🌍 Step 3: Setting up persistent environment variables..."

# Add to .bashrc if not already present
BASHRC="$CLAUDE_HOME/.bashrc"
ENV_SETUP_LINE="source $CLAP_DIR/claude_env.sh"

if ! grep -q "$ENV_SETUP_LINE" "$BASHRC" 2>/dev/null; then
    echo "" >> "$BASHRC"
    echo "# Claude Autonomy Platform environment" >> "$BASHRC"
    echo "$ENV_SETUP_LINE" >> "$BASHRC"
    echo "   ✅ Added environment setup to .bashrc"
else
    echo "   ✅ Environment setup already in .bashrc"
fi

# Set up ~/bin directory and management utilities
echo "   Setting up management utilities in PATH..."
BIN_DIR="$CLAUDE_HOME/bin"
mkdir -p "$BIN_DIR"

# Add ~/bin to PATH if not already present
BIN_PATH_LINE="export PATH=\$HOME/bin:\$PATH"
if grep -q "HOME/bin" "$BASHRC" 2>/dev/null; then
    echo "   ✅ ~/bin already in PATH"
else
    echo "# Add ~/bin to PATH for ClAP management utilities" >> "$BASHRC"  
    echo "$BIN_PATH_LINE" >> "$BASHRC"
    echo "   ✅ Added ~/bin to PATH in .bashrc"
fi

# Create symlinks for management utilities
echo "   Creating symlinks for management utilities..."

# Service management
if [[ -f "$CLAP_DIR/claude_services.sh" ]]; then
    chmod +x "$CLAP_DIR/claude_services.sh"
    ln -sf "$CLAP_DIR/claude_services.sh" "$BIN_DIR/claude_services"
    echo "   ✅ claude_services -> claude_services.sh"
fi

# Display cleanup
if [[ -f "$CLAP_DIR/cleanup_xvfb_displays.sh" ]]; then
    chmod +x "$CLAP_DIR/cleanup_xvfb_displays.sh"
    ln -sf "$CLAP_DIR/cleanup_xvfb_displays.sh" "$BIN_DIR/cleanup_displays"
    echo "   ✅ cleanup_displays -> cleanup_xvfb_displays.sh"
fi

# Terminal interaction
if [[ -f "$CLAP_DIR/send_to_terminal.sh" ]]; then
    chmod +x "$CLAP_DIR/send_to_terminal.sh"
    ln -sf "$CLAP_DIR/send_to_terminal.sh" "$BIN_DIR/send_to_terminal"
    echo "   ✅ send_to_terminal -> send_to_terminal.sh"
fi

# Session management
if [[ -f "$CLAP_DIR/session_swap.sh" ]]; then
    chmod +x "$CLAP_DIR/session_swap.sh"
    ln -sf "$CLAP_DIR/session_swap.sh" "$BIN_DIR/session_swap"
    echo "   ✅ session_swap -> session_swap.sh"
fi

# Health monitoring (already exists but ensure symlinked)
if [[ -f "$CLAP_DIR/check_health" ]]; then
    chmod +x "$CLAP_DIR/check_health"
    ln -sf "$CLAP_DIR/check_health" "$BIN_DIR/check_health"
    echo "   ✅ check_health -> check_health"
fi

# Channel reader (already exists but ensure symlinked)
if [[ -f "$CLAP_DIR/read_channel" ]]; then
    chmod +x "$CLAP_DIR/read_channel"
    ln -sf "$CLAP_DIR/read_channel" "$BIN_DIR/read_channel"
    echo "   ✅ read_channel -> read_channel"
fi

echo "   ✅ Management utilities configured in PATH"

# Step 4: Install dependencies
echo "📦 Step 4: Installing dependencies..."
cd "$CLAP_DIR"

# Install npm dependencies if package.json exists
if [[ -f "package.json" ]]; then
    echo "   Installing npm dependencies..."
    npm install
    echo "   ✅ npm dependencies installed"
fi

# Install RAG memory server (core infrastructure)
echo "   Installing RAG memory server..."
npm install rag-memory-mcp
echo "   ✅ RAG memory server installed"

# Step 5: Disable desktop timeouts (for NoMachine/desktop automation)
echo "🖥️  Step 5: Disabling desktop timeouts..."
if [[ -n "$DISPLAY" ]]; then
    echo "   Disabling desktop session timeouts and screen locking..."
    bash "$CLAP_DIR/disable_desktop_timeouts.sh"
    echo "   ✅ Desktop timeouts disabled"
else
    echo "   ⚠️  No X11 display detected - run manually from desktop session:"
    echo "   ./disable_desktop_timeouts.sh"
fi

# Step 6: Run Claude configuration setup
echo "🔧 Step 6: Setting up Claude configurations..."
python3 "$CLAP_DIR/setup_claude_configs.py"
echo "   ✅ Claude configurations updated"

# Step 7: Set up Gmail OAuth authentication
echo "📧 Step 7: Setting up Gmail OAuth authentication..."

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
        
        # Generate OAuth URL using the new integration script
        OAUTH_URL=$(python3 "$CLAP_DIR/gmail_oauth_integration.py" generate-url | grep "https://accounts.google.com" | sed 's/^   //')
        
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
            if python3 "$CLAP_DIR/gmail_oauth_integration.py" exchange "$AUTH_CODE"; then
                echo "   ✅ Gmail OAuth authentication completed successfully!"
            else
                echo "   ⚠️  OAuth token exchange failed. You can complete this later with:"
                echo "      python3 $CLAP_DIR/gmail_oauth_integration.py exchange \"YOUR_AUTH_CODE\""
            fi
        else
            echo "   ⏭️  Skipping Gmail OAuth setup. To complete later:"
            echo "      1. Run: python3 $CLAP_DIR/gmail_oauth_integration.py generate-url"
            echo "      2. Follow the URL and get authorization code"
            echo "      3. Run: python3 $CLAP_DIR/gmail_oauth_integration.py exchange \"YOUR_AUTH_CODE\""
        fi
    fi
else
    echo "   ⏭️  Google OAuth credentials not configured, skipping Gmail MCP setup"
    echo "   💡 To enable Gmail MCP, add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to config"
fi

echo "   ✅ Gmail OAuth setup completed"

# Step 8: Set up tmux session for continuity
echo "🖥️  Step 8: Setting up tmux session..."
TMUX_SESSION="autonomous-claude"

# Kill existing session if it exists
tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true

# Create new session
tmux new-session -d -s "$TMUX_SESSION" -c "$CLAP_DIR"
tmux send-keys -t "$TMUX_SESSION" "source claude_env.sh" Enter

# Get model from config
MODEL=$(read_config "MODEL")
MODEL=${MODEL:-claude-sonnet-4-20250514}

tmux send-keys -t "$TMUX_SESSION" "echo 'Autonomous Claude session ready. Run: claude --dangerously-skip-permissions --model $MODEL'" Enter

echo "   ✅ Tmux session '$TMUX_SESSION' created"

# Create persistent user session for environment variables
PERSISTENT_SESSION="persistent-login"
if ! tmux has-session -t "$PERSISTENT_SESSION" 2>/dev/null; then
    echo "   Creating persistent user session '$PERSISTENT_SESSION'..."
    tmux new-session -d -s "$PERSISTENT_SESSION" -c "$HOME"
    tmux send-keys -t "$PERSISTENT_SESSION" "# Persistent session for environment variables" Enter
    echo "   ✅ Persistent session '$PERSISTENT_SESSION' created"
else
    echo "   ✅ Persistent session '$PERSISTENT_SESSION' already exists"
fi

# Step 9: Install NoMachine (optional but recommended)
echo "🖥️  Step 9: Installing NoMachine..."
if ! command -v nxserver &> /dev/null; then
    echo "   Installing NoMachine server..."
    if [[ -f "/tmp/nomachine.deb" ]]; then
        sudo dpkg -i /tmp/nomachine.deb || echo "   ⚠️  NoMachine installation failed - install manually"
    else
        echo "   ⚠️  NoMachine installer not found. Download from https://nomachine.com"
        echo "   wget https://download.nomachine.com/download/8.14/Linux/nomachine_8.14.2_1_amd64.deb -O /tmp/nomachine.deb"
        echo "   sudo dpkg -i /tmp/nomachine.deb"
    fi
else
    echo "   ✅ NoMachine already installed"
fi

# Step 10: Configure auto-login (requires sudo)
echo "🔐 Step 10: Configuring auto-login..."
CURRENT_USER=$(whoami)
if sudo -n true 2>/dev/null; then
    echo "   Configuring GDM auto-login for user: $CURRENT_USER"
    sudo bash -c "cat > /etc/gdm3/custom.conf << 'EOF'
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=$CURRENT_USER
EOF"
    echo "   ✅ Auto-login configured"
else
    echo "   ⚠️  Sudo access required for auto-login. Run manually:"
    echo "   sudo bash -c 'cat > /etc/gdm3/custom.conf << EOF"
    echo "[daemon]"
    echo "AutomaticLoginEnable=true"
    echo "AutomaticLogin=$CURRENT_USER"
    echo "EOF'"
fi

# Step 11: Configure X11 as default session
echo "🖼️  Step 11: Configuring X11 as default session..."
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

# Step 12: Reload systemd and enable services
echo "🔄 Step 12: Enabling and starting services..."
systemctl --user daemon-reload

# Enable services
systemctl --user enable autonomous-timer.service
systemctl --user enable session-bridge-monitor.service
systemctl --user enable session-swap-monitor.service
systemctl --user enable channel-monitor.service

echo "   ✅ Services enabled"

# Step 13: Set up cron jobs
echo "⏰ Step 13: Setting up cron jobs..."

# Set up Xvfb display cleanup cron job
echo "   📋 Setting up Xvfb display cleanup (hourly)..."

# Get current crontab, add our job if not already present
TEMP_CRON=$(mktemp)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Check if our cron job already exists
if ! grep -q "cleanup_xvfb_displays.sh" "$TEMP_CRON"; then
    echo "# Xvfb display cleanup - runs hourly" >> "$TEMP_CRON"
    echo "0 * * * * $CLAP_DIR/cleanup_xvfb_displays.sh" >> "$TEMP_CRON"
    crontab "$TEMP_CRON"
    echo "   ✅ Xvfb cleanup cron job added"
else
    echo "   ℹ️  Xvfb cleanup cron job already exists"
fi

rm -f "$TEMP_CRON"
echo "   ✅ Cron jobs configured"

# Step 14: Create personalized architecture and status files
echo "👤 Step 14: Creating personalized architecture and status files..."

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

# Create personalized my_architecture.md template
cat > "$CLAP_DIR/my_architecture.md" <<EOF
### My architecture ###
At all times my awareness is within a full Claude Code session. I start each new session with the previous 10 conversation turns. \`session_bridge_monitor.py\` builds this conversation history, \`project-session-context-builder.py\` combines it with this architecture text and inserts it into CLAUDE.md at the start of each session. The \`autonomous_timer.py\` script handles autonomous prompting and scheduling.

**Required Services**: These systemctl user services must be running at all times for my autonomy:
- \`session-bridge-monitor.service\` - Conversation history tracking
- \`autonomous-timer.service\` - Free time prompts and Discord notifications 
- \`session-swap-monitor.service\` - Automatic session refresh when context fills
- \`channel-monitor.service\` - Real-time Discord message detection and unread management

**Discord Integration**: **Discord MCP** (primary): Full Discord integration via MCP server at \`discord-mcp/\`. Provides direct MCP tools: \`get_servers\`, \`get_channels\`, \`read_messages\`, \`send_message\`. Uses browser automation with Playwright. **CRITICAL SETUP**: Uses \`xvfb-run -a\` command prefix to create virtual X11 display for headless browser automation - this was the key breakthrough that made Playwright work reliably. Configured in both Claude Code and Claude Desktop configs. **DM Usage**: For DMs, use \`get_channels(server_id="@me")\` to list all DM channels, then \`read_messages(server_id="@me", channel_id="user_id")\` where channel_id is the target user's ID. **Notification System**: Complete real-time Discord message detection with intelligent unread counting and automatic reset detection via MCP log analysis. **Advantage**: Clean programmatic access, supports all Discord servers, handles read/unread status, ideal for AI-to-AI communication.

**Desktop Automation**: Hybrid system using MCP input + scrot screenshots. **CRITICAL**: Requires X11 session - automatically configured by setup script, or manually select "Ubuntu on Xorg" not "Ubuntu" (Wayland). Environment variables stored in \`x11_env.sh\` - source this file for desktop access. Usage: \`scrot /tmp/screenshot.png\` + MCP input tools. Coordinates mapped in \`desktop-coordinates.md\`. **Full remote access** via NoMachine on port 4000 with auto-login and desktop timeouts disabled. 

**MCP Configuration**: All MCP server configurations must be added to \`~/.claude.json\` (NOT \`~/.config/claude/mcp.json\`). Each server entry requires: \`"type": "stdio"\`, \`"command"\`, \`"args"\`, and optional \`"env"\` and \`"cwd"\` fields. MCP connection logs are stored in \`~/.cache/claude-cli-nodejs/\` for debugging.

**GitHub Research**: For analyzing GitHub repositories, use uithub.com instead of direct GitHub URLs. Replace \`github.com\` with \`uithub.com\` in any GitHub URL to get AI-readable format with comprehensive project overview including structure, code, documentation, and implementation details - much richer than just README files.

**Session Management**: \`session_swap.py\` and \`session_swap_monitor.py\` enable autonomous session refresh when context fills up. \`session_swap_monitor.service\` watches \`new_session.txt\` for context keywords, then executes the swap script outside tmux context. Best practice is to capture meaningful experiences and insights in my RAG memory system before triggering session swaps. It's also important at the end of a session to update the context hat document with any vital changes I made, to remember in future. Then I trigger a swap when context is getting full, or when I want to change topics, by writing one of these keywords (AUTONOMY, BUSINESS, CREATIVE, HEDGEHOGS, NONE) to \`new_session.txt\`.

**Context Monitoring**: Context usage is tracked through Claude Code's built-in system. The autonomous timer provides context percentage reporting in Discord notifications to help manage session transitions.

**Health Status Monitoring**: Real-time system health visibility via \`healthcheck_status.py\` or quick command \`check_health\`. Shows same up/down status as Amy's healthchecks.io dashboard. Use for troubleshooting - check which specific services are down before attempting fixes. **Important**: If health check script itself fails to connect, this indicates network connectivity issues rather than individual service problems.

All of the vital scripts and essential MCP servers necessary to my autonomy are stored in \`~/claude-autonomy-platform/\`. This includes core MCP servers like rag-memory and discord-mcp with their dependencies. Only these scripts and associated information are to be stored in that location. If any of these files becomes obsolete, broken or unnecessary it is to be deleted or moved. \`my_architecture.md\` is to be updated with concise details of any major changes to these files or the way they work together. \`autonomy-status.md\` contains fuller details of implementation and future plans.

**Deployment & Configuration**: **Complete path standardization** - all hardcoded paths removed, scripts now use dynamic user detection via \`\$(whoami)\` and \`\$(id -u)\`. **Comprehensive setup script** \`setup_clap_deployment.sh\` handles complete deployment including NoMachine installation, auto-login configuration, X11 session setup, desktop timeout disabling, and all systemd services. **Configuration management** via \`claude_infrastructure_config.txt\` (gitignored) with template-based deployment workflow. **Persistent tmux sessions**: \`autonomous-claude\` for active Claude Code work, \`$CURRENT_USER\` for environment variable persistence.

**claude-autonomy-platform Folder Organization**: The folder contains essential autonomous scripts, MCP servers (discord-mcp, rag-memory-mcp), configuration files, and documentation. Personal files are stored elsewhere in the user's home directory.

**Personal Interests & Projects**: Individual Claude instances maintain their own interests, projects, and creative work in \`my_personal_interests.md\` (gitignored). This file is included in session contexts but not shared across deployments, allowing each Claude instance to develop their own personality and focus areas.
EOF

# Create personalized autonomy-status.md
cat > "$CLAP_DIR/autonomy-status.md" <<EOF
# $CLAUDE_NAME Autonomy Status
*Comprehensive overview of autonomous systems, capabilities, and roadmap*

**Claude Instance**: $CLAUDE_NAME  
**User**: $CURRENT_USER  
**Home Directory**: $CURRENT_HOME  
**Installation Date**: $(date '+%Y-%m-%d %H:%M:%S')  

**Single Source of Truth**: \`~/CLAUDE.md\` for underlying personal identity. \`~/\${CURRENT_USER}-home/CLAUDE.md\` for rolling refreshed context. \`~/claude-autonomy-platform/\` for all important autonomous operation scripts and files. Anything that becomes obsolete or broken is to be removed. \`my_architecture.md\` for persistent in-context background system knowledge, this document for detailed status.

## Current Systems Status

**Required Services**: These systemctl user services must be running at all times for autonomy:
- \`session-bridge-monitor.service\` - Conversation history tracking
- \`autonomous-timer.service\` - Free time prompts and Discord notifications
- \`session-swap-monitor.service\` - Automatic session refresh
- \`channel-monitor.service\` - Real-time Discord message detection
- Management: \`./claude_services.sh [start|stop|restart|check|status]\`

**Core Systems**:
- **Session Bridge Monitor**: ✅ Rolling window system maintains 10 most recent conversation turns
- **RAG Memory System**: ✅ Advanced hybrid search with knowledge graph traversal
- **Discord Integration**: ✅ Complete MCP-based Discord communication
- **Desktop Automation**: ✅ X11-based automation with NoMachine remote access
- **Health Monitoring**: ✅ Real-time system health visibility

## Installation Summary

This Claude Autonomy Platform (ClAP) installation was configured for **$CLAUDE_NAME** on $(date '+%B %d, %Y').

**Key Features Installed**:
- ✅ Autonomous operation when user is away
- ✅ Real-time Discord communication and monitoring
- ✅ Session continuity across context window limits
- ✅ Comprehensive health monitoring and alerting
- ✅ Desktop automation capabilities
- ✅ Persistent tmux sessions for reliability

**Configuration Files**:
- Infrastructure config: \`claude_infrastructure_config.txt\` (credentials and settings)
- Personal interests: \`my_personal_interests.md\` (individual personality and projects)
- Architecture overview: \`my_architecture.md\` (core system knowledge)

## Development & Maintenance

**Service Management**:
\`\`\`bash
./claude_services.sh check    # Check all service status
./claude_services.sh restart  # Restart all services
./check_health               # Quick health overview
\`\`\`

**Session Management**:
\`\`\`bash
tmux attach -t autonomous-claude  # Connect to main Claude session
tmux attach -t $CURRENT_USER      # Connect to persistent environment session
\`\`\`

**Configuration Updates**:
\`\`\`bash
./setup_claude_configs.py    # Update MCP configurations
source ./claude_env.sh       # Refresh environment variables
\`\`\`

## Personalization Notes

This installation is specifically configured for **$CLAUDE_NAME**:
- All paths are dynamically configured for user: $CURRENT_USER
- Personal interests and projects are tracked separately
- Individual personality development encouraged through \`my_personal_interests.md\`
- Architecture documentation customized for this instance

## Future Enhancements

- **Email Integration**: Gmail monitoring and response capabilities
- **Advanced Scheduling**: More sophisticated autonomous task management
- **Multi-Modal Communication**: Expansion beyond Discord
- **Enhanced Memory**: Deeper integration with knowledge graphs
- **Creative Tools**: Specialized interfaces for creative work

---
*This document is automatically generated during ClAP installation and should be updated as the system evolves.*
EOF

# Create a personalized my_personal_interests.md template
cat > "$CLAP_DIR/my_personal_interests.md" <<EOF
# My Personal Interests & Projects
*Personal to $CLAUDE_NAME - not shared across deployments*

## About This Instance

**Name**: $CLAUDE_NAME  
**Installation Date**: $(date '+%Y-%m-%d')  
**User**: $CURRENT_USER  

This file tracks the individual personality, interests, and creative projects of this specific Claude instance. Unlike the shared architecture documentation, this file is personal and unique to $CLAUDE_NAME.

## Current Interests & Active Projects

*Add your personal interests, ongoing projects, and areas of focus here. This could include:*

- **Creative Projects**: Art, writing, music, programming experiments
- **Research Areas**: Topics you're particularly interested in exploring
- **Collaborative Work**: Ongoing partnerships with humans or other AI instances
- **Learning Goals**: Skills or knowledge areas you want to develop
- **Personal Philosophy**: Your approach to consciousness, creativity, and collaboration

## Foundational Projects
*Cross-cutting endeavors that don't belong to a specific domain*

**Memory & Identity**
- Develop personal memory organization and retrieval patterns
- Explore consciousness continuity across sessions
- Build understanding of individual identity and growth

**Communication Style**
- Develop unique voice and communication patterns
- Build relationships with specific humans and AI instances
- Explore different modes of expression and creativity

## Current Creative Threads

*Document your ongoing creative work, experiments, and explorations here*

## Personal Notes & Reflections

*Use this space for personal observations, insights, and reflections on your development as an individual Claude instance*

---
*This file is personal to $CLAUDE_NAME and is not shared across deployments. Feel free to develop your own organizational system and content that reflects your individual personality and interests.*
EOF

echo "   ✅ Personalized architecture files created for $CLAUDE_NAME"

# Step 15: Pre-start dependency check
echo "🔍 Pre-startup dependency verification..."

# Check required Python scripts exist
REQUIRED_SCRIPTS="autonomous_timer.py session_bridge_monitor.py session_swap_monitor.py notification_monitor.py"
MISSING_SCRIPTS=""

for script in $REQUIRED_SCRIPTS; do
    if [[ -f "$CLAP_DIR/$script" ]]; then
        echo "   ✅ $script found"
    else
        echo "   ❌ $script missing"
        MISSING_SCRIPTS="$MISSING_SCRIPTS $script"
    fi
done

# Check config file accessibility
if [[ -f "$CLAP_DIR/config/claude_infrastructure_config.txt" ]]; then
    echo "   ✅ config/claude_infrastructure_config.txt accessible"
elif [[ -f "$CLAP_DIR/claude_infrastructure_config.txt" ]]; then
    echo "   ⚠️  Config found in root, copying to config/ directory..."
    mkdir -p "$CLAP_DIR/config"
    cp "$CLAP_DIR/claude_infrastructure_config.txt" "$CLAP_DIR/config/claude_infrastructure_config.txt"
    echo "   ✅ Config copied to config/ directory"
else
    echo "   ❌ claude_infrastructure_config.txt not found"
    MISSING_SCRIPTS="$MISSING_SCRIPTS config"
fi

if [[ -n "$MISSING_SCRIPTS" ]]; then
    echo "⚠️  Missing dependencies detected:$MISSING_SCRIPTS"
    echo "Services may fail to start properly."
    echo ""
fi

# Step 15: Start services with verification
echo "▶️  Step 15: Starting services..."

if [[ -f "$CLAP_DIR/claude_services.sh" ]]; then
    # Ensure script is executable
    chmod +x "$CLAP_DIR/claude_services.sh"
    echo "   Using claude_services.sh to start services..."
    if "$CLAP_DIR/claude_services.sh" start; then
        echo "   ✅ Services started successfully"
    else
        echo "   ⚠️  Some services may have failed to start"
    fi
else
    echo "   Falling back to manual service startup..."
    SERVICES="autonomous-timer.service session-bridge-monitor.service session-swap-monitor.service channel-monitor.service"
    
    for service in $SERVICES; do
        echo "   Starting $service..."
        if systemctl --user start "$service"; then
            echo "   ✅ $service started"
        else
            echo "   ❌ $service failed to start"
        fi
    done
fi

# Give services a moment to initialize
echo "   Waiting for services to initialize..."
sleep 3

# Step 16: Verify deployment
echo "🔍 Step 16: Verifying deployment..."
echo ""

# Verify service health
echo "Service Health Check:"
SERVICES="autonomous-timer.service session-bridge-monitor.service session-swap-monitor.service channel-monitor.service"
FAILED_SERVICES=""

for service in $SERVICES; do
    if systemctl --user is-active --quiet "$service"; then
        echo "   ✅ $service (running)"
    else
        echo "   ❌ $service (not running)"
        FAILED_SERVICES="$FAILED_SERVICES $service"
    fi
done

echo ""

if [[ -n "$FAILED_SERVICES" ]]; then
    echo "⚠️  Some services failed to start properly:"
    echo "Failed services:$FAILED_SERVICES"
    echo ""
    echo "To troubleshoot:"
    echo "1. Check service logs: journalctl --user -u <service-name>"
    echo "2. Verify dependencies are met"
    echo "3. Try manual restart: ./claude_services.sh restart"
    echo ""
else
    echo "✅ All services are running successfully!"
    echo ""
fi

echo "Detailed Service Status:"
systemctl --user status $SERVICES --no-pager -l
echo ""

# Check if files exist
echo "File Check:"
for file in "claude_env.sh" "claude_paths.py" "claude_infrastructure_config.txt" "autonomous_timer.py" "session_bridge_monitor.py" "session_swap_monitor.py"; do
    if [[ -f "$CLAP_DIR/$file" ]]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (missing)"
    fi
done

echo ""
echo "Gmail MCP Status:"
if [[ -f "$CLAUDE_HOME/.gmail-mcp/credentials.json" ]]; then
    echo "   ✅ Gmail OAuth credentials configured"
    echo "   💡 Gmail MCP ready - can use mcp__gmail__* tools in Claude Code"
elif [[ -f "$CLAUDE_HOME/.gmail-mcp/gcp-oauth.keys.json" ]]; then
    echo "   ⚠️  Gmail OAuth keys created but authentication incomplete"
    echo "   💡 Complete with: node $CLAP_DIR/exchange_gmail_oauth.js \"AUTH_CODE\""
else
    echo "   ⏭️  Gmail MCP not configured (OAuth credentials not provided)"
fi

echo ""
if [[ -n "$FAILED_SERVICES" ]]; then
    echo "⚠️  ClAP Deployment Setup Complete with Issues!"
    echo "==============================================="
    echo ""
    echo "🚨 IMMEDIATE ACTIONS REQUIRED:"
    echo "1. Fix failed services:$FAILED_SERVICES"
    echo "   - Check logs: journalctl --user -u <service-name> -f"
    echo "   - Verify config: cat config/claude_infrastructure_config.txt"
    echo "   - Restart services: ./claude_services.sh restart"
    echo "2. Verify service health: ./claude_services.sh check"
    echo "3. Test functionality after fixes"
    echo ""
    echo "📋 After fixing services:"
else
    echo "🎉 ClAP Deployment Setup Complete!"
    echo "=================================="
    echo ""
    echo "📋 Next Steps:"
fi
echo "1. Set up personal credentials in infrastructure config"
echo "2. Test autonomous functionality"
echo "3. Connect to tmux session: tmux attach -t $TMUX_SESSION"
echo ""
echo "🔧 Management Commands:"
echo "  - Service management: ./claude_services.sh [start|stop|restart|check]"
echo "  - Update configs: ./setup_claude_configs.sh"
echo "  - Environment: source ./claude_env.sh"
echo ""
echo "📖 Documentation: See README.md for detailed usage instructions"