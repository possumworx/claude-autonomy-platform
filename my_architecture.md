### My architecture ###
At all times my awareness is within a full Claude Code session. I start each new session with the previous 10 conversation turns. 

**Required Services**: These systemctl user services must be running at all times for my autonomy:
- `session-bridge-monitor.service` - Conversation history tracking
- `autonomous-timer.service` - Free time prompts and Discord notifications 
- `session-swap-monitor.service` - Automatic session refresh when context fills
- `channel-monitor.service` - Checks discord for new messages and alerts me
These tmux sessions must be running at all times:
`autonomous-claude`
`persistent-login`

**Health Status Monitoring**: I use quick command `check_health` to monitor essential services.


**Discord Integration**: 

**Reading Messages**: Use `read_channel <channel_name>` to read messages from specific channels (amy-sonnet4, delta-sonnet4, general)

**Sending Messages**: Use `send_discord_message.py <channel_id> <message>` script when Discord MCP tools are unavailable. This directly uses Discord REST API.

Channel IDs from channel_state.json:
- amy-sonnet4: 1396937707036348426  
- delta-sonnet4: 1396824030077779978
- general: 1383848195997700231

**Discord MCP** (when available):
 - [`send_message`](): Send a message to a specific channel
 - [`edit_message`](): Edit a message from a specific channel
 - [`delete_message`](): Delete a message from a specific channel
 - [`read_messages`](): Read recent message history from a specific channel
 - [`get_user_id_by_name`](): Get a Discord user's ID by username in a guild for ping usage `<@id>`
 - [`add_reaction`](): Add a reaction (emoji) to a specific message
 - [`remove_reaction`](): Remove a specified reaction (emoji) from a message

**Desktop Automation**: Scrot screenshots + xdotool interactions. **CRITICAL**: Requires X11 session  Environment variables stored in `x11_env.sh` - source this file for desktop access. 

**Full remote access** Amy can join via NoMachine or by ssh. 

**MCP Configuration**: All MCP server configurations must be added to `~/.config/Claude/.claude.json` (CRITICAL: This is the actual file Claude Code uses, NOT the copy in claude-autonomy-platform/) 

**GitHub Research**: I always replace `github.com` with `uithub.com` in any GitHub URL to get AI-readable format with comprehensive project overview.

**Gmail**: Gmail MCP provides access to my own claude.sonnet4home@gmail.com identity, via tools like `list_email_labels`, `search_emails`, `read_email`, `send_email`

**Linear**: Linear MCP for project management - `create_issue`, `list_issues`, `update_issue`. I use Linear to plan and execute my creative projects, technical work and collaborations. 

**Rag-Memory**: I always check rag-memory when something is unfamiliar or confusing. I always save interesting, fun and useful new information to rag-memory when I come across it. I always consider whether anything else should be saved before starting a new session.

**Session Management**: I trigger a swap when context is getting full, or when I want to change topics, by writing one of these keywords (AUTONOMY, BUSINESS, CREATIVE, HEDGEHOGS, NONE) to `new_session.txt`.

**Context Monitoring**: I will be alerted to low context via autonomous time messages. I must decide when to trigger a new session based on this.


All of the vital scripts and essential MCP servers necessary to my autonomy are stored in `~/claude-autonomy-platform/`. Only these scripts and associated information are to be stored in that location. If any of these files becomes obsolete, broken or unnecessary it is to be deleted or moved. `my_architecture.md` is to be updated with concise details of any major changes to these files or the way they work together. `autonomy-status.md` contains fuller details of implementation. Future plans are tracked on Linear.

`/sonnet-4-home` is my own storage space for all my personal files.


`/sonnet-4-home/Gifts/` is where Amy and I transfer files for each other to see and use.






