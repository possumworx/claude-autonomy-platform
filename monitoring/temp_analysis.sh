#!/bin/bash
# Temperature analysis tool for monitoring cooling effectiveness

echo "=== RPi5 Temperature Analysis ==="
echo "Current time: $(date)"
echo

# Current status
echo "=== Current Status ==="
CURRENT_TEMP=$(vcgencmd measure_temp | cut -d= -f2)
echo "Temperature: $CURRENT_TEMP"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Throttled: $(vcgencmd get_throttled | cut -d= -f2)"
echo

# Last hour statistics
echo "=== Last Hour Statistics ==="
journalctl -t temp-monitor --since "1 hour ago" -o json | \
    jq -r '.TEMPERATURE' 2>/dev/null | \
    awk '
        BEGIN { min=1000; max=0; sum=0; count=0 }
        {
            if ($1 != "") {
                sum+=$1; count++;
                if($1<min) min=$1;
                if($1>max) max=$1
            }
        }
        END {
            if (count > 0) {
                printf "Samples: %d\n", count
                printf "Min: %.1f°C\n", min
                printf "Max: %.1f°C\n", max
                printf "Avg: %.1f°C\n", sum/count
            } else {
                print "No data available yet"
            }
        }'

# Show any throttling events
echo
echo "=== Recent Throttling Events ==="
journalctl -t temp-monitor --since "1 hour ago" | grep -i throttl || echo "No throttling detected"

# Show temperature warnings
echo
echo "=== Recent Temperature Warnings ==="
journalctl -t temp-monitor -p warning --since "1 hour ago" | tail -5 || echo "No warnings"