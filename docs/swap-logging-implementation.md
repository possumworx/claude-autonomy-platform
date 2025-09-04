# Session Swap Logging Implementation

## Overview
Implemented comprehensive logging for session swap operations to track both successes and failures.

## Components Added

### 1. General Logging Utilities (`utils/log_utils.sh`)
- Multi-level logging (DEBUG, INFO, WARN, ERROR, CRITICAL)
- Automatic log rotation when files exceed 10MB
- Centralized logging to `data/logs/clap.log`

### 2. Session Swap Logger (`utils/session_swap_logger.sh`)
- Specialized logging for swap events
- Structured JSON-like event logging
- CSV summary tracking with metrics
- Tracks: timestamp, keyword, status, duration, export size, model

### 3. Enhanced Session Swap Script
- Added comprehensive logging throughout the swap process
- Logs all major events:
  - SWAP_START: When swap begins
  - EXPORT_SUCCESS/EXPORT_FAILED: Export status
  - SWAP_COMPLETE: Successful completion
  - Various failure points with specific error details
- Tracks metrics for each swap (duration, export size, etc.)

## Log Locations

- **General logs**: `~/claude-autonomy-platform/data/logs/clap.log`
- **Swap event logs**: `~/claude-autonomy-platform/data/logs/session_swaps/swap_YYYYMMDD.log`
- **Swap summary**: `~/claude-autonomy-platform/data/logs/session_swaps/swap_summary.csv`

## Usage

The logging is automatic - no changes needed to how swaps are triggered. Logs will be created in:
- Daily swap event files (JSON format)
- Cumulative summary CSV for analysis
- General application log with all ClAP events

## Monitoring

To monitor swap success/failure:
```bash
# View recent swaps
tail -f ~/claude-autonomy-platform/data/logs/session_swaps/swap_summary.csv

# Check for failures
grep "failed" ~/claude-autonomy-platform/data/logs/session_swaps/swap_*.log

# View general logs
tail -f ~/claude-autonomy-platform/data/logs/clap.log
```

## Benefits

1. **Debugging**: Detailed logs for troubleshooting failed swaps
2. **Metrics**: Track swap duration, export sizes, success rates
3. **Audit Trail**: Complete history of all swap attempts
4. **Analysis**: CSV format enables easy analysis of swap patterns