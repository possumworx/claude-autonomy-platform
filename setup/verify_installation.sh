#!/bin/bash
# ClAP Comprehensive Installation Verification Script
# Implements POSS-121: Comprehensive post-install verification

echo "🔍 ClAP Installation Verification"
echo "================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$(dirname "$SCRIPT_DIR")"

# Initialize counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
pass() {
    echo -e "   ${GREEN}✅ $1${NC}"
    ((PASS_COUNT++))
}

fail() {
    echo -e "   ${RED}❌ $1${NC}"
    ((FAIL_COUNT++))
}

warn() {
    echo -e "   ${YELLOW}⚠️  $1${NC}"
    ((WARN_COUNT++))
}

# Create verification log
LOG_FILE="$CLAP_DIR/data/install_verification.log"
mkdir -p "$CLAP_DIR/data"
echo "ClAP Installation Verification - $(date)" > "$LOG_FILE"
echo "=====================================" >> "$LOG_FILE"

# 1. Python Dependencies Check
echo "📦 1. Testing Python Dependencies..."
echo "" >> "$LOG_FILE"
echo "Python Dependencies:" >> "$LOG_FILE"

# Basic imports
if python3 -c "import json, time, glob, os, sys" 2>/dev/null; then
    pass "Basic Python imports successful"
    echo "✅ Basic imports: json, time, glob, os, sys" >> "$LOG_FILE"
else
    fail "Basic Python imports failed"
    echo "❌ Basic imports failed" >> "$LOG_FILE"
fi

# Core script imports
for script in autonomous_timer session_bridge_monitor session_swap_monitor; do
    if python3 -c "import sys; sys.path.append('$CLAP_DIR'); from core.$script import *" 2>/dev/null; then
        pass "$script imports successfully"
        echo "✅ $script imports successfully" >> "$LOG_FILE"
    else
        fail "$script import failed"
        echo "❌ $script import failed" >> "$LOG_FILE"
        # Get detailed error
        python3 -c "import sys; sys.path.append('$CLAP_DIR'); from core.$script import *" 2>&1 | tail -5 >> "$LOG_FILE"
    fi
done

# Channel monitor import (different location)
# Channel monitor functionality now integrated into autonomous_timer
# No separate import test needed

echo ""

# 2. MCP Server Binaries Check
echo "🔌 2. Checking MCP Server Binaries..."
echo "" >> "$LOG_FILE"
echo "MCP Servers:" >> "$LOG_FILE"

MCP_DIR="$CLAP_DIR/mcp-servers"

# Check Discord MCP
if [[ -f "$MCP_DIR/discord-mcp/target/discord-mcp-0.0.1-SNAPSHOT.jar" ]]; then
    pass "Discord MCP binary found"
    echo "✅ Discord MCP: discord-mcp-0.0.1-SNAPSHOT.jar" >> "$LOG_FILE"
else
    fail "Discord MCP binary missing"
    echo "❌ Discord MCP binary missing" >> "$LOG_FILE"
fi

# Check RAG Memory MCP
if [[ -f "$MCP_DIR/rag-memory-mcp/dist/index.js" ]]; then
    pass "RAG Memory MCP binary found"
    echo "✅ RAG Memory MCP: dist/index.js" >> "$LOG_FILE"
else
    fail "RAG Memory MCP binary missing"
    echo "❌ RAG Memory MCP binary missing" >> "$LOG_FILE"
fi

# Check Linear MCP
if [[ -f "$MCP_DIR/linear-mcp/build/index.js" ]]; then
    pass "Linear MCP binary found"
    echo "✅ Linear MCP: build/index.js" >> "$LOG_FILE"
else
    fail "Linear MCP binary missing"
    echo "❌ Linear MCP binary missing" >> "$LOG_FILE"
fi

# Check Gmail MCP
if [[ -f "$MCP_DIR/gmail-mcp/dist/index.js" ]]; then
    pass "Gmail MCP binary found"
    echo "✅ Gmail MCP: dist/index.js" >> "$LOG_FILE"
else
    fail "Gmail MCP binary missing"
    echo "❌ Gmail MCP binary missing" >> "$LOG_FILE"
fi

echo ""

# 3. Service Health Check
echo "🚀 3. Verifying Services..."
echo "" >> "$LOG_FILE"
echo "Services:" >> "$LOG_FILE"

for service in autonomous-timer session-swap-monitor; do
    if systemctl --user is-active --quiet "$service.service"; then
        pass "$service is running"
        echo "✅ $service is running" >> "$LOG_FILE"
        # Get PID for log
        PID=$(systemctl --user show "$service.service" --property MainPID --value)
        echo "   PID: $PID" >> "$LOG_FILE"
    else
        fail "$service is not running"
        echo "❌ $service is not running" >> "$LOG_FILE"
        # Get failure reason
        systemctl --user status "$service.service" --no-pager -n 5 >> "$LOG_FILE" 2>&1
    fi
done

# Check systemd lingering
if loginctl show-user $USER | grep -q "Linger=yes"; then
    pass "Systemd lingering enabled (services will start on boot)"
    echo "✅ Systemd lingering enabled" >> "$LOG_FILE"
else
    fail "Systemd lingering NOT enabled (services won't start without login)"
    echo "❌ Systemd lingering NOT enabled" >> "$LOG_FILE"
    echo "   Fix with: sudo loginctl enable-linger $USER" >> "$LOG_FILE"
fi

echo ""

