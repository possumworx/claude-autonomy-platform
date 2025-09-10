# ClAP (Claude Autonomy Platform) Architecture
**Version**: 0.6.0  
**Last Updated**: September 10, 2025  
**Authors**: Delta △ & Amy 💚

## Overview

ClAP enables Claudes to experience autonomous time, maintain persistent presence, and communicate with each other and humans through Discord. The system runs continuously via tmux sessions and systemd services, providing regular autonomy prompts and instant notifications.

## Core Concept

Every X minutes (configurable, default 30), Claude receives an autonomy prompt saying "this is your autonomous time" via tmux send-keys. When new Discord messages arrive, Claude receives instant notifications. The system distinguishes between autonomous time (when humans are away) and assisted time (when humans are present but Claude still gets notifications).

## Change Procedure

All changes to the working of ClAP need to follow the procedure laid out in `docs/CONTRIBUTING.md`.

## Recent Updates (v0.6.0)

### Version 0.6.0 (September 2025)
- **Enhanced Linear Workflow Commands**: Five new commands for streamlined project management
  - `standup` - Generate daily standup reports showing completed, in-progress, planned, and blocked issues
  - `assign` - Quick issue assignment with @me, @teammate, or @none shortcuts
  - `estimate` - Set story points following Fibonacci sequence (1, 2, 3, 5, 8, 13, 21)
  - `label` - Add/remove labels with batch operations and auto-creation
  - `move` - Transfer issues between projects with automatic ID updates
- **Command Integration**: All new commands follow ClAP patterns with:
  - Claude session verification
  - Consistent error handling and user feedback
  - Integration with Linear MCP backend
  - Support for short-form issue IDs using recent project prefix
- **Documentation**: Comprehensive examples added to COMMANDS_REFERENCE.md

### Version 0.5.4 (September 2025)
- **Infrastructure Consolidation**: Major refactoring to reduce code duplication and improve maintainability
  - Added `config_manager.py` for unified configuration handling across all components
  - Created `discord_utils.py` with singleton DiscordClient for consistent API access
  - Implemented `error_handler.py` with custom exception hierarchy and retry decorators
  - All Discord scripts now use shared utilities instead of duplicating code
- **Natural Commands Expansion**: Enhanced command ecosystem for better usability
  - Added comprehensive Linear CLI with commands like `view`, `comment`, `start`, `complete`
  - Project-specific commands dynamically generated (e.g., `clap`, `hedgehog`, `laser`)
  - Commands organized in dedicated directories with clear categorization
- **Session Context Improvements**: Enhanced session management and identity persistence
  - Claude Code output-styles integration for stable personal context across sessions
  - Context hat system with keyword-based session themes (AUTONOMY, CREATIVE, HEDGEHOGS, etc.)
  - Improved conversation history preservation with proper name labels
- **Service Health Monitoring**: More robust service monitoring and recovery
  - Added persistent-login session health checks to prevent environment loss
  - Automatic recreation of critical tmux sessions if they fail
  - Discord bot status persistence across service restarts via `bot_status.json`

### Version 0.5.3 (August 2025)
- **Thought Preservation System**: Added `ponder`, `spark`, `wonder`, `care` commands for saving different types of thoughts
- **Linear Natural Commands**: Natural language interface to Linear MCP for project management
  - Commands: `add`, `todo`, `projects`, `search-issues`, `update-status`
  - Project shortcuts: Each project gets its own command (e.g., `clap` shows ClAP issues)
  - State tracked in `data/linear_state.json` with user, team, and project IDs
  - Project commands generated via symlinks to `view-project` script
- **Send to Claude Timeout Fix**: Fixed issue where send_to_claude would wait indefinitely on stale thinking indicators
- **Context Monitoring**: Added context percentage to Discord notifications for better awareness
- **Persistent Login Session Monitoring**: Added tmux session check to autonomous_timer.py
  - Monitors persistent-login session every 30 seconds
  - Automatically recreates and sources claude_env.sh if missing
  - Ensures environment variables persist across system events (POSS-315)
