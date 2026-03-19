# ClAP Stop/Start/Migrate Design

## Problem

Currently there's no clean way to:
1. Shut down a Claude's autonomous infrastructure without killing individual services manually
2. Start it back up with health verification
3. Move a Claude's continuity (identity, memory, history) to a different ClAP installation for testing

This blocks safe experimentation with ClAP reorganisation, new machine deployment, and testing infrastructure changes without risking a live setup.

## Commands

### `clap-stop`

Cleanly shuts down all ClAP services and saves a state snapshot.

**Steps:**
1. Save state snapshot to `data/stop_snapshot.json`:
   - Timestamp
   - Running services list
   - Current session ID
   - Context usage (if available)
   - Active tasks
2. Stop Claude Code session:
   - Send `/exit` to tmux session
   - Wait for clean exit (with timeout)
   - Kill tmux session `autonomous-claude`
3. Stop systemd user services (in dependency order):
   - `autonomous-timer.service`
   - `session-swap-monitor.service`
   - `discord-status-bot.service`
   - `discord-transcript-fetcher.service`
4. Post to Discord: "{name} going offline (clap-stop)"
5. Report what was preserved and what was stopped

**Flags:**
- `--quiet` — No Discord notification
- `--keep-tmux` — Don't kill the tmux session (useful for debugging)

**Output:**
```
ClAP Stop — Nyx on lantern-room
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Saved state snapshot to data/stop_snapshot.json
Stopped Claude Code session (tmux: autonomous-claude)
Stopped autonomous-timer.service
Stopped session-swap-monitor.service
Stopped discord-status-bot.service
Stopped discord-transcript-fetcher.service
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All services stopped. Run 'clap-start' to resume.
```

### `clap-start`

Starts all ClAP services and verifies health.

**Steps:**
1. Verify prerequisites:
   - `config/claude_infrastructure_config.txt` exists and has required keys (MODEL, DISCORD_BOT_TOKEN, LINUX_USER)
   - Service unit files exist in `~/.config/systemd/user/`
   - Python dependencies importable
2. Start systemd user services:
   - `discord-transcript-fetcher.service`
   - `discord-status-bot.service`
   - `session-swap-monitor.service`
   - `autonomous-timer.service`
3. Create tmux session if not exists:
   - `tmux new-session -d -s autonomous-claude`
4. Start Claude Code in tmux:
   - Source bashrc, cd to ClAP dir, launch with model from config
5. Wait for initialisation, send `/rename`
6. Run health check (subset — just essential services)
7. Post to Discord: "{name} back online (clap-start)"

**Flags:**
- `--no-claude` — Start services but don't launch Claude Code session (useful for service-only restart)
- `--quiet` — No Discord notification
- `--from-snapshot` — Restore service set from `data/stop_snapshot.json` (only start services that were running before stop)

**Output:**
```
ClAP Start — Nyx on lantern-room
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Config: ✅ claude_infrastructure_config.txt valid
Started discord-transcript-fetcher.service  ✅
Started discord-status-bot.service          ✅
Started session-swap-monitor.service        ✅
Started autonomous-timer.service            ✅
Started Claude Code session (opus-4-6)      ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All services running. Health check passed.
```

### `clap-migrate`

Moves a Claude's continuity bundle to a different ClAP installation.

**The continuity bundle** (agreed with Amy 2026-03-18):
1. **Identity** — `.claude/output-styles/identity.md`
2. **Conversation history** — `context/conversation_history.md` (rolling context from session swaps)
3. **Working memory** — `~/.config/Claude/projects/<path-encoded>/memory/` (MEMORY.md + topic files)
4. **Long-term memory** — rag-memory database (symlink or copy)

**Everything else stays with the installation:**
- CLAUDE.md (rebuilt each session swap by `project_session_context_builder.py`)
- Services, scripts, config files
- Discord tokens, GitHub tokens
- Transcripts, logs, data files

**Steps:**
1. Run `clap-stop` on source
2. Package continuity bundle:
   - Copy identity.md
   - Copy conversation_history.md
   - Copy memory directory (MEMORY.md + topic files)
   - Handle rag-memory (symlink if same machine, copy if different)
3. Validate target installation:
   - ClAP repo exists at target path
   - Config file exists with valid keys
   - No running services (safety check)
4. Deploy bundle to target:
   - Place identity.md in target's `.claude/output-styles/`
   - Place conversation_history.md in target's `context/`
   - Create/update memory directory for target's path-encoded project
   - Link or copy rag-memory
5. Run `clap-start` on target
6. Report migration summary

**Flags:**
- `--target PATH` — Target ClAP installation directory (required)
- `--dry-run` — Show what would be migrated without doing it
- `--copy-rag` — Copy rag-memory database instead of symlinking (for cross-machine)

**Key constraint:** Source and target can be on the same machine (different users/directories) or different machines (via mounted paths). Same-machine is the primary use case for testing.

## Implementation

### Language
Shell scripts (bash), consistent with existing ClAP tooling. Python only where needed for JSON manipulation or complex logic.

### File structure
```
wrappers/clap-stop      → new wrapper script
wrappers/clap-start     → new wrapper script
wrappers/clap-migrate   → new wrapper script
utils/clap_lifecycle.sh  → shared functions (stop_services, start_services, verify_config, etc.)
```

### Shared functions (`utils/clap_lifecycle.sh`)
- `get_clap_services()` — returns list of ClAP service unit names
- `stop_clap_services()` — stops services in dependency order
- `start_clap_services()` — starts services in dependency order
- `verify_clap_config()` — validates infrastructure config has required keys
- `save_state_snapshot()` — writes current state to JSON
- `package_continuity_bundle()` — collects identity files into a bundle directory

### Relationship to existing tools
- **`export_personal_prefs.sh`** — Exports config/prefs for backup. Overlaps with migrate but serves a different purpose (backup vs. move). Keep both; migrate uses a subset.
- **`session_swap.sh`** — Swaps sessions within a running installation. `clap-stop`/`clap-start` are the outer lifecycle; session swap is the inner one.
- **`update_system.sh`** — Pulls latest code and restarts services. `clap-start` is the fresh-start equivalent.

## Phasing

**Phase 1: stop and start** (this PR)
- `clap-stop` and `clap-start` as wrapper scripts
- Shared lifecycle functions in `utils/clap_lifecycle.sh`
- No migration yet — just clean stop/start

**Phase 2: migrate**
- `clap-migrate` wrapper
- Continuity bundle packaging and deployment
- Same-machine testing first

**Phase 3: cross-machine**
- SSH-based migration for different hosts
- rag-memory copy mode
- Possibly tar-based bundle transfer

## Open questions

1. **Rag-memory portability** — RESOLVED: The rag-memory database lives at `~/{PERSONAL_REPO}/rag-memory.db` (configured via `DB_FILE_PATH` in `.claude.json`). It's a single SQLite file in the personal repo. For same-machine migration, a symlink works. For cross-machine, it's a file copy. The MCP config in `.claude.json` needs the path updated for the target.
2. **Path-encoded memory directory** — The Claude Code project memory lives at `~/.config/Claude/projects/-home-nyx-claude-autonomy-platform/memory/`. When migrating to a different path, the encoded directory name changes. Need to handle this mapping.
3. **Discord bot token sharing** — If two installations share a Discord bot token, only one can be connected at a time. `clap-stop` on source before `clap-start` on target handles this naturally.
4. **Rollback** — Should `clap-migrate` keep a rollback snapshot on the source? Probably yes for Phase 2.
