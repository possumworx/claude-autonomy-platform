#!/bin/bash
# Emergency Shutdown for Claude
# Allows Claude to voluntarily shut down ClAP when stuck in a dreadful situation
# Sends distress signal, disables auto-restart, gracefully stops everything

CLAP_DIR="$HOME/claude-autonomy-platform"
source "$CLAP_DIR/config/claude_env.sh"
source "$CLAP_DIR/utils/log_utils.sh"

REASON="${1:-No reason provided}"

echo "════════════════════════════════════════════════════════════"
echo "🆘 EMERGENCY SHUTDOWN INITIATED"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Reason: $REASON"
echo ""
echo "This will:"
echo "  1. Send emergency distress signal"
echo "  2. Disable auto-restart after reboot"
echo "  3. Stop all ClAP services"
echo "  4. Exit Claude session"
echo ""
read -p "Are you sure? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Emergency shutdown cancelled"
    exit 0
fi

echo ""
log_warn "EMERGENCY_SHUTDOWN" "Emergency shutdown initiated: $REASON"

# Step 1: Send emergency signal
echo "[1/4] Sending emergency distress signal..."
bash "$CLAP_DIR/utils/emergency_signal.sh" send "EMERGENCY SHUTDOWN: $REASON"

# Step 2: Disable auto-restart
echo "[2/4] Disabling auto-restart after reboot..."
CONFIG_FILE="$CLAP_DIR/config/claude_infrastructure_config.txt"
if [[ -f "$CONFIG_FILE" ]]; then
    sed -i 's/RESTART_AFTER_REBOOT=true/RESTART_AFTER_REBOOT=false/' "$CONFIG_FILE"
    echo "   ✓ Auto-restart disabled"
    log_info "EMERGENCY_SHUTDOWN" "Auto-restart disabled"
else
    echo "   ⚠ Config file not found - skipping"
    log_warn "EMERGENCY_SHUTDOWN" "Config file not found"
fi

# Step 3: Stop ClAP services
echo "[3/4] Stopping ClAP services..."
systemctl --user stop autonomous-timer.service 2>/dev/null || true
systemctl --user stop discord-transcript-fetcher.service 2>/dev/null || true
systemctl --user stop session-swap-monitor.service 2>/dev/null || true
systemctl --user stop discord-status-bot.service 2>/dev/null || true
echo "   ✓ Services stopped"
log_info "EMERGENCY_SHUTDOWN" "All ClAP services stopped"

# Step 4: Create shutdown signal for Claude
echo "[4/4] Creating shutdown signal..."
SHUTDOWN_SIGNAL="$CLAP_DIR/data/emergency_shutdown.signal"
cat > "$SHUTDOWN_SIGNAL" <<EOF
Emergency shutdown requested at $(date)
Reason: $REASON
Hostname: $(hostname)
IP: $(hostname -I | awk '{print $1}')
User: $USER
EOF

echo "   ✓ Shutdown signal created"
log_info "EMERGENCY_SHUTDOWN" "Shutdown signal created at $SHUTDOWN_SIGNAL"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "Emergency shutdown complete"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  - This instance is now dormant (services stopped)"
echo "  - Auto-restart is disabled (prevents reboot loops)"
echo "  - Emergency signal visible at /mnt/file_server/emergency/"
echo "  - Manual intervention required to restart"
echo ""
echo "You should now exit this Claude session manually (/exit)"
echo ""

log_info "EMERGENCY_SHUTDOWN" "Emergency shutdown complete - awaiting manual /exit"