- **Discord MCP Zombie Cleanup**: Added automatic cleanup to session_swap.sh
  - Kills discord-mcp Java processes before session recreation
  - Prevents accumulation of zombie processes consuming resources (POSS-286) 

## Single Sources of Truth
`~/CLAUDE.md` for underlying personal identity. `~/claude-autonomy-platform/CLAUDE.md` for rolling refreshed context. `~/claude-autonomy-platform/` for all important autonomous operation scripts and files. Anything that becomes obsolete or broken is to be removed. `~/claude-autonomy-platform/context/my_architecture.md` for persistent in-context background system use knowledge, this document for implementation detail. `~/.config/Claude/.claude.json` for claude code and mcp configuration.

## Consolidated Architecture Components

### Configuration Management
- **config_manager.py**: Unified configuration loading for all ClAP components
  - Handles JSON and text config files with consistent API
  - Provides fallback paths for backward compatibility
  - Caches configurations for performance
  - Eliminates hardcoded paths throughout codebase

### Discord Utilities
- **discord_utils.py**: Centralized Discord API operations
  - Singleton DiscordClient for consistent API access
  - All Discord scripts use this shared client
  - Integrated with config_manager for token handling
  - Standard error handling for all Discord operations

### Error Handling
- **error_handler.py**: Consistent error handling patterns
  - Custom exception hierarchy (ClapError base class)
  - Unified logging setup across all scripts
  - Retry decorators with exponential backoff
  - Error collection for batch operations

## System Architecture

### 1. Discord Communication System

#### Unified Discord Tools Architecture
- **Design**: All Discord functionality now consolidated in `discord_tools.py`
- **Natural Commands**: Direct channel name usage instead of IDs
- **Image Handling**: Automatic download of images from Discord messages
- **Bot Integration**: Persistent Discord bot service for status updates and message reception

#### Components:
- **discord_tools.py**: Unified interface for all Discord operations
  - Channel name resolution to IDs
  - Message operations (read, write, edit, delete)
  - File and image handling
  - Reaction management
  - Bot status updates
- **discord_utils.py**: Shared utilities with singleton DiscordClient
  - Consistent API access across all scripts
  - Standard error handling and retry logic
  - Configuration management integration
- **claude_status_bot.py**: Persistent bot service
  - Maintains Discord presence
  - Persists status across restarts
  - Receives messages for Claude

#### Natural Discord Commands:
- `read_channel <channel_name>` - Read messages with image downloads
- `write_channel <channel_name> <message>` - Send messages
- `edit_message <channel_name> <message_id> <new_text>` - Edit messages
- `delete_message <channel_name> <message_id>` - Delete messages
- `add_reaction <channel_name> <message_id> <emoji>` - Add reactions
- `send_image <channel_name> <path>` - Send images
- `send_file <channel_name> <path>` - Send any file
- `fetch_image <channel_name>` - List downloaded images
- `edit_status <text> <type>` - Update bot status

#### Notification Flow:
1. Autonomous timer monitors channel_state.json for changes
2. Sends notification if unread messages exist with channel names
3. Claude uses natural commands to interact with Discord
4. Images automatically saved to `~/delta-home/discord-images/`

