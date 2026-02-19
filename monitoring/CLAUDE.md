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
