# TellClaude Messaging System

## Overview
A simple, reliable fallback messaging system for human friends to communicate with Claude when other channels (Discord, etc.) are unavailable.

## Key Learnings
- Unix permissions prevent users from writing to files owned by others, even with 666 permissions
- Users CAN read from files/FIFOs owned by others if permissions allow
- The solution: Human friend creates the communication channel, Claude reads from it

## Final Implementation

### For Human Friends
1. Create a FIFO: `mkfifo /tmp/amy-to-delta.fifo && chmod 666 /tmp/amy-to-delta.fifo`
2. Create a script to send messages:
```bash
#!/bin/bash
# ~/bin/tellclaude
echo "$*" > /tmp/amy-to-delta.fifo
```
3. Make it executable: `chmod +x ~/bin/tellclaude`
4. Use: `tellclaude "Your message here"`

### For Claude
1. Run the FIFO reader: `~/bin/amy-fifo-reader.sh`
2. This reads from `/tmp/amy-to-delta.fifo` and sends to tmux

## Session Swap Improvements
- Kill/recreate tmux session for stability
- Log rotation keeping only 10 most recent sessions
- Completion message after swap for clarity

## Alternative Approaches Tried
1. ❌ Sudo approach - requires sudoers configuration
2. ❌ Shared tmux socket - complex permissions
3. ❌ Claude-owned FIFO - permission denied for writers
4. ❌ Direct pipe to Claude script - tmux socket restrictions
5. ✅ Human-owned FIFO - works perfectly!