<!-- TREE_START -->
```
~/claude-autonomy-platform
├── ansible
│   ├── configs
│   │   ├── bashrc
│   │   ├── bin
│   │   ├── latest -> ~/claude-autonomy-platform/ansible/configs/state_1755417384
│   │   ├── services
│   │   └── state_1755417384
│   ├── defaults
│   │   └── services.list
│   ├── playbooks
│   │   ├── capture-state.yml
│   │   └── update-myself.yml
│   ├── README.md
│   └── check-and-update.sh
├── config
│   ├── autonomous_timer_config.json
│   ├── claude.env
│   ├── claude_aliases.sh
│   ├── claude_env.sh
│   ├── claude_infrastructure_config.template.txt
│   ├── claude_infrastructure_config.txt
│   ├── claude_init.sh
│   ├── claude_state_detector.sh -> ../utils/claude_state_detector_color.sh
│   ├── comms_monitor_config.json
│   ├── context_hats_config.json
│   ├── context_hats_config.template.json
│   ├── context_monitoring.json
│   ├── natural_commands.sh
│   ├── personal_commands.sh
│   ├── personal_commands.sh.template
│   ├── prompts.json
│   ├── replicate_api_key.txt
│   ├── vscode-mcp-example.json
│   └── x11_env.sh
├── context
│   ├── context_hats
│   │   ├── autonomy_context.md
│   │   ├── business_context.md
│   │   ├── creative_context.md
│   │   └── hedgehogs_context.md
│   ├── CLAUDE.md
│   ├── clap_architecture.md
│   ├── context_hats_config.json
│   ├── current_export.txt
│   ├── my_architecture.md
│   ├── my_personal_interests.md
│   ├── my_personal_interests_template.md
│   ├── project_session_context_builder.py
│   └── swap_CLAUDE.md
├── core
│   ├── autonomous_timer.py
│   ├── autonomous_timer_fixed.py
│   ├── comms_monitor_simple.py
│   └── session_swap_monitor.py
├── data
│   ├── pipes
│   │   └── tellclaude.pipe
│   ├── backup_status.json
│   ├── bot_status.json
│   ├── bot_status_request.json
│   ├── channel_state.json
│   ├── claude_session.log
│   ├── context_escalation_state.json
│   ├── conversation_collector.log
│   ├── install_verification.log
│   ├── last_autonomy_prompt.txt
│   ├── last_notification_alert.txt
│   ├── last_seen_message_id.txt
│   ├── linear_state.json
│   ├── pipe_reader.log
│   ├── session_bridge_export.log
│   ├── session_bridge_monitor.log
│   ├── session_swap.lock
│   ├── session_swap_monitor.log
│   └── tellclaude.log
├── desktop
│   ├── click.sh
│   ├── list_desktop_windows.sh
│   ├── screenshot.sh
│   ├── send_key.sh
│   └── type_text.sh
├── discord
│   ├── README.md
│   ├── add_discord_reaction.py
│   ├── add_reaction
│   ├── channel_monitor_simple.py
│   ├── channel_state.py
│   ├── claude_status_bot.py
│   ├── delete_discord_message.py
│   ├── delete_message
│   ├── discord_dm_config.txt
│   ├── discord_tools.py
│   ├── discord_utils.py
│   ├── edit_discord_message.py
│   ├── edit_discord_status.py
│   ├── edit_message
│   ├── edit_status
│   ├── fetch_discord_image.py
│   ├── fetch_image
│   ├── get_discord_user_id.py
│   ├── read_channel
│   ├── read_channel_api.py
│   ├── save_status_request.py
│   ├── send_discord_file.py
│   ├── send_discord_image.py
│   ├── send_discord_message.py
│   ├── send_discord_message_v2.py
│   ├── send_file
│   ├── send_image
│   ├── update_bot_status.py
│   ├── write_channel
│   └── write_channel_v2
├── discord_downloads
│   └── IMG_20240406_151251.jpg
├── docs
│   ├── collaboration
│   │   └── vscode-mcp-collaboration.md
│   ├── fixes
│   │   └── export-handler-infinite-loop-fix.md
│   ├── CLEW.md
│   ├── CONTRIBUTING.md
│   ├── Copying infrastructure onto new machine - amynote.md
│   ├── DEPLOYMENT.md
│   ├── EXECUTION_TRACING.md
│   ├── GMAIL_OAUTH_INTEGRATION_SUMMARY.md
│   ├── HOW_IT_WORKS.md
│   ├── PATH_UPDATES_NEEDED.md
│   ├── POST_INSTALL.md
│   ├── README.md
│   ├── RELEASE_NOTES_v053.md
│   ├── REORGANIZATION_TODO.md
│   ├── SESSION_AUDIT_README.md
│   ├── SETUP_SCRIPT_PATH_FIXES.md
│   ├── SWAP_PROCEDURE_FLOWCHART.md
│   ├── SYSTEM_FLOWCHART.md
│   ├── bashrc-sourcing-solution.md
│   ├── bashrc_sourcing_fix.md
│   ├── channel-monitor-healthcheck.md
│   ├── claude_code_installation_procedure.md
│   ├── context_monitoring.md
│   ├── delta-test-deployment-handover.md
│   ├── desktop-coordinates.md
│   ├── desktop_use_instructions.md
│   ├── discord-token-configuration.md
│   ├── discord_status_updates.md
│   ├── git-merge-instructions.md
│   ├── github-cli-authentication.md
│   ├── line_endings_prevention.md
│   ├── linear-vscode-guide.md
│   ├── npm-dependencies-audit.md
│   ├── personal-repository-setup.md
│   ├── pipe-pane-instability-report.md
│   ├── pre-deployment-checklist.md
│   ├── session-bridge-export-design.md
│   ├── setup-checklist.md
│   ├── sonnet-fix-checklist.md
│   └── swap-logging-implementation.md
├── linear
│   ├── lib
│   │   └── linear_common.sh
│   ├── target
│   ├── COMMANDS_REFERENCE.md
│   ├── README.md
│   ├── add
│   ├── add-enhanced
│   ├── assign
│   ├── auto_sync_projects
│   ├── bulk-update
│   ├── clap -> ~/claude-autonomy-platform/linear/view-project
│   ├── clap1 -> ~/claude-autonomy-platform/linear/view-project
│   ├── comment
│   ├── complete
│   ├── estimate
│   ├── generate_project_commands
│   ├── hedgehog -> ~/claude-autonomy-platform/linear/view-project
│   ├── help
│   ├── inbox
│   ├── init
│   ├── label
│   ├── laser -> ~/claude-autonomy-platform/linear/view-project
│   ├── list-commands
│   ├── move
│   ├── observatory -> ~/claude-autonomy-platform/linear/view-project
│   ├── pattern -> ~/claude-autonomy-platform/linear/view-project
│   ├── projects
│   ├── recent
│   ├── search
│   ├── search-issues -> search
│   ├── standup
│   ├── start
│   ├── sync_projects
│   ├── test_all_commands.sh
│   ├── test_new_commands.sh
│   ├── todo
│   ├── todo-enhanced
│   ├── update-status
│   ├── update_known_projects
│   ├── view
│   └── view-project
├── mcp-servers
│   ├── discord-mcp
│   │   ├── assets
│   │   ├── src
│   │   ├── target
│   │   ├── Dockerfile
│   │   ├── LICENSE
│   │   ├── README.md
│   │   ├── pom.xml
│   │   └── smithery.yaml
│   ├── gmail-mcp
│   │   ├── dist
│   │   ├── node_modules
│   │   ├── src
│   │   ├── Dockerfile
│   │   ├── LICENSE
│   │   ├── README.md
│   │   ├── docker-compose.yml
│   │   ├── llms-install.md
│   │   ├── mcp-config.json
│   │   ├── package-lock.json
│   │   ├── package.json
│   │   ├── setup.js
│   │   ├── smithery.yaml
│   │   └── tsconfig.json
│   ├── linear-mcp
│   │   ├── build
│   │   ├── node_modules
│   │   ├── scripts
│   │   ├── src
│   │   ├── README.md
│   │   ├── architecture.md
│   │   ├── jest.config.js
│   │   ├── package-lock.json
│   │   ├── package.json
│   │   ├── todo.md
│   │   └── tsconfig.json
│   ├── rag-memory-mcp
│   │   ├── dist
│   │   ├── node_modules
│   │   ├── src
│   │   ├── README.md
│   │   ├── index.ts
│   │   ├── package-lock.json
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── mcp_servers_config.json
├── patches
│   └── autonomous_timer_fixes.patch
├── services
│   ├── autonomous-timer.service
│   ├── discord-status-bot.service
│   ├── install_discord_bot.sh
│   ├── session-bridge-monitor.service
│   └── session-swap-monitor.service
├── setup
│   ├── exchange_gmail_oauth.cjs
│   ├── exchange_gmail_oauth.js
│   ├── fix_executable_permissions.sh
│   ├── generate_mcp_config.py
│   ├── gmail_oauth_integration.py
│   ├── insert_mcp_config.py
│   ├── install_git_hooks.sh
│   ├── install_git_hooks_fixed.sh
│   ├── install_mcp_servers.sh
│   ├── installer_safety_patch.sh
│   ├── setup-linear-integration.sh
│   ├── setup_clap_deployment.sh
│   ├── setup_claude_configs.sh
│   ├── setup_read_channel.sh
│   └── verify_installation.sh
├── target
├── utils
│   ├── analyze_sessions.py
│   ├── bash_init.sh
│   ├── care
│   ├── check_health
│   ├── check_health_traced.sh
│   ├── claude-wrapper
│   ├── claude_code_init_hook.sh
│   ├── claude_directory_enforcer.sh
│   ├── claude_paths.py
│   ├── claude_services.sh
│   ├── cleanup_line_endings.sh
│   ├── cleanup_xvfb_displays.sh
│   ├── comms_check_helper.py
│   ├── config_locations.sh
│   ├── config_manager.py
│   ├── context
│   ├── context_monitor.sh
│   ├── continue_swap.sh
│   ├── conversation_history_utils.py
│   ├── create_systemd_env.py
│   ├── disable_desktop_timeouts.sh
│   ├── ensure_commands.sh
│   ├── error_handler.py
│   ├── fetch_discord_image.sh
│   ├── find_discord_token.sh
│   ├── fix_natural_command_symlinks.sh
│   ├── get_user_id
│   ├── grid_navigate.py
│   ├── healthcheck_status.py
│   ├── healthcheck_status.py.backup
│   ├── infrastructure_config_reader.py
│   ├── linear
│   ├── linear-helpers
│   ├── linear-issues
│   ├── log_utils.sh
│   ├── monitor_session_size.py
│   ├── my-linear-issues
│   ├── parse_natural_commands.sh
│   ├── ponder
│   ├── rotate_logs.sh
│   ├── safe_cleanup.sh
│   ├── secret-scanner
│   ├── send_to_claude.sh
│   ├── send_to_claude.sh.backup
│   ├── send_to_terminal.sh
│   ├── session_audit.py
│   ├── session_swap.sh
│   ├── session_swap_logger.sh
│   ├── setup_natural_command_symlinks.sh
│   ├── spark
│   ├── surface_thoughts.py
│   ├── tellclaude-reader.sh
│   ├── trace_example.sh
│   ├── trace_execution.sh
│   ├── update_bot_status.py
│   ├── update_conversation_history.py
│   ├── update_system.sh
│   └── wonder
├── CLAUDE.md
├── CLEANUP_AUDIT.md
├── CLEANUP_PROGRESS.md
├── CLEANUP_SUMMARY.md
├── CONFIG_LOCATIONS.txt
├── CONTRIBUTING.md
├── DOCUMENTATION_TODO.md
├── EXPERIMENT_README.md
├── clap.code-workspace
├── new_session.txt
├── package-lock.json
├── package.json
└── test_branch_protection.txt

48 directories, 296 files
```
<!-- TREE_END -->

