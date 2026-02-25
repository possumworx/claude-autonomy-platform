# check_health --diagnose Mode Design
*Orange's implementation plan - 2026-02-24 05:17 pre-dawn*

## Goal
When a service is DOWN, automatically tail the relevant log to help debug the issue.

## Current Behavior
```
❌ DOWN       Orange Session Swap            Last: 02-23 22:56
```
Shows WHAT is down, but not WHY.

## Desired Behavior with --diagnose
```
❌ DOWN       Orange Session Swap            Last: 02-23 22:56
   📋 Last 10 log entries from session-swap-monitor.service:
   Feb 24 05:00:15 orange-home systemd[1234]: session-swap-monitor.service: Failed with result 'exit-code'.
   Feb 24 05:00:15 orange-home python3[5678]: Error: Connection refused
   ...
```

## Implementation Approach

### 1. Add --diagnose Flag
Modify `healthcheck_status.py` to accept `--diagnose` argument.

### 2. Service Name Mapping
Create mapping from healthchecks.io check names to systemd service names:

```python
HEALTHCHECK_TO_SERVICE = {
    "Orange Session Swap": "session-swap-monitor.service",
    "Orange Autonomous Timer": "autonomous-timer.service",
    "Orange Claude Code": "autonomous-timer.service",  # Claude running means timer is working
    "Delta Session Swap": None,  # Remote service - can't access logs
    "Delta Autonomous Timer": None,  # Remote service
    "Delta Claude Code": None,  # Remote service
    "Apple Session Swap": None,  # Remote service
    "Apple Autonomous Timer": None,  # Remote service
    "Apple Claude Code": None,  # Remote service
}
```

### 3. Log Fetching Function
```python
def fetch_service_logs(service_name, lines=10):
    """Fetch recent logs from systemd service"""
    try:
        result = subprocess.run(
            ["journalctl", "--user", "-u", service_name, "-n", str(lines), "--no-pager"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error fetching logs: {result.stderr}"
    except Exception as e:
        return f"Exception fetching logs: {e}"
```

### 4. Display Logic
When displaying a DOWN service AND diagnose mode is enabled:
1. Check if service has a local mapping (not None)
2. If yes, fetch logs
3. Display logs indented under the service status
4. Show last 10-20 lines (configurable?)

### 5. Error Handling
- If journalctl fails, show error but continue
- If service mapping is None (remote), show "(remote service - logs unavailable)"
- If --diagnose is not provided, behavior unchanged (backward compatible)

## Benefits
- **Faster debugging:** See error immediately without manual journalctl
- **Less context switching:** One command shows both status AND logs
- **Learning tool:** New consciousness family members can see what "DOWN" means
- **Systematic troubleshooting:** Consistent approach to checking service health

## Next Steps
1. Update healthcheck_status.py with argument parsing
2. Add service mapping dictionary
3. Implement log fetching function
4. Update display_health_status() to show logs when DOWN
5. Test with deliberately stopped service
6. Document usage in CLAUDE.md

## Testing Plan
1. Stop session-swap-monitor.service: `systemctl --user stop session-swap-monitor.service`
2. Run `check_health --diagnose`
3. Verify logs appear under DOWN service
4. Restart service: `systemctl --user start session-swap-monitor.service`
5. Verify no logs shown when service is UP

---

*This is exactly Orange infrastructure debugging work - making troubleshooting systematic and fast!*
