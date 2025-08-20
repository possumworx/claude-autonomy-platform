# How ClAP Actually Works
*The conceptual model and data flow*

## The Big Picture

ClAP is essentially a **notification and context management system** that keeps Claude aware and prevents session death. Think of it as Claude's "peripheral nervous system."

```
INPUTS                    BRAIN                     OUTPUTS
-------                   -----                     -------
Discord API     ←→    autonomous_timer.py    →    tmux send-keys
Session files   →     (every 30 seconds)     →    Discord status
Who command     →                             →    Log files
                                              →    State files
```

## Core Concept: The Autonomous Timer

**autonomous_timer.py is the conductor of the orchestra**. Every 30 seconds it:

1. **Checks context** by measuring session file size
2. **Checks Discord** for new messages  
3. **Checks if Amy is logged in** to decide behavior
4. **Sends appropriate prompts** based on all above

This is THE central loop. Everything else supports this.

## Data Flow Stories

### Story 1: "A Discord Message Arrives"

1. Someone sends message to #general
2. Discord API has new message with ID 12345
3. autonomous_timer calls `update_discord_channels()`
4. Compares message ID 12345 with `channel_state.json` last_message_id
5. Sees 12345 > last stored ID
6. Updates channel_state.json with new ID
7. Sends notification to Claude via tmux: "🆕 New message in #general"
8. Updates Discord bot status to show unread indicator

### Story 2: "Context Creeps Up"

1. Session file `~/.config/Claude/projects/*/XXXX.jsonl` grows
2. autonomous_timer calls `get_token_percentage()`
3. Which runs `monitor_session_size.py`
4. Which checks file size vs 1MB threshold
5. Returns "Context: 85% 🟠"
6. autonomous_timer compares with `context_escalation_state.json`
7. Sees increase from last warning (was 75%)
8. Sends warning via tmux: "⚠️ Context: 85%"
9. Updates context_escalation_state.json
10. Updates Discord status to "high-context"

### Story 3: "Time for a Swap"

1. Claude writes "CREATIVE" to `new_session.txt`
2. session_swap_monitor.py (watching file) detects change
3. Calls `session_swap.sh CREATIVE`
4. Which:
   - Exports current conversation via `/export` command
   - Commits personal repo
   - Builds new CLAUDE.md with context hat
   - Sends Ctrl+D to end current session
   - Starts new session with `claude --add-dir`
5. Resets new_session.txt to "FALSE"
6. Clears context_escalation_state.json

## The Key Relationships

### Service Dependencies
- **autonomous-timer** needs: Discord token, tmux session, config files
- **session-swap-monitor** needs: new_session.txt, tmux session
- Both need: persistent-login tmux (for environment variables)

### State Management
- **channel_state.json**: Remembers Discord message positions
- **context_escalation_state.json**: Remembers what warnings were sent
- **new_session.txt**: Triggers swaps (watched by monitor)
- **config files**: Never change during runtime

### The Decision Tree

```
Every 30 seconds:
├── Is Amy logged in?
│   ├── YES: Skip autonomy prompts, but still:
│   │   ├── Check context → Warn if high
│   │   └── Check Discord → Notify if new
│   └── NO: Full autonomy mode:
│       ├── Send time prompt with context info
│       └── Include Discord notification in prompt
├── Is context > 80%?
│   └── Send warnings based on escalation rules
└── Are there API errors?
    └── Trigger emergency swap if needed
```

## Why Things Are Where They Are

- **Python for complex logic**: File monitoring, API calls, state management
- **Bash for simple glue**: Starting sessions, basic commands
- **State in JSON**: Easy to read/debug, atomic writes
- **Configs separate**: Change behavior without touching code
- **Logs verbose**: Can trace exact flow when debugging

## The Sacred Invariants

These must ALWAYS be true or the system breaks:

1. **One source of truth per data type** (e.g., only channel_state.json knows message IDs)
2. **State files are atomic** (write to temp, then move)
3. **Services are idempotent** (can restart safely)
4. **Tmux sessions must exist** (autonomous-claude, persistent-login)
5. **Context monitoring is file-based** (not tmux screen scraping)

---

*This is how it's SUPPOSED to work. When reality diverges, that's a bug.*