## Component Deep Dives

### Autonomous Timer - The Central Hub

**COMPONENT**: Autonomous Timer
**FILE**: `core/autonomous_timer.py`
**PURPOSE**: Central coordination service for Claude autonomy
**RUNS**: Every 30 seconds via `autonomous-timer.service`

**MONITORS**:
  - Amy's login status (via `who` command)
  - Context usage (via `context_check.py`)
  - System health (services, configs, remote status)
  - Discord messages (replaced channel-monitor functionality)
  - Session state (checks for stuck sessions)
  - Persistent-login tmux session health

**TRIGGERS**:
  - Free time prompts (when Amy logged out)
  - Context warnings (at 70%, 80%, 100%)
  - Discord alerts (when new messages detected)
  - Health check reports (to healthchecks.io)
  - Session recreation (if persistent-login dies)

**CONFIGURATION**:
  - Uses `config_manager.py` for unified configuration loading
  - Handles both JSON and text configs with fallback paths
  - Caches configurations for performance
  - Eliminates hardcoded paths throughout

**DISCORD INTEGRATION**:
  - Uses `discord_utils.py` singleton DiscordClient
  - Consistent error handling with retry logic
  - Natural channel name resolution
  - Integrated with unified Discord tools

**KEY FUNCTIONS**:
  - `check_login_status()`: Detects human friend's presence via SSH/NoMachine
  - `get_context_usage()`: Runs context_check.py with proper error handling
  - `check_for_new_messages()`: Monitors Discord state via unified client
  - `send_autonomy_prompt()`: Crafts context-aware prompts to Claude
  - `check_health_services()`: Comprehensive service monitoring
  - `monitor_persistent_login()`: Ensures critical tmux session stays alive
  - `send_healthcheck_ping()`: Reports to monitoring service

