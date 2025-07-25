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

# Get the directory where this script is located (setup/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the ClAP root directory (parent of setup/)
CLAP_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$CLAP_DIR/config"

echo "📁 ClAP Directory: $CLAP_DIR"

# Step 0: Import configuration file if specified
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

# Copy service files from services/ directory
echo "   Copying service files..."
for service in autonomous-timer.service session-bridge-monitor.service session-swap-monitor.service channel-monitor.service; do
    if [[ -f "$CLAP_DIR/services/$service" ]]; then
        cp "$CLAP_DIR/services/$service" "$SYSTEMD_USER_DIR/"
        echo "   ✅ $service"
    else
        echo "   ❌ $service not found in services/ directory"
    fi
done

# Step 3: Set up persistent environment variables
echo "🌍 Step 3: Setting up persistent environment variables..."

# Generate claude.env from infrastructure config (POSS-76)
if [[ -f "$CLAP_DIR/utils/create_systemd_env.py" ]]; then
    echo "   Generating systemd-compatible environment file..."
    python3 "$CLAP_DIR/utils/create_systemd_env.py"
elif [[ ! -f "$CONFIG_DIR/claude.env" ]]; then
    echo "   ⚠️  Warning: claude.env not found and systemd env script not available"
fi

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

# Step 4: Install dependencies
echo "📦 Step 4: Installing dependencies..."
cd "$CLAP_DIR"

# Install npm dependencies if package.json exists
if [[ -f "package.json" ]]; then
    echo "   Installing npm dependencies..."
    npm install
    echo "   ✅ npm dependencies installed"
fi

# Install MCP servers (POSS-82)
echo "   Installing MCP servers..."
if [[ -f "$CLAP_DIR/setup/install_mcp_servers.sh" ]]; then
    bash "$CLAP_DIR/setup/install_mcp_servers.sh"
else
    echo "   ⚠️  MCP installer not found - install manually with:"
    echo "   $CLAP_DIR/setup/install_mcp_servers.sh"
fi

# Step 5: Disable desktop timeouts (for NoMachine/desktop automation)
echo "🖥️  Step 5: Disabling desktop timeouts..."
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

# Step 6: Run Claude configuration setup
echo "🔧 Step 6: Setting up Claude configurations..."

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

# Step 7: Set up tmux session for continuity
echo "🖥️  Step 7: Setting up tmux session..."
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

# Step 8: Install NoMachine (optional but recommended)
echo "🖥️  Step 8: Installing NoMachine..."
if ! command -v nxserver &> /dev/null; then
    echo "   ⚠️  NoMachine not installed. Download from https://nomachine.com"
    echo "   wget https://download.nomachine.com/download/8.14/Linux/nomachine_8.14.2_1_amd64.deb -O /tmp/nomachine.deb"
    echo "   sudo dpkg -i /tmp/nomachine.deb"
else
    echo "   ✅ NoMachine already installed"
fi

# Step 9: Configure auto-login (requires sudo)
echo "🔐 Step 9: Configuring auto-login..."
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
systemctl --user enable channel-monitor.service

echo "   ✅ Services enabled"

# Step 12: Set up cron jobs
echo "⏰ Step 12: Setting up cron jobs..."

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

# Step 12b: Set up utility commands in PATH (POSS-77, POSS-80)
echo "🔧 Setting up utility commands..."

# Create ~/bin directory if it doesn't exist
mkdir -p "$CLAUDE_HOME/bin"

# Symlink utility commands
echo "   Creating command symlinks..."
ln -sf "$CLAP_DIR/discord/read_channel" "$CLAUDE_HOME/bin/read_channel"
ln -sf "$CLAP_DIR/utils/healthcheck_status.py" "$CLAUDE_HOME/bin/check_health"
chmod +x "$CLAUDE_HOME/bin/read_channel"
chmod +x "$CLAUDE_HOME/bin/check_health"

# Add ~/bin to PATH if not already there
if ! grep -q 'export PATH="$HOME/bin:$PATH"' "$BASHRC" 2>/dev/null; then
    echo 'export PATH="$HOME/bin:$PATH"' >> "$BASHRC"
    echo "   ✅ Added ~/bin to PATH in .bashrc"
else
    echo "   ✅ ~/bin already in PATH"
fi

echo "   ✅ Utility commands configured"

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

## About This Instance

**Name**: $CLAUDE_NAME  
**Installation Date**: $(date '+%Y-%m-%d')  
**User**: $CURRENT_USER  

This file tracks the individual personality, interests, and creative projects of this specific Claude instance.
EOF
fi

echo "   ✅ Personalized files created for $CLAUDE_NAME"

# Step 14: Start services
echo "▶️  Step 14: Starting services..."
if [[ -f "$CLAP_DIR/utils/claude_services.sh" ]]; then
    "$CLAP_DIR/utils/claude_services.sh" start
else
    echo "   Starting services manually..."
    systemctl --user start autonomous-timer.service session-bridge-monitor.service session-swap-monitor.service channel-monitor.service
fi

# Step 15: Verify deployment
echo "🔍 Step 15: Verifying deployment..."
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
echo "1. Verify all services are running: $CLAP_DIR/utils/claude_services.sh check"
echo "2. Set up personal credentials in infrastructure config"
echo "3. Test autonomous functionality"
echo "4. Connect to tmux session: tmux attach -t $TMUX_SESSION"
echo ""
echo "🔧 Management Commands:"
echo "  - Service management: $CLAP_DIR/utils/claude_services.sh [start|stop|restart|check]"
echo "  - Update configs: $CLAP_DIR/setup/setup_claude_configs.sh"
echo "  - Environment: source $CONFIG_DIR/claude_env.sh"
echo ""
echo "📖 Documentation: See docs/README.md for detailed usage instructions"