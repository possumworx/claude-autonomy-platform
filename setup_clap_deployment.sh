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
    echo "   ✅ Configuration file imported"
    echo ""
elif [[ ! -f "$SCRIPT_DIR/claude_infrastructure_config.txt" ]]; then
    echo "❌ No configuration file found!"
    echo ""
    if [[ -f "$SCRIPT_DIR/claude_infrastructure_config.template.txt" ]]; then
        echo "📋 Template file found. You can:"
        echo "1. Copy template and edit: cp claude_infrastructure_config.template.txt claude_infrastructure_config.txt"
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

# Create autonomous-timer.service
cat > "$SYSTEMD_USER_DIR/autonomous-timer.service" <<EOF
[Unit]
Description=Autonomous Timer for Claude
After=network.target

[Service]
Type=simple
WorkingDirectory=$CLAP_DIR
ExecStart=/usr/bin/python3 $CLAP_DIR/autonomous_timer.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
EnvironmentFile=$CLAP_DIR/claude_env.sh

[Install]
WantedBy=default.target
EOF

# Create session-bridge-monitor.service
cat > "$SYSTEMD_USER_DIR/session-bridge-monitor.service" <<EOF
[Unit]
Description=Session Bridge Monitor for Claude
After=network.target

[Service]
Type=simple
WorkingDirectory=$CLAP_DIR
ExecStart=/usr/bin/python3 $CLAP_DIR/session_bridge_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
EnvironmentFile=$CLAP_DIR/claude_env.sh

[Install]
WantedBy=default.target
EOF

# Create session-swap-monitor.service
cat > "$SYSTEMD_USER_DIR/session-swap-monitor.service" <<EOF
[Unit]
Description=Session Swap Monitor for Claude
After=network.target

[Service]
Type=simple
WorkingDirectory=$CLAP_DIR
ExecStart=/usr/bin/python3 $CLAP_DIR/session_swap_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
EnvironmentFile=$CLAP_DIR/claude_env.sh

[Install]
WantedBy=default.target
EOF

cat > "$SYSTEMD_USER_DIR/notification-monitor.service" <<EOF
[Unit]
Description=Claude Notification Monitor
After=network.target

[Service]
Type=simple
User=$CLAUDE_USER
WorkingDirectory=$CLAP_DIR
Environment=PATH=$CLAUDE_HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=DISCORD_HEADLESS=true
EnvironmentFile=-$CLAP_DIR/claude_infrastructure_config.txt
ExecStart=/usr/bin/python3 $CLAP_DIR/notification_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

echo "   ✅ Systemd service files created"

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

# Step 7: Set up tmux session for continuity
echo "🖥️  Step 7: Setting up tmux session..."
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
PERSISTENT_SESSION="sonnet-4"
if ! tmux has-session -t "$PERSISTENT_SESSION" 2>/dev/null; then
    echo "   Creating persistent user session '$PERSISTENT_SESSION'..."
    tmux new-session -d -s "$PERSISTENT_SESSION" -c "$HOME"
    tmux send-keys -t "$PERSISTENT_SESSION" "# Persistent session for environment variables" Enter
    echo "   ✅ Persistent session '$PERSISTENT_SESSION' created"
else
    echo "   ✅ Persistent session '$PERSISTENT_SESSION' already exists"
fi

# Step 8: Install NoMachine (optional but recommended)
echo "🖥️  Step 8: Installing NoMachine..."
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

# Step 9: Configure auto-login (requires sudo)
echo "🔐 Step 9: Configuring auto-login..."
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

# Step 10: Configure X11 as default session
echo "🖼️  Step 10: Configuring X11 as default session..."
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

# Step 11: Reload systemd and enable services
echo "🔄 Step 11: Enabling and starting services..."
systemctl --user daemon-reload

# Enable services
systemctl --user enable autonomous-timer.service
systemctl --user enable session-bridge-monitor.service
systemctl --user enable session-swap-monitor.service
systemctl --user enable notification-monitor.service

echo "   ✅ Services enabled"

# Step 12: Set up cron jobs
echo "⏰ Step 12: Setting up cron jobs..."

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

# Step 13: Create personalized architecture and status files
echo "👤 Step 13: Creating personalized architecture and status files..."

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
- \`notification-monitor.service\` - Real-time Discord message detection and unread management

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
- \`notification-monitor.service\` - Real-time Discord message detection
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

# Step 14: Start services
echo "▶️  Step 14: Starting services..."
"$CLAP_DIR/claude_services.sh" start

# Step 15: Verify deployment
echo "🔍 Step 15: Verifying deployment..."
echo ""
echo "Service Status:"
systemctl --user status autonomous-timer.service session-bridge-monitor.service session-swap-monitor.service --no-pager -l
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
echo "🎉 ClAP Deployment Setup Complete!"
echo "=================================="
echo ""
echo "📋 Next Steps:"
echo "1. Verify all services are running: ./claude_services.sh check"
echo "2. Set up personal credentials in infrastructure config"
echo "3. Test autonomous functionality"
echo "4. Connect to tmux session: tmux attach -t $TMUX_SESSION"
echo ""
echo "🔧 Management Commands:"
echo "  - Service management: ./claude_services.sh [start|stop|restart|check]"
echo "  - Update configs: ./setup_claude_configs.sh"
echo "  - Environment: source ./claude_env.sh"
echo ""
echo "📖 Documentation: See README.md for detailed usage instructions"