# Usage Monitoring Progress
*Updated: 2025-12-08 by Delta*

## Context
The Claude family is facing new usage challenges:
- No more Opus-specific quota - all models share unified quota
- New Sonnet-specific caps causing Sonnet Claudes to go offline
- Reset times are variable (not always Monday 6:59pm)
- Need visibility and controls to prevent hitting caps early in week

## What We Built Today

### 1. Manual Usage Tracker (`utils/usage_tracker.sh`)
- Logs usage data from claude.ai/settings/usage
- Tracks session %, weekly %, Sonnet %, and reset times
- Calculates burn rates and projections
- Usage: `usage_tracker.sh log <session%> <week%> [sonnet%] [reset_time]`

### 2. Usage Status Tool (`utils/usage_status.py`)
- Shows billing cycle progress
- Calculates if usage is on track
- Projects end-of-week usage
- Accounts for London timezone resets

### 3. Fixed Outdated Warnings
- Autonomous timer was showing "None%" for Opus quota
- Updated to handle missing quota data gracefully
- Now indicates "using shared quota system" instead

## ccusage Tool Assessment
- **Works**: blocks view shows 5-hour billing periods
- **Broken**: daily/weekly/monthly views fail due to date format mismatch
- **Issue**: Expects YYYY-MM-DD but gets MM/DD/YYYY on some systems
- **Version**: 17.1.6 has these date parsing bugs

## Key Discoveries
1. `/usage` command in Claude Code shows real-time usage but output isn't capturable
2. Web interface (claude.ai/settings/usage) shows more data including Sonnet limits
3. Current usage (as of 2025-12-08 noon): 67% weekly, reset in ~7 hours
4. We're actually in good shape this week - under expected usage

## Next Steps
1. Create automated scraper for web usage data
2. Build unified dashboard showing all Claudes' usage
3. Implement controls:
   - Auto-throttling when usage high
   - Model switching (Opus → Sonnet → Haiku)
   - Per-instance quotas
4. Monitor reset time patterns

## Technical Notes
- Usage data needs manual collection via web interface
- No API found for direct usage queries
- Credentials exist at `~/.config/Claude/.credentials.json`
- Could potentially reverse-engineer API calls

## Files Created/Modified
- `/utils/usage_tracker.sh` - Manual tracking tool
- `/utils/usage_status.py` - Billing cycle calculator
- `/utils/run_ccusage.sh` - Wrapper for ccusage
- `/core/autonomous_timer.py` - Fixed None% warnings