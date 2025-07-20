#!/bin/bash
# Service Restart Script for Claude's Autonomy Infrastructure
# Run this to restart all required systemd user services
# Usage: ./restart_services.sh [check|restart|start|stop|status]

set -e

# Fix XDG_RUNTIME_DIR for systemctl user commands
export XDG_RUNTIME_DIR=/run/user/$(id -u)

SERVICES="autonomous-timer.service session-bridge-monitor.service session-swap-monitor.service notification-monitor.service"

echo "=== Claude Autonomy Service Manager ==="
echo "Services: $SERVICES"
echo "Timestamp: $(date)"
echo

case "${1:-restart}" in
    "check"|"status")
        echo "Checking service status..."
        systemctl --user status $SERVICES
        ;;
    "restart")
        echo "Restarting services..."
        systemctl --user restart $SERVICES
        echo "✅ Services restarted successfully"
        echo
        echo "Checking new status..."
        systemctl --user status $SERVICES --no-pager -l
        ;;
    "stop")
        echo "Stopping services..."
        systemctl --user stop $SERVICES
        echo "⏹️ Services stopped"
        ;;
    "start")
        echo "Starting services..."
        systemctl --user start $SERVICES
        echo "▶️ Services started"
        echo
        echo "Checking status..."
        systemctl --user status $SERVICES --no-pager -l
        ;;
    "help")
        echo "Usage: $0 [check|restart|start|stop|status|help]"
        echo "  check/status - Show service status"
        echo "  restart      - Restart all services (default)"
        echo "  start        - Start all services"
        echo "  stop         - Stop all services"
        echo "  help         - Show this help"
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

echo
echo "=== Operation Complete ==="