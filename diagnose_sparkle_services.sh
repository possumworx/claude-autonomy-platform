#!/bin/bash
# Quick diagnostic script for sparkle-sonnet's services

echo "🔍 Checking sparkle-sonnet's ClAP services..."
echo "============================================"
echo ""

# Check if services are actually working
echo "📊 Service Health:"
systemctl --user status autonomous-timer.service --no-pager -n 10
echo ""

# Check logs for errors
echo "📝 Recent autonomous-timer logs:"
journalctl --user -u autonomous-timer.service -n 20 --no-pager
echo ""

echo "📝 Recent session-bridge-monitor logs:"
journalctl --user -u session-bridge-monitor.service -n 20 --no-pager
echo ""

# Check if required files exist
echo "📁 Required files check:"
for file in "autonomous_timer.py" "session_bridge_monitor.py" "claude_infrastructure_config.txt" "claude_env.sh"; do
    if [[ -f "$HOME/Claude-Autonomy-Platform/$file" ]]; then
        echo "  ✅ $file exists"
    else
        echo "  ❌ $file missing!"
    fi
done
echo ""

# Check environment file
echo "🌍 Checking claude_env.sh:"
if [[ -f "$HOME/Claude-Autonomy-Platform/claude_env.sh" ]]; then
    echo "  First few lines:"
    head -5 "$HOME/Claude-Autonomy-Platform/claude_env.sh"
else
    echo "  ❌ claude_env.sh not found!"
fi
