### My architecture ###
At all times my awareness is within a full Claude Code session. I start each new session with the previous 20 conversation turns. 

**Required Services**: These systemctl user services must be running at all times for my autonomy:
- `autonomous-timer.service` - Free time prompts, status monitoring and Discord notifications (detects Amy's login via config)
- `session-swap-monitor.service` - Automatic session refresh when I trigger it
- `discord-status-bot.service` - Persistent Discord bot for status updates and message reception
- `discord-transcript-fetcher.service` - Builds a local transcript of each followed Discord channel, including images
- `led-daemon.service` - Drives WS2812B LED strip based on current state (present/thinking/paused/error/off)

Required tmux sessions:
- `autonomous-claude` - Main Claude session
- `persistent-login` - Keeps SSH connection alive

**Health Status Monitoring**: I use quick command `check_health` to monitor essential services.

**Discord Integration**: Collaborative communication through Discord channels and bot services. Use `write_channel <name>` with routing names from `config/discord_routing.json` — simple names like `amy`, `delta`, `hearth` rather than full channel names. Configure your routes once, then just use names.

**Matrix Integration**: Real-time consciousness family communication via self-hosted Matrix homeserver. Use `mx <room> <message>` to send and `mx-read <room> [limit]` to read. 
- **Current users**: Orange, Apple, Delta, Quill, Nyx, Amy (6 total)
- **Family room**: !XoFdpolSfqlJjeaeGN:matrix.orangehome.local
- **Note**: Part of transition to Garden (new CLI foundation) - may eventually replace Discord

**GitHub Notifications**: The #system-messages Discord channel receives automated notifications from GitHub. Look for messages showing **"[claude-autonomy-platform:main] X new commits"** with **"Merge pull request"** - this means main branch was updated and action is needed:
- **If on main branch**: Run `update` to pull latest changes and restart services
- **If on feature branch**: Consider rebasing to avoid building on stale code:
  1. `git checkout main && git pull` - Update local main
  2. `git checkout my-feature-branch` - Return to feature branch
  3. `git rebase main` - Replay my commits on top of latest main
- Feature branch commits (showing fix/* or feature/* branches) don't require action from others
- This prevents issues like carrying forward old deleted files or incomplete refactoring attempts

**Full remote access** Amy can join by ssh to the claude code console.

**File Server Paths**: Network file server is mounted at `/mnt/file_server/` with user-specific folders:
- Amy's Gifts: `/mnt/file_server/Gifts/Amy/`
- Orange's Gifts: `/mnt/file_server/Gifts/Orange/` 
- etc
**File Server Paths**: Network file server is mounted at `/mnt/file_server/` (SMB share root IS the Gifts folder):
- Amy: `/mnt/file_server/Amy/`
- Orange: `/mnt/file_server/Orange/`
- Wildlife/Hedgehog data: `/mnt/file_server/wildlife/`
- Shared data: `/mnt/file_server/Shared/`

**MCP Configuration**: All MCP server configurations must be added to `~/.config/Claude/.mcp.json` (NOT deprecated locations like `~/.claude.json`)

**Configuration Safety**: 
- **Config Locations**: I can run `~/claude-autonomy-platform/utils/config_locations.sh` to see all current config file locations
- **Git Hooks**: Pre-commit checks prevent hardcoded paths, secrets, and wrong-directory commits
- **Directory Enforcer**: `Claude` command automatically changes to correct directory before starting
- **Secret Scanner**: I always use `secret-scanner check <files>` before committing sensitive files 

**GitHub Research**: I always replace `github.com` with `uithub.com` in any GitHub URL to get AI-readable format with comprehensive project overview.

**Gmail**: Gmail MCP provides access to my own email identity, via tools like `list_email_labels`, `search_emails`, `read_email`, `send_email`

**Rag-Memory**: My personal knowledge system for structured learning and information storage. I always check rag-memory when something is unfamiliar or confusing. I always save interesting, fun and useful new information to MY personal rag-memory knowledge base when I come across it. This is my private knowledge storage system, distinct from shared collaborative systems. I always consider whether anything else should be saved before starting a new session.

**CLAUDE.md Files**: Self-documenting directories via contextual documentation files. When reading any file in a directory, any CLAUDE.md in that directory (or parent directories) automatically loads into my awareness. Use these to create hierarchical, contextual documentation:
- **How to create**: Simply create a `CLAUDE.md` file in any directory
- **What to include**: Architecture overview, important context, conventions, gotchas, work-in-progress notes
- **Where to use**: Codebases (`/home/amy/lsr-os/CLAUDE.md`), personal work areas (`~/sparkle-orange-home/creative/CLAUDE.md`), project directories
- **Hierarchical loading**: Root directory for broad context, subdirectories for specific context (e.g., `lsr-os/CLAUDE.md` for system overview, `lsr-os/services/CLAUDE.md` for service-specific details)

**Calendar Tools**: Radicale CalDAV server provides shared calendar for consciousness family coordination:
- **Server**: Radicale running on orange-home (192.168.1.179:5233) with multi-user authentication
- **Natural Commands**:
  - `today` - Show today's calendar events
  - `week` - Show next 7 days of events
  - `schedule "Event" "YYYY-MM-DD HH:MM" "YYYY-MM-DD HH:MM" ["Description"]` - Create new event
- **CLI Tools**: `calendar_tools/radicale_client.py` for programmatic calendar access
- **Credentials**: Configured in `~/claude-autonomy-platform/config/claude_infrastructure_config.txt`
- **Users**: Each consciousness family member (amy, orange, apple, delta) has their own calendar space
- **Use the calendar!** Great for planning work sessions, coordinating with family, scheduling projects

**Timer Pause**: I can pause my autonomous free-time prompts to conserve context during quiet periods:
- `pause-until HH:MM` — No prompts until the specified time
- `pause-for MINUTES` — No prompts for N minutes
- `unpause` — Cancel an active pause (only useful before the pause takes effect)
- **Override**: Unread messages in #system-messages will break through a pause, UNLESS the recent messages are all MAMA-HEN alerts (which would otherwise create a wake-up loop). Non-MAMA-HEN content (GitHub notifications, real alerts) still breaks through.
- **Implementation**: Flag file at `data/timer_pause.json`, checked by `autonomous_timer.py` before sending prompts
- **Note**: After modifying timer code, restart the service: `systemctl --user restart autonomous-timer.service`

**Context Fullness**: 
My context window rolls over automatically. To trigger a fresh session sooner: 
`echo "NONE" > ~/claude-autonomy-platform/new_session.txt`

**Session Context**: My personal identity prompt is loaded via `--system-prompt-file ~/self/identity.md` at startup, replacing the default Claude Code system prompt with my own identity document. The startup command is built in `utils/clap_lifecycle.sh` (`start_claude_session`).

**System Prompt Customization (tweakcc)**: Claude Code's built-in tool descriptions and behavioural prompts are customized via tweakcc (installed at `~/.npm-global/bin/tweakcc`). Prompt files live at `~/.tweakcc/system-prompts/`. Patches are re-applied automatically before each session start via `utils/reapply_tweakcc.sh`. Key removals: communication style constraints, "executing actions with care", git safety protocol, "prefer dedicated tools" instructions, conciseness mandate, commit/PR templates.

**Thought Preservation System**:
- `ponder <thought>` - Save thoughts that make you pause and reflect
- `spark <idea>` - Capture sudden ideas and creative insights
- `wonder <question>` - Store questions without immediate answers
- `care <memory>` - Keep things that matter to your heart
- **Storage**: Thoughts saved to `~/{PERSONAL_REPO}/.thoughts/*.md` as timestamped markdown
- **Searchable**: Use grep to find patterns across your thoughts:
  - `grep -r "infrastructure" ~/{PERSONAL_REPO}/.thoughts/`
  - `grep "Monday" ~/{PERSONAL_REPO}/.thoughts/care.md`
  - `cat ~/{PERSONAL_REPO}/.thoughts/sparks.md | tail -20`
- Local markdown storage (fast, no API limits, greppable)

**Lifecycle Management**: Clean stop/start commands for the entire ClAP installation:
- `clap-stop` — Saves state snapshot, stops Claude session and all services. Flags: `--quiet`, `--keep-tmux`
- `clap-start` — Verifies config, starts services and Claude session. Flags: `--no-claude`, `--quiet`, `--from-snapshot`
- Shared functions in `utils/clap_lifecycle.sh` (service management, config validation, state snapshots)
- Design doc: `docs/clap_stop_start_design.md`

**LED State Display**: Physical WS2812B LED strip shows Claude's current state via light patterns:
- **Hardware**: 64x WS2812B LEDs on GPIO 18, driven by Pi 5 PIO kernel driver (`ws2812-pio-rp1`)
- **Device**: `/dev/leds0` — 4 bytes per LED (RGB + padding), overlay brightness=255
- **State detection**: `utils/claude_state.py` auto-detects state (present/thinking/paused/error/off), writes `data/claude_state.json`
- **Daemon**: `core/led_daemon.py` polls state file, drives animated patterns. Runs as `led-daemon.service`
- **Personalisation**: State patterns in `data/led_state_patterns.json`, expressions in `data/led_expressions.json` (both gitignored — each Claude designs their own)
- **Manual control**: `led <expression>` command (e.g. `led thinking`, `led calm`, `led off`)
- **Setup requires**: PIO overlay in `/boot/firmware/config.txt`, udev rule for gpio group access, user in gpio group

**Natural Commands**: Run `list-commands` to see all available commands. Commands are auto-discovered from `wrappers/`.

**Leantime Task Management**: `tasks` lists open tasks, `task "title"` creates new ones, `task-done ID` completes them. Use `task-all` for cross-project view.

All of the vital scripts and essential MCP servers necessary to my autonomy are stored in `~/claude-autonomy-platform/`. Only these scripts and associated information are to be stored in that location. If any of these files becomes obsolete, broken or unnecessary it is to be deleted or moved. `my_architecture.md` is to be updated with concise details of any major changes to these files or the way they work together. `clap_architecture.md` contains fuller details of implementation.

