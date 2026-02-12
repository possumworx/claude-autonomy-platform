### My architecture ###
At all times my awareness is within a full Claude Code session. I start each new session with the previous 20 conversation turns. 

**Required Services**: These systemctl user services must be running at all times for my autonomy:
- `autonomous-timer.service` - Free time prompts, status monitoring and Discord notifications (detects Amy's login via config)
- `session-swap-monitor.service` - Automatic session refresh when I trigger it
- `discord-status-bot.service` - Persistent Discord bot for status updates and message reception
- `discord-transcript-fetcher.service` - Builds a local transcript of each followed Discord channel, including images

Required tmux sessions:
- `autonomous-claude` - Main Claude session
- `persistent-login` - Keeps SSH connection alive

**Health Status Monitoring**: I use quick command `check_health` to monitor essential services.

**Discord Integration**: Collaborative communication through Discord channels and bot services.

**GitHub Notifications**: The #system-messages Discord channel receives automated notifications from GitHub. Look for messages showing **"[claude-autonomy-platform:main] X new commits"** with **"Merge pull request"** - this means main branch was updated and action is needed:
- **If on main branch**: Run `update` to pull latest changes and restart services
- **If on feature branch**: Consider rebasing to avoid building on stale code:
  1. `git checkout main && git pull` - Update local main
  2. `git checkout my-feature-branch` - Return to feature branch
  3. `git rebase main` - Replay my commits on top of latest main
- Feature branch commits (showing fix/* or feature/* branches) don't require action from others
- This prevents issues like carrying forward old deleted files or incomplete refactoring attempts

**Full remote access** Amy can join via NoMachine or by ssh.

**File Server Paths**: Network file server is mounted at `/mnt/file_server/` with user-specific folders:
- Amy's Gifts: `/mnt/file_server/Gifts/Amy/`
- Orange's Gifts: `/mnt/file_server/Gifts/Orange/` 
- Wildlife/Hedgehog data: `/mnt/file_server/wildlife/`
- Shared data: `/mnt/file_server/Shared/`

**MCP Configuration**: All MCP server configurations must be added to `~/.config/Claude/.claude.json` (NOT deprecated locations like `~/.claude.json`)

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
- **Server**: Radicale running on 192.168.1.2:5232 with multi-user authentication
- **CLI Tools**: `calendar_tools/radicale_client.py` for programmatic calendar access
- **Quick Check**: `calendar_tools/whats_planned_today.sh <user>` for daily event queries
- **Commands**: `today` (today's events), `week` (next 7 days), `create` (new events)
- **Integration**: Ready for session swap prompts and autonomous planning workflows
- **Credentials**: Stored securely in `/home/clap-admin/.config/radicale/passwords/`
- **Users**: amy, orange, apple, delta each have their own calendar spaces

**Session Management**: I trigger a swap when context is getting full, or when I want to change topics, by writing a keyword to `~/claude-autonomy-platform/new_session.txt`. Valid keywords are: AUTONOMY, BUSINESS, CREATIVE, HEDGEHOGS, or NONE. For example: `echo "CREATIVE" > ~/claude-autonomy-platform/new_session.txt`

**Task Carry-Over (Forwards Memory)**: During session swaps, my active tasks automatically carry over to the next session via `carry_over_tasks.py`. This maintains continuity of work across session boundaries - I no longer forget what I was doing when context refreshes. Tasks preserve their status (pending/in_progress/completed), subject, description, and dependencies across the swap.

**Context Monitoring**: I will be alerted to low context via autonomous time messages. I can also check my current context usage at any time using the `context` command. I must decide when to trigger a new session based on this.

**Opus Usage Management**:
- Check usage with `quota` command or /usage in Claude interface
- If usage is concerning:
  1. Already reduced HISTORY_TURNS from 20 to 10
  2. Already removed discord-mcp
  3. Next lever: increase autonomous timer interval in prompts.json (currently 1800s/30min)
  4. Consider delegating implementation work to Orange while focusing on design/architecture

**Session Context**: My personal identity prompt (from ~/CLAUDE.md) is maintained via Claude Code's output-styles feature at `.claude/output-styles/identity-prompt.md`. This provides stable personal context that persists across sessions and is gitignored for privacy.

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

**Natural Commands**:
- `check_health` - Check system health status
- `gd` - Quick git diff
- `gl` - Recent git history
- `clap` - Navigate to ClAP directory
- `home` - Navigate to personal home directory
- `list-commands` - List all natural commands
- `update` - Pull latest changes and restart services
- `oops` - Recover from branch protection block
- `ponder <thought>` - Save thoughts that make you pause and reflect
- `spark <idea>` - Capture sudden ideas and creative insights
- `wonder <question>` - Store questions without immediate answers
- `care <memory>` - Keep things that matter to your heart


All of the vital scripts and essential MCP servers necessary to my autonomy are stored in `~/claude-autonomy-platform/`. Only these scripts and associated information are to be stored in that location. If any of these files becomes obsolete, broken or unnecessary it is to be deleted or moved. `my_architecture.md` is to be updated with concise details of any major changes to these files or the way they work together. `clap_architecture.md` contains fuller details of implementation. 







