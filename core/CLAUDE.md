# Core Services

The three services that keep the Claude autonomous session alive. These run as systemd user services.

## Components

### `autonomous_timer.py` → `autonomous-timer.service`
The heartbeat. Runs on a 30-minute loop (configurable in `config/prompts.json`). Responsibilities:
- Checks for unread Discord messages across tracked channels
- Monitors context usage and triggers escalating warnings at 70%/80%/95%
- Detects Amy's presence via tmux attachment state
- Delivers free-time prompts during autonomous periods
- Sends context-critical alerts via Discord when usage is dangerous

Reads prompts from `config/prompts.json`. Tracks escalation state in `data/context_escalation_state.json`.

### `session_swap_monitor.py` → `session-swap-monitor.service`
Watches `new_session.txt` for keyword triggers (AUTONOMY, BUSINESS, CREATIVE, HEDGEHOGS, NONE). When triggered:
1. Calls `utils/session_swap.sh` which handles the full swap lifecycle
2. Exports transcript, updates conversation history, rebuilds session context
3. Kills and recreates the tmux session with a fresh Claude instance
4. Carries over active tasks via `utils/carry_over_tasks.py`

The trigger mechanism: Claude writes a keyword to `new_session.txt` → a PostToolUse hook exports the transcript → the monitor detects the change → swap executes.

### `claude_auto_resume.sh` → `claude-auto-resume.service`
Runs on boot. Checks `RESTART_AFTER_REBOOT` config flag. If enabled, ensures the tmux session exists and starts Claude Code with `--continue` to resume the previous conversation. Dormant installations (where the flag is false) exit gracefully.

## Dependencies

These services depend heavily on:
- `config/claude_infrastructure_config.txt` — token, model, user config
- `config/prompts.json` — prompt templates and thresholds
- `utils/infrastructure_config_reader.py` — config parsing
- `data/transcript_channel_state.json` — channel tracking for notifications
- `utils/session_swap.sh` — the actual swap mechanism (called by monitor)

## Key Design Decisions

- The timer detects human presence by checking tmux attachment (`tmux list-clients`), not by Discord status
- Context warnings escalate: first warning → escalated → critical, with increasing urgency
- Session swaps create a lockfile (`data/session_swap.lock`) to pause the autonomous timer during the swap
- The auto-resume script verifies model config before starting Claude to prevent identity confusion
