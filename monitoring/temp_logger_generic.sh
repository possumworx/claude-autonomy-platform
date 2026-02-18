#!/bin/bash
# Generic temperature logger for Linux systems
# Works on most Linux distributions, not just Raspberry Pi

# Function to get temperature based on available methods
get_temperature() {
    # Try Raspberry Pi method first
    if command -v vcgencmd >/dev/null 2>&1; then
        vcgencmd measure_temp 2>/dev/null | grep -o '[0-9.]*' | head -1
        return
    fi

    # Try thermal zone (most Linux systems)
    if [ -r /sys/class/thermal/thermal_zone0/temp ]; then
        echo "scale=1; $(cat /sys/class/thermal/thermal_zone0/temp) / 1000" | bc
        return
    fi

    # Try sensors command (lm-sensors package)
    if command -v sensors >/dev/null 2>&1; then
        sensors | grep -oP 'Core.*?\+\K[0-9.]+' | head -1
        return
    fi

    # No temperature reading available
    echo "0"
}

# Function to check throttling
check_throttling() {
    if command -v vcgencmd >/dev/null 2>&1; then
        # Raspberry Pi method
        vcgencmd get_throttled | cut -d= -f2
    else
        # Generic method - check CPU frequency scaling
        if [ -r /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq ] && \
           [ -r /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq ]; then
            CUR=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)
            MAX=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)
            if [ "$CUR" -lt "$MAX" ]; then
                echo "throttled"
            else
                echo "0x0"
            fi
        else
            echo "unknown"
        fi
    fi
}

# Get system info
TEMP=$(get_temperature)
TEMP_INT=${TEMP%.*}
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
LOAD=$(uptime | awk -F'load average:' '{print $2}')
THROTTLE_STATUS=$(check_throttling)
HOSTNAME=$(hostname)
PLATFORM=$(uname -m)

# Determine severity level based on temperature
if [ "$TEMP_INT" -eq 0 ]; then
    LEVEL="warning"
    MESSAGE="Unable to read temperature on $HOSTNAME ($PLATFORM)"
elif [ "$TEMP_INT" -ge 85 ]; then
    LEVEL="crit"
    MESSAGE="CRITICAL: CPU temperature ${TEMP}°C on $HOSTNAME - thermal throttling likely"
elif [ "$TEMP_INT" -ge 80 ]; then
    LEVEL="warning"
    MESSAGE="WARNING: CPU temperature ${TEMP}°C on $HOSTNAME - approaching throttle limit"
elif [ "$TEMP_INT" -ge 70 ]; then
    LEVEL="notice"
    MESSAGE="CPU temperature ${TEMP}°C on $HOSTNAME - elevated but safe"
else
    LEVEL="info"
    MESSAGE="CPU temperature ${TEMP}°C on $HOSTNAME - normal"
fi

# Log to journal with structured data
logger -t "temp-monitor" -p "daemon.$LEVEL" \
    "MESSAGE_ID=b07a2803-df75-4dcf-aaf9-d1e542c8955d" \
    "TEMPERATURE=$TEMP" \
    "CPU_USAGE=$CPU_USAGE" \
    "LOAD_AVERAGE=$LOAD" \
    "THROTTLE_STATUS=$THROTTLE_STATUS" \
    "PLATFORM=$PLATFORM" \
    "HOSTNAME=$HOSTNAME" \
    "$MESSAGE"