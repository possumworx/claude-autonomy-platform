# Channel Monitor Health Check Setup

## Overview
The channel-monitor.service replaces the old discord-monitor.service and is integrated with healthchecks.io monitoring.

## Configuration Steps

1. **Create a new check in healthchecks.io**:
   - Name: "Channel Monitor" 
   - Timeout: 5 minutes (since it checks every 30 seconds)
   - Grace time: 5 minutes

2. **Add the ping URL to your infrastructure config**:
   ```
   CHANNEL_MONITOR_PING=https://hc-ping.com/your-channel-monitor-uuid
   ```

3. **Restart the channel monitor service**:
   ```bash
   systemctl --user restart channel-monitor.service
   ```

## Verification

1. Check that the channel monitor is pinging:
   ```bash
   journalctl --user -u channel-monitor.service -f
   ```
   Look for "Healthcheck URL configured" in the logs.

2. Run the health check status:
   ```bash
   ~/claude-autonomy-platform/utils/healthcheck_status.py
   ```
   You should see "Channel Monitor" in the list of checks.

## Migration Notes

- The channel-monitor.service replaces the old discord-monitor.service
- The new channel-based architecture is more reliable than the old DM-based system
- If you have `DISCORD_MONITOR_PING` configured, you can reuse it for `CHANNEL_MONITOR_PING`

## Backwards Compatibility

The channel monitor will check for these config keys in order:
1. `CHANNEL_MONITOR_PING` (preferred - new name)
2. `DISCORD_MONITOR_PING` (legacy - from old discord-monitor)

This ensures existing deployments can reuse their discord-monitor healthcheck URL.
