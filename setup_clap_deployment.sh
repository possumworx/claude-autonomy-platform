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

# Step 13: Start services
echo "▶️  Step 13: Starting services..."
"$CLAP_DIR/claude_services.sh" start

# Step 14: Verify deployment
echo "🔍 Step 14: Verifying deployment..."
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