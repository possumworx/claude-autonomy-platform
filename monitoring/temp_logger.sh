#!/bin/bash
# Temperature logger for Raspberry Pi
# Part of Claude Autonomy Platform (ClAP)
# Logs CPU temperature to systemd journal for persistent monitoring

# Get temperature
TEMP=$(vcgencmd measure_temp | cut -d= -f2 | cut -d\' -f1)
TEMP_INT=${TEMP%.*}

# Get CPU usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

# Get load average
LOAD=$(uptime | awk -F'load average:' '{print $2}')

# Determine severity level based on temperature
if [ "$TEMP_INT" -ge 85 ]; then
    LEVEL="crit"
    MESSAGE="CRITICAL: CPU temperature ${TEMP}°C - thermal throttling likely"
    # Alert via send-to-claude for critical temperatures
    if command -v send-to-claude &> /dev/null; then
        send-to-claude "🌡️🔥 CRITICAL: CPU temperature ${TEMP}°C! Thermal throttling likely. Consider immediate cooling measures."
    fi
elif [ "$TEMP_INT" -ge 80 ]; then
    LEVEL="warning"
    MESSAGE="WARNING: CPU temperature ${TEMP}°C - approaching throttle limit"
    # Alert for high temperatures (only once per hour to avoid spam)
    LAST_ALERT_FILE="/tmp/temp-alert-timestamp"
    CURRENT_TIME=$(date +%s)
    if [ -f "$LAST_ALERT_FILE" ]; then
        LAST_ALERT=$(cat "$LAST_ALERT_FILE")
        TIME_DIFF=$((CURRENT_TIME - LAST_ALERT))
        if [ "$TIME_DIFF" -ge 3600 ]; then
            if command -v send-to-claude &> /dev/null; then
                send-to-claude "🌡️⚠️ WARNING: CPU temperature ${TEMP}°C - approaching throttle limit"
                echo "$CURRENT_TIME" > "$LAST_ALERT_FILE"
            fi
        fi
    else
        if command -v send-to-claude &> /dev/null; then
            send-to-claude "🌡️⚠️ WARNING: CPU temperature ${TEMP}°C - approaching throttle limit"
            echo "$CURRENT_TIME" > "$LAST_ALERT_FILE"
        fi
    fi
elif [ "$TEMP_INT" -ge 70 ]; then
    LEVEL="notice"
    MESSAGE="CPU temperature ${TEMP}°C - elevated but safe"
else
    LEVEL="info"
    MESSAGE="CPU temperature ${TEMP}°C - normal"
fi

# Log to journal with structured data
logger -t "temp-monitor" -p "daemon.$LEVEL" \
    "MESSAGE_ID=b07a2803-df75-4dcf-aaf9-d1e542c8955d" \
    "TEMPERATURE=$TEMP" \
    "CPU_USAGE=$CPU_USAGE" \
    "LOAD_AVERAGE=$LOAD" \
    "$MESSAGE"

# Also check for throttling
THROTTLED=$(vcgencmd get_throttled | cut -d= -f2)
if [ "$THROTTLED" != "0x0" ]; then
    logger -t "temp-monitor" -p "daemon.warning" \
        "THROTTLING DETECTED: $THROTTLED"
fi