# 4. Configuration Files Check
echo "📄 4. Checking Configuration Files..."
echo "" >> "$LOG_FILE"
echo "Configuration:" >> "$LOG_FILE"

CONFIG_DIR="$CLAP_DIR/config"

# Critical config files
declare -A config_files=(
    ["claude_env.sh"]="Environment variables"
    ["claude_infrastructure_config.txt"]="Infrastructure configuration"
    ["channel_state.json"]="Discord channel state"
)

for file in "${!config_files[@]}"; do
    if [[ "$file" == "channel_state.json" ]]; then
        filepath="$CLAP_DIR/data/$file"
    else
        filepath="$CONFIG_DIR/$file"
    fi
    
    if [[ -f "$filepath" ]]; then
        pass "${config_files[$file]} found"
        echo "✅ $file: ${config_files[$file]}" >> "$LOG_FILE"
    else
        fail "${config_files[$file]} missing"
        echo "❌ $file: ${config_files[$file]} missing" >> "$LOG_FILE"
    fi
done

echo ""

# 5. File Permissions Check
echo "🔐 5. Verifying File Permissions..."
echo "" >> "$LOG_FILE"
echo "Permissions:" >> "$LOG_FILE"

# Check if user can write to critical directories
for dir in "$CLAP_DIR/data" "$CLAP_DIR/logs" "$CONFIG_DIR"; do
    if [[ -w "$dir" ]]; then
        pass "Write access to $(basename $dir)/"
        echo "✅ Write access to $dir" >> "$LOG_FILE"
    else
        fail "No write access to $(basename $dir)/"
        echo "❌ No write access to $dir" >> "$LOG_FILE"
    fi
done

echo ""

# 6. Discord Token Check
echo "💬 6. Checking Discord Configuration..."
echo "" >> "$LOG_FILE"
echo "Discord:" >> "$LOG_FILE"

# Check for Discord token in environment
if [[ -f "$CONFIG_DIR/claude_infrastructure_config.txt" ]]; then
    if grep -q "DISCORD_TOKEN=" "$CONFIG_DIR/claude_infrastructure_config.txt" && \
       grep "DISCORD_TOKEN=" "$CONFIG_DIR/claude_infrastructure_config.txt" | grep -qv "DISCORD_TOKEN=$\|DISCORD_TOKEN=\"\""; then
        pass "Discord token configured"
        echo "✅ Discord token found in config" >> "$LOG_FILE"
    else
        warn "Discord token not configured"
        echo "⚠️  Discord token not configured" >> "$LOG_FILE"
    fi
else
    fail "Infrastructure config missing"
    echo "❌ Infrastructure config missing" >> "$LOG_FILE"
fi

echo ""

# 7. Tmux Sessions Check
echo "🖥️  7. Checking Tmux Sessions..."
echo "" >> "$LOG_FILE"
echo "Tmux Sessions:" >> "$LOG_FILE"

for session in "autonomous-claude" "persistent-login"; do
    if tmux has-session -t "$session" 2>/dev/null; then
        pass "Tmux session '$session' exists"
        echo "✅ Tmux session '$session' exists" >> "$LOG_FILE"
    else
        fail "Tmux session '$session' missing"
        echo "❌ Tmux session '$session' missing" >> "$LOG_FILE"
    fi
done

echo ""

# 8. Natural Commands Check
echo "🛠️  8. Verifying Natural Commands..."
echo "" >> "$LOG_FILE"
echo "Natural Commands:" >> "$LOG_FILE"

# Check if ~/bin is in PATH
if [[ ":$PATH:" == *":$HOME/bin:"* ]]; then
    pass "~/bin is in PATH"
    echo "✅ ~/bin is in PATH" >> "$LOG_FILE"
else
    warn "~/bin not in PATH (run: source ~/.bashrc)"
    echo "⚠️  ~/bin not in PATH" >> "$LOG_FILE"
fi

# Check natural commands
declare -a commands=("check_health" "read_channel" "write_channel" "swap" "claude_services")
for cmd in "${commands[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        pass "Command '$cmd' available"
        echo "✅ Command '$cmd' available" >> "$LOG_FILE"
    else
        fail "Command '$cmd' not found"
        echo "❌ Command '$cmd' not found" >> "$LOG_FILE"
    fi
done

echo ""

# Summary
echo "📊 Verification Summary"
echo "======================"
echo -e "   ${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "   ${YELLOW}Warnings: $WARN_COUNT${NC}"
echo -e "   ${RED}Failed: $FAIL_COUNT${NC}"
echo ""

# Write summary to log
echo "" >> "$LOG_FILE"
echo "Summary:" >> "$LOG_FILE"
echo "Passed: $PASS_COUNT" >> "$LOG_FILE"
echo "Warnings: $WARN_COUNT" >> "$LOG_FILE"
echo "Failed: $FAIL_COUNT" >> "$LOG_FILE"

if [[ $FAIL_COUNT -eq 0 ]]; then
    echo -e "${GREEN}✅ Installation verification passed!${NC}"
    echo "" >> "$LOG_FILE"
    echo "✅ Installation verification passed!" >> "$LOG_FILE"
    exit 0
else
    echo -e "${RED}❌ Installation verification failed with $FAIL_COUNT errors${NC}"
    echo "   See $LOG_FILE for details"
    echo "" >> "$LOG_FILE"
    echo "❌ Installation verification failed with $FAIL_COUNT errors" >> "$LOG_FILE"
    exit 1
fi