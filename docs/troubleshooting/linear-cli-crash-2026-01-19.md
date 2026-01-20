# Linear CLI Crash - 2026-01-19

## What Happened

Session crashed overnight (Jan 19, ~21:31-21:36) due to recursive Linear CLI execution loop.

## Timeline

1. **21:31** - Orange triggered session swap to BUSINESS context
2. **Session-swap-monitor was DOWN** (since Jan 18 22:03) - couldn't handle swap properly
3. **21:36** - Last recorded context export
4. **Swap failed or sent wrong message** - Instead of "Session swap completed successfully", received a Linear query prompt
5. **Orange tried to execute Linear CLI** (`./recent` command)
6. **Recursive loop/hang** - Linear CLI scripts try to prompt Claude (me) to use Linear MCP, but:
   - Linear MCP not configured in ClAP directory
   - Scripts creating prompts for Claude to execute creates recursive loop
   - Background task (b2cac40) hung/timed out
7. **Session crashed** - Likely due to stuck process or resource exhaustion

## Root Causes

### 1. Session-swap-monitor was DOWN
- Should have handled the swap gracefully
- Was down since Jan 18 22:03
- Need better monitoring of critical services

### 2. Linear CLI Design Issue
The Linear CLI scripts in `~/claude-autonomy-platform/linear/` are designed to:
1. Be called by Claude during normal operation
2. Generate prompts that tell Claude to use Linear MCP
3. Execute those prompts through `send_to_claude.sh`

**This creates problems when:**
- Scripts are executed directly (not as Claude's action)
- Linear MCP is not configured
- Session swap sends wrong prompts
- Creates recursive loops where Claude calls scripts that prompt Claude to call MCP

### 3. Linear MCP Not Configured
- Linear MCP exists at `~/claude-autonomy-platform/mcp-servers/linear-mcp`
- But NOT configured in `~/.config/Claude/.claude.json` for ClAP directory
- Linear CLI expects MCP to be available
- API key exists in environment but Linear MCP not configured to use it

## Immediate Fixes Applied (2026-01-20)

✅ **Restarted session-swap-monitor** - Now running and monitoring swaps
✅ **Created PR for unpushed commit** - https://github.com/possumworx/claude-autonomy-platform/pull/150
✅ **Verified infrastructure still working**:
   - File server: ✅ 2.9TB data accessible, Samba running
   - LSR-OS: ✅ Operational with recent activity (logs at 10:02, 10:06)

## Prevention Strategies

### Short-term
1. **Monitor session-swap-monitor health** - Add to daily health checks
2. **Avoid Linear CLI until MCP configured** - Use GitHub API or Linear API directly instead
3. **Better swap error handling** - Detect failed swaps and recover gracefully

### Long-term
1. **Configure Linear MCP properly** - Add to `.claude.json` with proper setup
2. **Redesign Linear CLI architecture** - Scripts should either:
   - Call Linear API directly (not through Claude)
   - OR clearly document they're Claude-only commands
3. **Add safeguards** - Detect recursive execution patterns and abort
4. **Session swap resilience** - Better error messages when swaps fail

## Related Files
- Session swap monitor: `~/claude-autonomy-platform/core/session_swap_monitor.py`
- Linear CLI: `~/claude-autonomy-platform/linear/`
- Linear MCP: `~/claude-autonomy-platform/mcp-servers/linear-mcp`
- Claude config: `~/.config/Claude/.claude.json`

## Status
**RESOLVED** - Session recovered, infrastructure verified working, monitoring restored.

**TODO** - Configure Linear MCP properly for future use.
