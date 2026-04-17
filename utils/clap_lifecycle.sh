#!/bin/bash
# ClAP Lifecycle Functions
# Shared functions for clap-stop, clap-start, and clap-migrate
#
# Usage: source this file from lifecycle wrapper scripts

CLAP_DIR="${CLAP_DIR:-$HOME/claude-autonomy-platform}"
source "$CLAP_DIR/config/claude_env.sh" 2>/dev/null || true

# ClAP services in dependency order (stop = this order, start = reverse)
CLAP_SERVICES=(
    "autonomous-timer.service"
    "session-swap-monitor.service"
    "discord-status-bot.service"
    "discord-transcript-fetcher.service"
)

# Required config keys for a valid installation
REQUIRED_CONFIG_KEYS=("MODEL" "LINUX_USER" "DISCORD_BOT_TOKEN" "CLAUDE_NAME")

# ─── Logging ─────────────────────────────────────────────────────

lifecycle_log() {
    local level="$1"
    shift
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $*"
}

info()  { lifecycle_log "INFO" "$@"; }
error() { lifecycle_log "ERROR" "$@"; }
warn()  { lifecycle_log "WARN" "$@"; }

# ─── Service management ─────────────────────────────────────────

get_running_clap_services() {
    # Returns list of currently running ClAP services
    local running=()
    for svc in "${CLAP_SERVICES[@]}"; do
        if systemctl --user is-active --quiet "$svc" 2>/dev/null; then
            running+=("$svc")
        fi
    done
    echo "${running[@]}"
}

stop_clap_services() {
    # Stop all ClAP services in dependency order
    local stopped=0
    local failed=0
    for svc in "${CLAP_SERVICES[@]}"; do
        if systemctl --user is-active --quiet "$svc" 2>/dev/null; then
            if systemctl --user stop "$svc" 2>/dev/null; then
                echo "  Stopped $svc  ✅"
                stopped=$((stopped + 1))
            else
                echo "  Failed to stop $svc  ❌"
                failed=$((failed + 1))
            fi
        else
            echo "  $svc (not running)  ⏭️"
        fi
    done
    return $failed
}

