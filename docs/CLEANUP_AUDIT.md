# ClAP Cleanup Audit Report
*Generated: 2025-08-19*

## Files to Remove

### Backup Files
- `./core/session_swap_monitor_with_fifo.py.bak`

### Python Cache (can be gitignored better)
- `./core/__pycache__/` (entire directory)
- `./discord/__pycache__/` (entire directory)
- `./utils/__pycache__/` (entire directory)

### Temporary/Old Files
- `./mcp-servers/gmail-mcp/node_modules/openai/src/resources/responses/input-items.ts.orig`
- `./target/logs/mcp-weather-stdio-server.log.2025-08-14.01143612423838410.tmp`
- `./target/logs/mcp-weather-stdio-server.log.2025-08-14.01305951059494361.tmp`

### Session Logs (evaluate which to keep)
- Multiple `session_ended_*.log` files in data/
- Consider archiving or rotating these

## Duplicate/Redundant Components

### Log Files in Multiple Locations
- `./logs/autonomous_timer.log` vs `./data/autonomous_timer.log`
- Need to standardize log location (recommend: ./logs/)

### Configuration Spread
- Config files in multiple places:
  - `config/claude_infrastructure_config.txt`
  - `ansible/configs/` (gitignored)
  - `.env` files in various locations

## Missing Documentation

### Core Components Needing Docs
1. **core/** - Session management, autonomous timer, swap monitor
2. **discord/** - Channel monitoring, state management
3. **utils/** - Various utility scripts
4. **scripts/** - Natural commands and helpers
5. **ansible/** - Infrastructure as code

### Architecture Overview Needed
- How components interact
- Data flow diagrams
- Service dependencies
- Configuration hierarchy

## Code Quality Issues

### Error Handling
- Many scripts use bare `except:` clauses
- Inconsistent logging patterns
- Missing error recovery in critical paths

### Hardcoded Values
- Context thresholds (should be configurable)
- Discord channel IDs in some places
- File paths that should use utils/claude_paths.py

### POSS References
- Old POSS-specific code scattered throughout
- Should be generalized or removed

## Recommendations

1. **Immediate Cleanup** (High Priority)
   - Remove all .bak, .tmp, .orig files
   - Clean __pycache__ directories
   - Consolidate log locations

2. **Standardization** (Medium Priority)
   - Create consistent error handling patterns
   - Move all configs to standardized locations
   - Document configuration hierarchy

3. **Documentation** (Medium Priority)
   - Write component READMEs
   - Create architecture diagrams
   - Document deployment process

4. **Code Quality** (Low Priority)
   - Replace bare except clauses
   - Extract hardcoded values to config
   - Add type hints where missing

## Next Steps

1. Start with removing obvious cruft (backup files, caches)
2. Consolidate duplicate components
3. Begin documentation effort
4. Gradually improve code quality


## No longer used?

core/comms_monitor_simple.py

config/comms_monitor_config.json
config/vscode-mcp-example.json
config/x11_env.sh
config/claude_state_detector.sh

patches/
patches/autonomous-timer-fixes.patch

services/session-bridge-monitor.service

utils/send-to-claude.sh.backup
utils/send-to-terminal.sh
utils/session-audit.py
utils/tellclaude-reader.sh