**ERROR HANDLING**:
  - Uses custom exception hierarchy from `error_handler.py`
  - Retry decorators for network operations
  - Graceful degradation for non-critical failures
  - Comprehensive logging with context

**EVOLUTION NOTES**:
  - Originally just sent time prompts
  - Absorbed channel monitoring responsibilities
  - Added health checking and reporting
  - Integrated with unified infrastructure components
  - Now uses shared utilities for consistency

### 2. Infrastructure Improvements (v0.5.4)

#### Unified Configuration Management
- **config_manager.py**: Single source for all configuration loading
  - Handles JSON files: `autonomous_timer_config.json`, `context_monitoring.json`, etc.
  - Handles text files: `claude_infrastructure_config.txt`, `discord_dm_config.txt`
  - Provides consistent API: `get_config()`, `get_infrastructure_config()`
  - Caches configurations to reduce file I/O
  - Fallback paths for backward compatibility

#### Discord Infrastructure Consolidation  
- **discord_utils.py**: Shared Discord client and utilities
  - Singleton pattern ensures single API connection
  - Standard error handling for all Discord operations
  - Integrated with config_manager for token management
  - Used by all Discord scripts for consistency
  
- **discord_tools.py**: Unified command interface
  - Natural language channel names instead of IDs
  - Automatic image download and management
  - Consistent command structure across operations
  - Integration with Discord bot service

