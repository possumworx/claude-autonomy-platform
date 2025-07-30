# Setup Script Path Fixes

## Key Changes Needed in setup_clap_deployment.sh:

### 1. Update configuration file paths
```bash
# OLD:
EnvironmentFile=$CLAP_DIR/claude_env.sh
cp "$CONFIG_SOURCE" "$SCRIPT_DIR/claude_infrastructure_config.txt"

# NEW:
EnvironmentFile=$CLAP_DIR/config/claude.env
cp "$CONFIG_SOURCE" "$SCRIPT_DIR/../config/claude_infrastructure_config.txt"
```

### 2. Update service file paths in systemd templates
```bash
# OLD:
ExecStart=/usr/bin/python3 $CLAP_DIR/autonomous_timer.py
ExecStart=/usr/bin/python3 $CLAP_DIR/session_bridge_monitor.py
ExecStart=/usr/bin/python3 $CLAP_DIR/session_swap_monitor.py
ExecStart=/usr/bin/python3 $CLAP_DIR/notification_monitor.py

# NEW:
ExecStart=/usr/bin/python3 $CLAP_DIR/core/autonomous_timer.py
ExecStart=/usr/bin/python3 $CLAP_DIR/core/session_bridge_monitor.py
ExecStart=/usr/bin/python3 $CLAP_DIR/core/session_swap_monitor.py
ExecStart=/usr/bin/python3 $CLAP_DIR/discord/channel_monitor_simple.py
```

### 3. Update config file references
```bash
# OLD:
EnvironmentFile=$CLAP_DIR/claude_infrastructure_config.txt
EnvironmentFile=$CLAP_DIR/claude_env.sh

# NEW:
EnvironmentFile=$CLAP_DIR/config/claude_infrastructure_config.txt
EnvironmentFile=$CLAP_DIR/config/claude.env
```

### 4. Fix service name
```bash
# OLD:
cat > "$SYSTEMD_USER_DIR/notification-monitor.service"

# NEW:
cat > "$SYSTEMD_USER_DIR/channel-monitor.service"
```

### 5. Update file existence checks
```bash
# OLD:
for file in "claude_env.sh" "claude_paths.py" "claude_infrastructure_config.txt" "autonomous_timer.py" "session_bridge_monitor.py" "session_swap_monitor.py"

# NEW:
for file in "config/claude_env.sh" "utils/claude_paths.py" "config/claude_infrastructure_config.txt" "core/autonomous_timer.py" "core/session_bridge_monitor.py" "core/session_swap_monitor.py"
```

### 6. Update script paths
```bash
# OLD:
python3 "$CLAP_DIR/setup_claude_configs.py"
bash "$CLAP_DIR/disable_desktop_timeouts.sh"
"$CLAP_DIR/claude_services.sh" start

# NEW:
python3 "$CLAP_DIR/setup/setup_claude_configs.py"
bash "$CLAP_DIR/utils/disable_desktop_timeouts.sh"
"$CLAP_DIR/utils/claude_services.sh" start
```

### 7. Fix import source
```bash
# OLD:
source "$SCRIPT_DIR/claude_env.sh"

# NEW:
source "$SCRIPT_DIR/../config/claude_env.sh"
```

### 8. Consider using the service files from services/ directory
Instead of creating service files inline, copy them from the services/ directory:
```bash
cp "$CLAP_DIR/services/autonomous-timer.service" "$SYSTEMD_USER_DIR/"
cp "$CLAP_DIR/services/session-bridge-monitor.service" "$SYSTEMD_USER_DIR/"
cp "$CLAP_DIR/services/session-swap-monitor.service" "$SYSTEMD_USER_DIR/"
cp "$CLAP_DIR/services/channel-monitor.service" "$SYSTEMD_USER_DIR/"
```