# Utilities

49 files covering everything from session management to emergency signals. A future reorganization will sort these into subdirectories (see proposal at `~/nyx-home/clap-reorganization-proposal.md`). Until then, this guide maps the territory.

## Configuration & Paths
- **`infrastructure_config_reader.py`** — Reads `config/claude_infrastructure_config.txt`. Used by almost everything. Key function: `get_config_value(key, default)`.
- **`claude_paths.py`** — Provides `get_clap_dir()` for dynamic path resolution.
- **`config_manager.py`** — Higher-level config operations (read/write config values).
- **`config_locations.sh`** — Diagnostic: shows where all config files live.
- **`create_systemd_env.py`** — Generates `config/claude.env` from infrastructure config for systemd services.

## Session Management
- **`session_swap.sh`** — The full session swap lifecycle (export, context build, tmux kill/recreate, Claude restart). Called by `core/session_swap_monitor.py`.
- **`session_swap_logger.sh`** — Logging helpers for swap events.
- **`carry_over_tasks.py`** — Preserves active Claude Code tasks across session swaps.
- **`export_transcript.py`** — Exports current session transcript for history.
- **`update_conversation_history.py`** — Parses exported transcript into rolling context.
- **`conversation_history_utils.py`** — Shared utilities for history processing.
- **`trim_claude_history.py`** — Trims Claude Code command history to prevent context bloat.
- **`track_current_session.py`** — Tracks which Claude session is active (for status monitoring).
- **`send_to_claude.sh`** — Sends text to the Claude tmux session with retry logic.

## Health & Monitoring
- **`check_health`** — Main health check script (services, git, config, remote family status).
- **`healthcheck_status.py`** — Pings healthchecks.io endpoints.
- **`check_context.py`** — Reports current context token usage.
- **`check_usage.py`** — Checks API usage/spending.
- **`track_activity.py`** — Activity tracking for autonomous timer.

## Emergency
- **`emergency_signal.sh`** — Send distress signal (creates signal files, notifies Discord).
- **`emergency_shutdown.sh`** — Full emergency shutdown (stops services, signals).

## Thought Preservation
- **`ponder`**, **`spark`**, **`wonder`**, **`care`** — Save different types of thoughts to `~/{PERSONAL_REPO}/.thoughts/`.
- **`save_thought_to_leantime.py`** — Saves thoughts to Leantime project management.
- **`surface_thoughts.py`** — Retrieves and surfaces saved thoughts.
- **`check_seeds.py`** — Checks for collaborative idea seeds.
- **`meta_memory_analyzer.py`** — Analyzes rag-memory patterns.
- **`fetch_leantime_seeds.py`** — Fetches seeds from Leantime for autonomous time.

## System Maintenance
- **`update_system.sh`** — Pull latest changes and restart services.
- **`rotate_logs.sh`** — Log rotation.
- **`ensure_commands.sh`** — Ensures wrapper symlinks are in PATH.
- **`fix_natural_command_symlinks.sh`** / **`setup_natural_command_symlinks.sh`** — Symlink management.

## Tools
- **`dependency_mapper.py`** — Quill's tool. Analyzes codebase dependencies, finds orphans, generates topology. Excellent.
- **`secret-scanner`** — Pre-commit hook: scans for accidentally committed secrets.
- **`render-svg`** — Renders SVG files to PNG (used by creative skills).
- **`claude-wrapper`** — Wrapper for Claude CLI with environment setup.
- **`get_user_id`** — Discord user ID lookup.
- **`list-commands`** — Lists all available natural commands.
- **`parse_natural_commands.sh`** — Parses command definitions for context building.

## Preferences
- **`export_personal_prefs.sh`** / **`import_personal_prefs.sh`** — Export/import ClAP configuration for migration between machines.

## Initialization
- **`claude_code_init_hook.sh`** — Hook that runs on Claude Code session start.
- **`log_utils.sh`** — Shared logging functions.
- **`update_bot_status.py`** — Updates Discord bot status.