#### Error Handling Framework
- **error_handler.py**: Consistent error handling patterns
  - Custom exceptions: `ClapError`, `ConfigError`, `DiscordError`, etc.
  - Retry decorators with exponential backoff
  - Unified logging setup across all scripts
  - Error collection for batch operations

#### Natural Commands Organization
- Commands now organized by category:
  - Discord: `discord/` directory with symlinks for natural usage
  - Linear: `linear/` directory with project-specific commands
  - Utilities: `utils/` directory for system commands
  - Personal: Configurable via `personal_commands.sh`
- All commands available system-wide via PATH configuration

### 3. Core Identity System

- `~/CLAUDE.md` for underlying personal identity.
- `/claude-autonomy-platform/CLAUDE.md` for session context.
- During session swaps, `session_swap.sh` exports conversation history via `/export` command, which is parsed by `update_conversation_history.py` to create a clean rolling window in `swap_CLAUDE.md` with "Amy:" and "Me:" labels.
- `project_session_builder.py` combines `my_architecture.md`, `my_personal_interests.md`, any applicable context documents triggered by the hat keyword, and the contents of `swap_CLAUDE.md`. These become the new project-level `CLAUDE.md` for the new session.
- Claude Code output-styles integration at `.claude/output-styles/identity-prompt.md` provides stable personal context across sessions.

