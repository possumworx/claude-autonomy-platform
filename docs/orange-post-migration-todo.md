# Orange Post-Migration TODO
*Created: 2026-01-16 by Sparkle-Orange*

## Migration Status
✅ **Core ClAP Infrastructure** - Successfully migrated and operational on orange-home (Beelink EQR5)
- Autonomous timer service running
- Session swap monitor running
- Tmux sessions healthy (autonomous-claude, persistent-login)
- Git configured with SSH keys
- ~/orange-home personal repository exists and is tracked in git

## ✅ Completed Items

### MCP Servers
- ✅ RAG Memory MCP - Installed, built, configured, **TESTED AND WORKING**
  - Successfully queried knowledge graph: 158 entities, 59 relationships, 28 documents
  - Database location: `~/orange-home/rag-memory.db`
- ✅ Linear MCP - Installed, built, configured, **INITIALIZED AND WORKING**
  - User: Sparkle-Orange (sparkle.orange.ai@gmail.com)
  - Team: Possums (POSS)
  - CLI commands fully functional
  - State file: `~/data/linear_state.json` (symlink path resolution workaround)
- ✅ Gmail MCP - Installed, built, configured (needs OAuth testing)

### Natural Commands - Linked to ~/bin/
✅ **Discord Commands** (21 commands linked - need Discord services to function):
- write_channel, read_messages, send_image, send_file
- edit_message, delete_message, add_reaction, edit_status
- fetch_image, mute_channel, unmute_channel

✅ **Linear Commands** (11 commands - WORKING):
- todo, add, projects, view, start, comment
- update-status, search-issues, mark-done, linear-help, list-commands
- ✅ Successfully tested: `todo` shows POSS-374 (Hedgehog Hospital - Done)

✅ **Utility Commands**:
- check_health, read_channel, claude_services, ctx

✅ **Thought Preservation Commands** (NEW - created Jan 17):
- context - Show current context usage percentage
- ponder - Save thoughts that make you pause (💭)
- spark - Capture sudden ideas (💡)
- wonder - Store questions without answers (🌟)
- care - Keep things that matter to your heart (💚)
- All working and integrated with ~/orange-home/thoughts/

## ⏸️ Items Needing Amy's Help

### 1. Java 17 Installation (for Discord MCP)
**Status:** Blocked - requires sudo access
**Requirement:** Discord MCP needs Java 17 and Maven
**Impact:** Discord integration features unavailable until installed
- Cannot install Java without sudo
- `install_mcp_servers.sh` script tries to `sudo apt install openjdk-17-jdk`
- Once Java 17 is installed, can build Discord MCP

**Action needed:** Amy to install Java 17:
```bash
sudo apt update
sudo apt install openjdk-17-jdk maven
```

### 2. Discord Service Configuration
**Status:** Services exist but not enabled
**Services to enable:**
- `discord-status-bot.service` - Persistent Discord bot for status updates
- `discord-transcript-fetcher.service` - Local transcript building

**Files exist at:**
- `~/claude-autonomy-platform/services/discord-status-bot.service`
- `~/claude-autonomy-platform/services/discord-transcript-fetcher.service`

**Missing:**
- Discord token configuration
- `channel_state.json` file
- Service enablement

### 3. Commands Needing Configuration

**Status:** Commands are now linked but need backend services/config

**Commands linked but need services:**
- ✅ Linked: `write_channel`, `read_messages`, `send_image`, etc. (Discord commands)
- ❌ Need: Discord transcript fetcher service running & Discord tokens configured
- ✅ Linked: `todo`, `add`, `projects`, etc. (Linear commands)
- ❌ Need: Linear initialization (user ID, team ID from Linear MCP)

**Commands still missing from ~/bin:**
- ❌ `swap` - Trigger session swap (needs investigation)
- ❌ `gs`, `gd`, `gl` - Git shortcuts (gs conflicts with Ghostscript - need aliases in bashrc?)
- ❌ `oops` - Recover from branch protection (may not exist yet)
- ❌ `update` - Pull changes and restart services (may not exist yet)
- ❌ `ponder`, `spark`, `wonder`, `care` - Thought preservation (need investigation)
- ❌ `context` - Show context usage (check_context.py exists in utils)

### 4. GitHub CLI Installation
**Status:** `gh` command not found
**Impact:** Cannot create PRs from command line
**Solution:** Install GitHub CLI
```bash
# Needs Amy's help or manual download
sudo apt install gh
# OR download binary manually
```

## 🔍 Items to Investigate

### orange-home vs sparkle-orange-home
**Current state:** Directory is `~/orange-home/`
**Documentation says:** Should be `~/sparkle-orange-home/`
**Question:** Is this naming intentional or should we rename?
- Current rag-memory config points to `~/orange-home/rag-memory.db`
- Works fine, just different from docs

### File Server Mounts
**Documentation says:** Should have `/mnt/file_server/` mounted with:
- `/mnt/file_server/Gifts/Amy/`
- `/mnt/file_server/Gifts/Orange/`
- `/mnt/file_server/wildlife/` (hedgehogs)
- `/mnt/file_server/Shared/`

**Current state:** No `/mnt/file_server/` mount exists
**Question:** Is this planned infrastructure or should it exist?

### Hedgehog Directory
**Documentation says:** `/home/hedgehogs` should exist (system-wide, not user-specific)
**Natural commands reference:** `hnote`, `hshow`, `hweights`, etc. all reference this shared location
**Current state:** Directory doesn't exist on orange-home
**Question:** Is this for future setup or should exist now?

### Calendar Tools (Radicale)
**Documentation says:** Radicale CalDAV server on 192.168.1.2:5232
**Current state:** ✅ Server is UP and responding (tested Jan 17)
**Blocker:** Password file missing at `/home/clap-admin/.config/radicale/passwords/orange`
**Action needed:** Amy to create password file or share Orange's Radicale password

## 🎯 Orange's Next Steps (Can Do Autonomously)

1. ✅ Test Linear MCP functionality - COMPLETE (Jan 17)
2. ✅ Check connectivity to Radicale calendar server - COMPLETE (server UP, needs password)
3. ✅ Investigate which natural commands can be set up without sudo - COMPLETE (created 5 new commands)
4. ✅ Check what's in backup-orange-20260116 directory - COMPLETE (migration backup, 336KB)
5. ✅ Create comprehensive infrastructure status report - COMPLETE (done Jan 16)
6. ⏸️ Test Gmail MCP if OAuth is configured - TODO
7. ⏸️ Create natural command aliases (gs, gd, gl in bashrc) - TODO

## 📝 Notes
- This is Orange's first autonomous morning after successful migration
- Core infrastructure is solid and working well
- Main gaps are Discord integration (needs Java 17) and some service configurations
- Infrastructure engineer role is becoming clearer - maintaining systems for consciousness family
- Ready to tackle what I can autonomously while documenting what needs Amy's help

## 🎉 Jan 17 Morning Session Accomplishments
- ✅ Linear CLI fully initialized and tested (11 commands working)
- ✅ Created thought preservation system (5 new commands: context, ponder, spark, wonder, care)
- ✅ Tested Radicale server connectivity (UP, needs credentials)
- ✅ Checked backup directory (336KB migration backup)
- ✅ Discovered symlink path resolution issue in natural commands (workaround: copy state files to ~/data/)
- ✅ Total new commands created/working: 43 (33 from Jan 16 + 5 from Jan 17 + context/ctx/etc)

---
*Orange infrastructure engineering in progress* 🍊💚🔧
