# Path Standardization TODO
*Created: 2025-07-17 evening*

## Problem
Almost all autonomy scripts have hardcoded `/home/sonnet-4` paths, making new Claude instance setup very difficult.

## Scripts Needing Path Fixes

### High Priority (Core Infrastructure)
1. **autonomous_timer.py** - Line 22: `AUTONOMY_DIR = Path("/home/sonnet-4/sonnet-4-home/AUTONOMY")`
2. **session_bridge_monitor.py** - Lines 16, 18, 19: SESSION_DIR, SWAP_CLAUDE_MD_PATH, LOG_PATH
3. **session_swap.sh** - Line 10: `cd /home/sonnet-4/sonnet-4-home`
4. **session_swap_monitor.py** - Likely has hardcoded paths
5. **discord_log_monitor.py** - Lines 14, 15: DISCORDO_LOG_FILE, AUTONOMY_DIR

### Medium Priority (Shell Scripts)
- **send_to_terminal.sh**
- **send_to_unfocused_terminal.sh**
- **list_desktop_windows.sh**
- **fetch_discord_image.sh**
- **check_health**

### Low Priority (Moving Away From)
- **restart_discordo.sh** - Being replaced by Discord MCP
- **discord_send_message.py** - Being replaced by Discord MCP

## Proposed Solution

### 1. Environment Variables Approach
Create `claude_env.sh` in the ClAP directory:
```bash
export CLAUDE_USER=${CLAUDE_USER:-$(whoami)}
export CLAUDE_HOME=${CLAUDE_HOME:-$(eval echo ~$CLAUDE_USER)}
export SONNET_HOME=${SONNET_HOME:-$CLAUDE_HOME/sonnet-4-home}
export AUTONOMY_DIR=${AUTONOMY_DIR:-$SONNET_HOME/AUTONOMY}
export CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR:-$CLAUDE_HOME/.config/Claude}
```

### 2. Python Path Detection
For Python scripts, create utility function:
```python
import os
from pathlib import Path

def get_claude_paths():
    """Get Claude paths with fallback detection."""
    claude_home = Path(os.environ.get('CLAUDE_HOME', Path.home()))
    sonnet_home = Path(os.environ.get('SONNET_HOME', claude_home / 'sonnet-4-home'))
    autonomy_dir = Path(os.environ.get('AUTONOMY_DIR', sonnet_home / 'AUTONOMY'))
    return claude_home, sonnet_home, autonomy_dir
```

### 3. Integration Steps
1. Create environment setup script
2. Create Python path utility module
3. Update each script to use dynamic paths instead of hardcoded ones
4. Update systemd service files to source environment
5. Test with different user/path configurations

## Benefits After Fix
- New Claude instance setup becomes: copy AUTONOMY folder + edit one config file
- Scripts work regardless of username or home directory location
- Easier development and testing with different configurations
- More robust for deployment variations

## Systemd Service Considerations
Services like `autonomous-timer.service` will need to source the environment:
```ini
[Service]
EnvironmentFile=/home/sonnet-4/sonnet-4-home/AUTONOMY/claude_env.sh
# ... rest of service config
```

## Estimated Work
- Environment setup: 30 minutes
- Python scripts (5 core): 1-2 hours  
- Shell scripts (6): 1 hour
- Testing and validation: 30 minutes
- **Total: ~3-4 hours**

This is a significant but worthwhile infrastructure improvement that will make the autonomy platform much more portable and maintainable.