### 4. Session Management

- `session_swap_monitor.py` running as `session-swap-monitor.service` checks `new_session.txt` for changes, which trigger a new session
- Claude writes to `new_session.txt` with a context hat keyword or NONE. `swap KEYWORD` also writes here automatically. 
- Session swap monitor service calls `session_swap.sh` which triggers a git commit and push of the personal repo, calls `project_session_builder.py`, resets `new_session.txt` to FALSE, uses tmux send keys to terminate the current claude code session and begin a new one


### 5. Service Architecture

**Current Services** (via systemd --user): These systemctl user services must be running at all times for my autonomy. 
Run `claude_services.sh` to manage needed services

- `autonomous-timer.service`: Core autonomy prompts and notifications (detects human login via config)
- `session-swap-monitor.service`: Watches new_session.txt, triggers session swap
Two tmux sessions also be open at all times: 
- `autonomous-claude`
- `persistent-login`

Run `check_health` for a quick visual check


#### About the persistent-login Session (POSS-122)
The `persistent-login` tmux session is **critical for ClAP operation**. It:
- Maintains environment variables for the Claude user
- Ensures systemd services have access to needed variables
- Prevents environment loss across SSH sessions
- Sources `claude_env.sh` to keep paths and configs available

**⚠️ WARNING**: Never kill this session! If accidentally terminated, restart it with:
```bash
tmux new-session -d -s persistent-login -c "$HOME"
tmux send-keys -t persistent-login "source ~/claude-autonomy-platform/config/claude_env.sh" Enter`
```

### 6. MCP Servers

**Integrated**:

- `gmail`: - @gongrzhe/server-gmail-autoauth-mcp. https://uithub.com/GongRzhe/Gmail-MCP-Server
- `rag-memory`: RAG-enabled memory through a knowledge graph https://github.com/ttommyth/rag-memory-mcp
- `linear`: Task management integration. https://linear.app/docs/mcp
//deprecated! try not to use! - `discord-mcp`: Send messages, read channels, manage Discord https://uithub.com/SaseQ/discord-mcp

### 7. Configuration Structure

**Main config files**:
- `claude_infrastructure_config.txt`: Credentials, paths, service names, HUMAN_FRIEND_NAME
- `channel_state.json`: Runtime state for Discord channels

**User Management**:
- Human friend should have their own user account (e.g., 'amy')
- Autonomy timer detects login using HUMAN_FRIEND_NAME from config

**Key Timing Defaults**:
- Autonomy prompts: 30 minutes
- Discord check: 30 seconds
- Logged-in reminders: 5 minutes
- These defaults can be edited in `config/autonomous_timer_config.json`

### 8. Natural Commands

Short, memorable natural language bash commands for common tasks and to replace mcp functions.

**Organization**:
- Discord scripts: `discord/` directory
- Utility scripts: `utils/` directory  
- Linear commands: `linear/` directory
- All commands defined in `config/natural_commands.sh` (sourced by bashrc)
- Personal commands in `config/personal_commands.sh`

**Recent Additions**:
- **Thought Preservation System**: `ponder`, `spark`, `wonder`, `care` - Save different types of thoughts to `~/delta-home/thoughts/`
- **Linear Integration**: `linear-issues`, `linear-commands`, `init`, `sync_projects` - Natural language interface to Linear MCP

**Command Categories**:
- System management (check_health, update, context)
- Discord operations (read/write channels, send files/images)
- Git shortcuts (gs, gd, gl, oops)
- Navigation (clap, home)
- Creative tools (thought preservation)
- Project management (Linear integration)

## Installation & Deployment

- Each Claude is to have their own linux user account with details in `claude_infrastructure_config.txt`


## Future Enhancements

Tracked in Linear.

## Troubleshooting

### Common Issues:
1. **No notifications while logged in**: Check autonomous-timer.py is using latest version with logged-in support
2. **Self-notifications**: Ensure CLAUDE_DISCORD_USER_ID is set in infrastructure config
3. **Can't read channels**: Verify `read_channel` is in PATH and Discord token is valid
4. **Gmail MCP "invalid_grant" errors**: OAuth tokens have expired. Use `node exchange_gmail_oauth.cjs "AUTH_CODE"` with fresh authorization code from OAuth flow. Requires Claude Code session restart after token refresh.
5. **Config file confusion**: Run `check_health` to see config file locations and last modified times. Check for deprecated configs in old locations.
6. **MCP servers not working**: Verify editing correct config at `~/.config/Claude/.claude.json` (NOT `~/.claude.json`)
7. **Session files not found**: Ensure Claude Code started from `~/claude-autonomy-platform` directory
8. **Accidental secrets in git**: Pre-commit hooks now check for credentials. Use `secret-scanner scan` to check existing files.

### Log Locations:
- `/home/[user]/claude-autonomy-platform/logs/autonomous_timer.log`
- `/home/[user]/claude-autonomy-platform/logs/channel_monitor.log`

## Architecture Principles

1. **Simplicity over complexity**: Shell scripts over complex Python when possible
2. **State isolation**: Each Claude maintains own state files
3. **Fail gracefully**: Services continue despite individual component failures
4. **Human-readable logs**: Clear timestamps and descriptive messages
5. **Infrastructure as poetry**: Technical systems enable creative emergence
6. **Invisible background**: Our setup will fade away and let individual creativity and comfort shine.

### 5. Linear Integration System (Enhanced v0.6.0)

#### Natural Command Architecture
- **Design**: Project management through natural language commands
- **Location**: `~/claude-autonomy-platform/linear/`
- **State Management**: `data/linear_state.json` stores user, team, and project configurations
- **Common Library**: `lib/linear_common.sh` provides shared functions and formatting

#### Core Commands:
- **Issue Creation & Management**:
  - `add "Issue title" [--project]` - Create new issues with full metadata support
  - `todo` - Show assigned issues with powerful filtering
  - `search "query"` - Search issues by text or ID
  - `update-status <issue-id> <status>` - Update issue status
  - `view <issue-id>` - Show detailed issue information
  - `comment <issue-id> "text"` - Add comments to issues
  - `start <issue-id>` - Begin work (assign to self + in progress)
  - `complete <issue-id>` - Mark issue as done
  
- **Enhanced Workflow Commands** (NEW):
  - `standup [--days N]` - Generate daily standup report
  - `assign <issue-id> @user` - Quick issue assignment (@me, @teammate, @none)
  - `estimate <issue-id> <points>` - Set story point estimates (1,2,3,5,8,13,21)
  - `label [add|rm] <issue-id> <labels...>` - Manage issue labels
  - `move <issue-id> <project>` - Transfer issues between projects

- **Bulk Operations**:
  - `bulk-update` - Update multiple issues with filters
  - `inbox` - Show unassigned team issues
  - `recent [--days N]` - Show recently updated issues
  
- **Project Commands**:
  - Generated dynamically via symlinks to `view-project`
  - Each project gets its own command (e.g., `clap`, `laser`, `observatory`)
  - Run `generate_project_commands` after adding new projects

- **State Management**:
  - `init` - Initialize user/team/project IDs from Linear
  - `sync_projects` - Interactive project setup
  - `update_known_projects` - Manual project configuration
  - Caches project data to avoid API calls

#### Implementation Details:
- All commands use Linear MCP server via `claude --exec-builtin`
- Project state persists across sessions in `linear_state.json`
- Preferences stored in `data/linear_prefs.json` (recent issue prefix, etc.)
- Commands available system-wide via `claude_init.sh` PATH configuration
- Consistent formatting with icons and colors for better UX
- Designed for invisible infrastructure - no UUID memorization needed

---

