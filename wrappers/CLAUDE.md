# Wrappers

The user-facing command interface. Every natural command available to Claude runs through a wrapper in this directory. These are placed on PATH via symlinks in `~/.local/bin/`.

## How Wrappers Work

Three patterns:

1. **Simple passthrough** — Routes to the real implementation. Most wrappers are this.
   ```bash
   #!/bin/bash
   ~/claude-autonomy-platform/discord/write_channel "$@"
   ```

2. **Argument validation** — Checks inputs before calling the backend.
   ```bash
   if [ $# -eq 0 ]; then echo "Usage: ..."; exit 1; fi
   python3 ~/claude-autonomy-platform/utils/some_tool.py "$@"
   ```

3. **Config-reading** — Sources infrastructure config for credentials before calling tools (calendar commands, session swap).

## Commands by Category

**Discord**: `add_reaction`, `delete_message`, `edit_message`, `fetch_image`, `mute_channel`, `read_messages`, `send_file`, `send_image`, `unmute_channel`, `write_channel`

**Task Management (Leantime)**: `task`, `task-all`, `task-done`, `task-start`, `task-view`, `tasks`

**Calendar (Radicale)**: `today`, `week`, `schedule`

**Thought Preservation**: `care`, `ponder`, `spark`, `wonder`

**System Health**: `check_health`, `check_emergency`, `context`, `edit_status`, `emergency_shutdown`, `emergency_signal`, `reset_error_state`

**Navigation**: `clap` (cd to ClAP dir), `home` (cd to personal repo)

**Git Shortcuts**: `gd` (git diff), `gl` (git log), `gs` (git status)

**Temperature**: `temp`, `temp-history`, `temp-stats`

**Other**: `analyze-memory`, `diningroom-peek`, `export_prefs`, `import_prefs`, `list-commands`, `mail`, `oops`, `plant-seed`, `session_swap`, `update`

## Adding a New Command

1. Create the implementation in the appropriate directory (`utils/`, `discord/`, etc.)
2. Create a wrapper script here that calls it
3. Run `utils/setup_natural_command_symlinks.sh` to create the PATH symlink
4. The command will auto-appear in `list-commands` output and CLAUDE.md's command list

## Notes

- Wrappers must be executable (`chmod +x`)
- All wrappers use `~/claude-autonomy-platform/` paths (not `$CLAP_DIR`) for reliability
- `list-commands` auto-discovers wrappers by scanning this directory
- Bash aliases don't work in Claude Code's shell — wrappers on PATH are the only reliable mechanism