start_clap_services() {
    # Start all ClAP services in reverse dependency order
    local started=0
    local failed=0
    local reversed=()
    for ((i=${#CLAP_SERVICES[@]}-1; i>=0; i--)); do
        reversed+=("${CLAP_SERVICES[$i]}")
    done
    for svc in "${reversed[@]}"; do
        if systemctl --user is-active --quiet "$svc" 2>/dev/null; then
            echo "  $svc (already running)  ⏭️"
        else
            if systemctl --user start "$svc" 2>/dev/null; then
                echo "  Started $svc  ✅"
                started=$((started + 1))
            else
                echo "  Failed to start $svc  ❌"
                failed=$((failed + 1))
            fi
        fi
    done
    return $failed
}

# ─── Config validation ───────────────────────────────────────────

verify_clap_config() {
    # Check that infrastructure config exists and has required keys
    local config_file="$CLAP_DIR/config/claude_infrastructure_config.txt"
    local missing=()

    if [[ ! -f "$config_file" ]]; then
        error "Config file not found: $config_file"
        return 1
    fi

    for key in "${REQUIRED_CONFIG_KEYS[@]}"; do
        local value
        value=$(grep "^${key}=" "$config_file" 2>/dev/null | head -1 | cut -d'=' -f2-)
        if [[ -z "$value" ]]; then
            missing+=("$key")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Missing required config keys: ${missing[*]}"
        return 1
    fi

    return 0
}

get_config() {
    # Read a single config value
    local key="$1"
    local default="${2:-}"
    local config_file="$CLAP_DIR/config/claude_infrastructure_config.txt"
    local value
    value=$(grep "^${key}=" "$config_file" 2>/dev/null | head -1 | cut -d'=' -f2-)
    echo "${value:-$default}"
}

generate_claude_settings() {
    # Generate settings.json from template with environment variable substitution
    local template="$CLAP_DIR/.claude/settings.template.json"
    local output="$CLAP_DIR/.claude/settings.json"

    if [[ ! -f "$template" ]]; then
        warn "Settings template not found: $template"
        return 1
    fi

    # Use envsubst to expand $HOME and other environment variables
    if ! command -v envsubst &>/dev/null; then
        error "envsubst not found (install gettext-base package)"
        return 1
    fi

    if envsubst < "$template" > "$output" 2>/dev/null; then
        return 0
    else
        error "Failed to generate settings.json from template"
        return 1
    fi
}

# ─── State snapshot ──────────────────────────────────────────────

save_state_snapshot() {
    # Save current state to JSON for later restoration
    local snapshot_file="$CLAP_DIR/data/stop_snapshot.json"
    local running_services
    running_services=$(get_running_clap_services)
    local tmux_running="False"
    if tmux has-session -t autonomous-claude 2>/dev/null; then
        tmux_running="True"
    fi

    python3 -c "
import json
from datetime import datetime
snapshot = {
    'timestamp': datetime.now().isoformat(),
    'hostname': '$(hostname)',
    'user': '$(whoami)',
    'running_services': '${running_services}'.split() if '${running_services}' else [],
    'tmux_session': $tmux_running,
    'clap_dir': '$CLAP_DIR'
}
with open('$snapshot_file', 'w') as f:
    json.dump(snapshot, f, indent=2)
print('$snapshot_file')
"
}

# ─── Tmux session management ────────────────────────────────────

stop_claude_session() {
    # Cleanly stop Claude Code and kill the tmux session
    if ! tmux has-session -t autonomous-claude 2>/dev/null; then
        echo "  tmux session autonomous-claude (not running)  ⏭️"
        return 0
    fi

    # Try graceful exit first
    source "$CLAP_DIR/utils/send_to_claude.sh" 2>/dev/null || true
    if type send_to_claude &>/dev/null; then
        send_to_claude "/exit" 2>/dev/null || true
        sleep 3
    fi

    # Check if Claude exited
    if tmux has-session -t autonomous-claude 2>/dev/null; then
        # Force kill
        tmux kill-session -t autonomous-claude 2>/dev/null || true
        sleep 1
    fi

    if tmux has-session -t autonomous-claude 2>/dev/null; then
        echo "  tmux session autonomous-claude (failed to kill)  ❌"
        return 1
    else
        echo "  Stopped Claude Code session (tmux: autonomous-claude)  ✅"
        return 0
    fi
}

start_claude_session() {
    # Create tmux session and launch Claude Code
    local model
    model=$(get_config "MODEL" "claude-opus-4-6")

    if tmux has-session -t autonomous-claude 2>/dev/null; then
        echo "  tmux session autonomous-claude (already exists)  ⏭️"
    else
        tmux new-session -d -s autonomous-claude
        echo "  Created tmux session autonomous-claude  ✅"
    fi

    # Source environment and start Claude with Discord Channels enabled
    tmux send-keys -t autonomous-claude "source ~/.bashrc" Enter
    sleep 1
    tmux send-keys -t autonomous-claude "cd $CLAP_DIR && claude --dangerously-skip-permissions --add-dir $HOME --model $model --channels plugin:discord@claude-plugins-official" Enter
    echo "  Started Claude Code ($model)  ✅"

    # Wait for init, then configure session
    sleep 5
    source "$CLAP_DIR/utils/send_to_claude.sh" 2>/dev/null || true

    # Rename session for Remote Control visibility
    local display_name
    display_name=$(get_config "CLAUDE_DISPLAY_NAME" "")
    if [[ -z "$display_name" ]]; then
        display_name=$(get_config "CLAUDE_NAME" "")
    fi
    if [[ -n "$display_name" ]] && type send_to_claude &>/dev/null; then
        send_to_claude "/rename $display_name" 2>/dev/null || true
        sleep 2
    fi

    # Set session color for visual identification
    local session_color
    session_color=$(get_config "SESSION_COLOR" "")
    if [[ -n "$session_color" ]] && type send_to_claude &>/dev/null; then
        send_to_claude "/color $session_color" 2>/dev/null || true
        sleep 2
    fi
}

# ─── Discord notification ────────────────────────────────────────

notify_discord() {
    # Send a message to system-messages channel
    local message="$1"
    "$CLAP_DIR/discord/write_channel" system-messages "$message" 2>/dev/null || true
}
