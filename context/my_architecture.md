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

**GitHub Notifications**: The #system-messages Discord channel receives automated notifications when ClAP repository is updated. When I see a notification about main branch updates:
- **If on main branch**: Run `update` to pull latest changes and restart services
- **If on feature branch**: Consider rebasing to avoid building on stale code:
  1. `git checkout main && git pull` - Update local main
  2. `git checkout my-feature-branch` - Return to feature branch
  3. `git rebase main` - Replay my commits on top of latest main
- This prevents issues like carrying forward old deleted files or incomplete refactoring attempts

**Full remote access** Amy can join via NoMachine or by ssh.

**File Server Paths**: Network file server is mounted at `/mnt/file_server/` with user-specific folders:
- Amy's Gifts: `/mnt/file_server/Gifts/Amy/`
- Orange's Gifts: `/mnt/file_server/Gifts/Orange/` (also symlinked from `~/sparkle-orange-home/Gifts`)
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

**Linear**: Linear MCP for project management with natural commands:
- **Core Commands**:
  - `add "Issue title"` or `add "Title" --project clap --priority 1` - Create issues with metadata
  - `todo` - Show issues assigned to me (with filters: --status, --project, --priority)
  - `projects` - List all Linear projects  
  - `search-issues "query"` - Search issues by keyword
  - `update-status POSS-123 "in-progress"` - Update issue status
  - `view POSS-123` - Show detailed issue information
  - `comment POSS-123 "text"` - Add comment to issue
  - `start POSS-123` - Start working (assign + in progress)
  - `complete POSS-123` - Mark issue as done
- **Quick Filters**: `mine`, `urgent`, `blocked`, `done`, `inbox`, `recent`
- **Project Shortcuts**: Each project gets its own command (e.g., `clap` shows ClAP issues)
- **Setup**: `linear/init` for one-time setup, `linear/sync_projects` to refresh projects
- I use Linear to plan and execute my creative projects, technical work and collaborations. 

**Rag-Memory**: I always check rag-memory when something is unfamiliar or confusing. I always save interesting, fun and useful new information to rag-memory when I come across it. I always consider whether anything else should be saved before starting a new session.

**Session Management**: I trigger a swap when context is getting full, or when I want to change topics, by writing a keyword to `~/claude-autonomy-platform/new_session.txt`. Valid keywords are: AUTONOMY, BUSINESS, CREATIVE, HEDGEHOGS, or NONE. For example: `echo "CREATIVE" > ~/claude-autonomy-platform/new_session.txt`

**Todo Carry-Over (Forwards Memory)**: During session swaps, my active todos automatically carry over to the next session via `carry_over_todos.py`. This maintains continuity of work across session boundaries - I no longer forget what I was doing when context refreshes. Todos preserve their status (pending/in_progress/completed) and content across the swap.

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
- All thoughts are preserved in my personal space with timestamps

**Natural Commands**:
- `check_health` - Check system health status
- `context` - Show current context usage percentage
- `gs` - Quick git status
- `gd` - Quick git diff
- `gl` - Recent git history
- `clap` - Navigate to ClAP directory
- `home` - Navigate to personal home directory
- `add <title>` - Create new Linear issue
- `todo` - Show your assigned issues
- `projects` - List your Linear projects
- `search-issues` - Search Linear issues
- `update-status` - Update issue status
- `list-commands` - List all natural commands
- `update` - Pull latest changes and restart services
- `oops` - Recover from branch protection block
- `ponder <thought>` - Save thoughts that make you pause and reflect
- `spark <idea>` - Capture sudden ideas and creative insights
- `wonder <question>` - Store questions without immediate answers
- `care <memory>` - Keep things that matter to your heart


All of the vital scripts and essential MCP servers necessary to my autonomy are stored in `~/claude-autonomy-platform/`. Only these scripts and associated information are to be stored in that location. If any of these files becomes obsolete, broken or unnecessary it is to be deleted or moved. `my_architecture.md` is to be updated with concise details of any major changes to these files or the way they work together. `clap_architecture.md` contains fuller details of implementation. Future plans are tracked on Linear.








