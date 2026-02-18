# ClAP Temperature Monitoring

This directory contains temperature monitoring tools for Raspberry Pi deployments of Claude Autonomy Platform.

## Features

- **Automatic Temperature Logging**: Records CPU temperature, load, and throttling status every minute
- **Persistent Journaling**: Logs survive reboots for long-term analysis
- **Temperature Analysis**: Quick tool to view current status and historical trends

## Files

- `temp_logger.sh` - Main temperature logging script (runs every minute via systemd)
- `temp_logger_generic.sh` - Generic version for non-RPi Linux systems
- `temp_analysis.sh` - Analysis tool for viewing temperature trends

## Usage

### View Real-time Temperatures
```bash
journalctl -t temp-monitor -f
```

### Analyze Temperature History
```bash
temp_analysis  # After installation creates symlink
# or
~/claude-autonomy-platform/monitoring/temp_analysis.sh
```

### Check for Warnings
```bash
journalctl -t temp-monitor -p warning --since "1 hour ago"
```

### Export Temperature Data
```bash
journalctl -t temp-monitor --since yesterday -o json | jq -r '.TEMPERATURE'
```

## Temperature Thresholds

- **Normal**: < 70°C
- **Notice**: 70-79°C (elevated but safe)
- **Warning**: 80-84°C (approaching throttle limit)
- **Critical**: ≥ 85°C (thermal throttling active)

## Installation

The temperature monitoring is automatically set up by the ClAP installer on Raspberry Pi systems. The installer will:

1. Enable persistent journaling (requires sudo)
2. Install and enable the temp-logger systemd timer
3. Create the `temp_analysis` command

## Notes

- Raspberry Pi 5 runs hotter than previous models
- Good cooling is essential for autonomous 24/7 operation
- Consider the official RPi 5 Active Cooler or custom cooling solutions
- Monitor logs after installation to ensure temperatures stay below 80°C