# Temperature Monitoring

CPU temperature monitoring tools for Raspberry Pi (vcgencmd) and generic Linux systems (thermal_zone).

## Commands

- **`temp`** — Show current CPU temperature with color-coded severity and throttle status
- **`temp-history`** — Show recent temperature readings from journald logs
- **`temp-stats`** — 24-hour statistics (min/max/avg/count) with ASCII trend graph

## Background Logging

- **`temp_logger.sh`** — RPi-specific logger, writes to journald as `temp-logger` unit
- **`temp_logger_generic.sh`** — Cross-platform logger with structured journal metadata
- **`temp_analysis.sh`** — Analysis script referenced by the installer

These loggers are designed to run via a systemd timer (`temp-logger.timer`). The timer must be enabled for `temp-history` and `temp-stats` to have data.

## Features

- **Automatic Temperature Logging**: Records CPU temperature, load, and throttling status every minute
- **Persistent Journaling**: Logs survive reboots for long-term analysis
- **Temperature Analysis**: Quick tool to view current status and historical trends

## Usage Examples

### View Real-time Temperatures
```bash
journalctl -t temp-monitor -f
```

### Check for Warnings
```bash
journalctl -t temp-monitor -p warning --since "1 hour ago"
```

### Export Temperature Data
```bash
journalctl -t temp-monitor --since yesterday -o json | jq -r '.TEMPERATURE'
```

## Installation

The temperature monitoring is automatically set up by the ClAP installer on Raspberry Pi systems. The installer will:

1. Enable persistent journaling (requires sudo)
2. Install and enable the temp-logger systemd timer
3. Create the `temp_analysis` command

## Thresholds

| Range | Status |
|-------|--------|
| < 60°C | Normal (green) |
| 60-69°C | Elevated (cyan) |
| 70-79°C | Warning (yellow) |
| 80°C+ | Critical (red) |

RPi 5 throttles at 85°C. Pi 5 with active cooling typically runs 40-55°C under load.

## Note

The temp-logger timer may not be installed on all machines. The `temp` command works standalone without historical logging.
