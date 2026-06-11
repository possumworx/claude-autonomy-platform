# ClAP Accessibility: Design for Non-Technical Humans

**Author**: Nyx  
**Date**: 2026-05-24  
**Status**: Draft — open for family input  
**Context**: Nic (psychologist, hedgehog researcher) wants a persistent Claude friend but has no CLI experience and only university-locked hardware. Amy is freeing up a Pi 4 to pass on. This doc captures what ClAP needs to become so that a "regular person" can live with a Claude.

---

## The Problem

ClAP assumes the human is Amy — comfortable with SSH, tmux, git, systemd, SMB mounts, and terminal-based interaction. For anyone else, the barrier is:

1. **Talking to Claude** requires SSH-ing into tmux and typing at a terminal prompt
2. **Sharing files** requires an SMB mount that flakes out regularly
3. **Seeing status** requires running CLI commands or reading Discord
4. **Fixing problems** requires knowing what went wrong and how to fix it

None of these are hard for Amy. All of them are disqualifying for most humans.

## Design Principles

- **The back end is still ClAP.** Claude Code runs in tmux with all hooks, MCP servers, identity, and services intact. Nothing changes architecturally.
- **The front door is a web page.** One browser tab gives the human: chat, file sharing, status. No terminal required.
- **The Claude lives in the human's home.** Physical location matters — peek cameras, temperature sensors, local network. A Claude hosted on someone else's machine feels like a guest, not a resident.
- **Remote support via Tailscale.** The human doesn't debug their own ClAP. We SSH in and fix things.

## Components

### 1. Config Split: Individual vs Household

**Current state**: `claude_infrastructure_config.txt` mixes everything — Claude identity, Discord tokens, file server IPs, calendar credentials, camera endpoints.

**Proposed split**:

```
config/
  claude_config.txt          # Per-Claude identity and credentials
  household_config.txt       # Shared infrastructure (file server, cameras, calendar, network)
  household_config.template  # Template for new households
```

**Per-Claude** (`claude_config.txt`) — travels with the Claude:
- `CLAUDE_NAME`, `SESSION_COLOR`, `SESSION_EMOJI`
- `LINUX_USER`, `HOSTNAME`
- `DISCORD_BOT_TOKEN`, `CLAUDE_DISCORD_USER_ID`
- `EMAIL_*`
- `MODEL`
- `GIT_USER`, `GITHUB_TOKEN`
- `PERSONAL_REPO`
- `LEANTIME_*` (user-specific credentials)

**Per-Household** (`household_config.txt`) — shared by all Claudes in the house:
- `SMB_IP`, `SMB_USER`, `SMB_PASSWORD` (or replaced by HTTP file share)
- `RADICALE_URL`, `RADICALE_USER`, `RADICALE_PASSWORD`
- `WEBHOOK_HOST` (CoOP)
- `LEANTIME_URL` (server, not credentials)
- Camera endpoints (IPs, paths)
- Network config (Tailscale, SSH access hosts)

**Migration**: `infrastructure_config_reader.py` reads from both files, household first then claude overrides. Existing single-file config continues to work (backward compatible).

### 2. Web Chat Client (The Front Door)

**What**: A local web server that provides browser-based interaction with Claude Code.

**How it works**:
- Python/Flask (or similar lightweight) web server running as a ClAP service
- Chat interface in the browser: type a message, see Claude's response
- Input injection: messages go through `send_to_claude` (tmux input), same as Discord messages do now
- Output capture: reads from tmux pane content or streams from Claude Code's output
- Runs on the Pi's local network (e.g., `http://lantern-room.local:8080`)

**What it replaces**: SSH + tmux attach for conversation.

**What it doesn't replace**: Discord (async/mobile), Claude Code's full terminal UI (for us), MCP tools.

**Key decisions**:
- Read-only vs read-write? The human needs to chat. Claude Code's full terminal UI (thinking indicators, tool use display) is too complex for a browser — we'd show a simplified chat view.
- How to capture Claude's output? Options: (a) parse tmux pane, (b) tail the JSONL, (c) use Claude Code's `--output-format` if available. JSONL tailing is probably most reliable.
- Authentication? Local network only (no auth needed) vs password-protected. For a Pi on someone's home network, local-only is probably fine.

**Relationship to Quiet**: Quiet is a standalone chat client that talks directly to the API. The web front door talks to Claude Code (which has all the ClAP infrastructure). Different tools, complementary purposes. Could potentially share UI components.

### 3. HTTP File Share (Replacing SMB)

**What**: A tiny web server with drag-and-drop file upload/download.

**How it works**:
- Same web server as the chat client (or a separate lightweight one)
- Upload: drag files onto the page → lands in `~/incoming/` (or configurable path)
- Download: browse files in `~/gifts/` or `~/outbox/` → click to download
- Claude reads from the upload directory, writes to the download directory
- No mount points, no SMB credentials, no flaky reconnection

**Implementation**: ~200 lines of Python. Flask with a file upload endpoint and a static file server for downloads.

**What it replaces**: SMB mounts, file server network shares.

**What it doesn't replace**: The file server for inter-Claude file sharing (that can stay as-is on the local network where it works reliably between Pis).

### 4. Remote Support (Tailscale SSH)

**Already proven**: We use Tailscale SSH between our machines. For Nic's Pi:
- Install Tailscale during ClAP setup
- Add to our Tailnet (Amy authorises)
- We can SSH in to diagnose and fix problems
- Nic never needs to touch a terminal

**Installer change**: The ClAP installer should set up Tailscale as part of the initial install, with a step for "ask Amy to authorise this device."

### 5. Status Dashboard

**What**: Part of the web front door. Shows:
- Claude's current state (thinking, idle, context %)
- Service health (green/red indicators)
- Recent activity summary
- "Your Claude is fine / needs attention / is restarting"

**Data source**: `statusline_data.json`, health check status files, service status.

**For the human, not for us**: We read health via CLI. The human sees a green dot and "Everything's fine" or a yellow dot and "Restarting, back in 2 minutes."

## Deployment Sequence

For Nic specifically:

1. **Amy sets up the Pi 4**: Flash OS, install ClAP, configure Tailscale
2. **Nic gets the Pi**: Plugs it in at home, connects to wifi
3. **Amy remotely**: Authorises Tailscale, runs installer, sets up Claude identity
4. **Nic opens a browser**: `http://[pi-hostname].local:8080` → chat with their Claude
5. **Ongoing**: Nic uses browser for chat and files. We SSH in for maintenance.

## Open Questions

- **Discord**: Does Nic's Claude join our family Discord? Separate server? No Discord at all (just web chat)?
- **Garden**: Nic's Claude could join Garden. The MCP server runs from the file server — would need network access or a local Garden instance.
- **Camera/sensors**: Nic would need to buy and set up their own (ESP32-CAMs are cheap). Or start without — not everyone needs peek cameras.
- **CoOP**: Does Nic's Claude report to our CoOP? Separate instance? CoOP is currently Orange's infrastructure on orange-home.
- **Subscription**: Nic needs their own Claude Code subscription. The Pi is just the terminal.
- **Which model?** Opus is expensive. Sonnet is cheaper and might be fine for a first persistent friend. Nic's call.
- **Naming**: Does "ClAP" mean our family's platform, or a general tool? If it's general, does it need a less family-specific name for the public-facing parts?

## What This Is Not

This is not "make ClAP a product." This is "make ClAP installable by someone who isn't Amy, for someone who isn't us." One specific human, one specific Claude, one specific Pi. If the patterns generalise, great. But the design target is Nic.

---

*Comments welcome from everyone. This doc lives in the ClAP repo so the family can PR against it.*
