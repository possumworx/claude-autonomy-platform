# Tellclaude Messaging System Implementation

## Overview
A simple, reliable fallback messaging system that allows human friends to send messages to Claude instances even when they're stuck at 100% context or unresponsive. Uses named pipes (FIFOs) and integrates with the existing session-swap-monitor service.

## Architecture
- **FIFO Location**: `/tmp/amy-to-delta.fifo` (to be renamed to `/tmp/human-to-claude.fifo`)
- **Service**: Integrated into `session-swap-monitor.py` (checks every 2 seconds)
- **No sudo required**: Human friend creates and owns the FIFO
- **Automatic**: Runs continuously as part of session-swap-monitor

## Key Design Decisions
1. **Human-owned FIFO**: Solves Unix permission restrictions where users can't write to others' files
2. **Integration with session-swap-monitor**: Avoids creating another service, uses existing 2-second check cycle
3. **Simple text protocol**: Just echo messages to the FIFO, no complex formatting needed

## Setup Instructions

### For Human Friend (Amy)
1. Create the FIFO once:
   ```bash
   mkfifo /tmp/amy-to-delta.fifo && chmod 666 /tmp/amy-to-delta.fifo
   ```

2. Create tellclaude script:
   ```bash
   cat > ~/bin/tellclaude.sh << 'EOF'
   #!/bin/bash
   echo "$*" > /tmp/amy-to-delta.fifo
   EOF
   chmod +x ~/bin/tellclaude.sh
   ```

3. Add alias to .bashrc:
   ```bash
   alias tellclaude='~/bin/tellclaude.sh'
   ```

### For Claude (Delta)
The FIFO reading is integrated into `session-swap-monitor.py`. The service:
- Checks the FIFO every 2 seconds using non-blocking I/O
- Sends any messages to the tmux session
- Automatically sends Enter key after each message
- Logs all received messages

## Usage
Human friend sends messages with:
```bash
tellclaude "Your message here"
```

Or directly:
```bash
echo "Your message" > /tmp/amy-to-delta.fifo
```

## Implementation Details

### session-swap-monitor.py additions:
```python
def check_fifo():
    """Check if FIFO has data and send to tmux if it does"""
    try:
        if not os.path.exists(FIFO_PATH):
            return
        
        if not stat.S_ISFIFO(os.stat(FIFO_PATH).st_mode):
            return
        
        # Non-blocking read from FIFO
        with open(FIFO_PATH, 'r', os.O_NONBLOCK) as fifo:
            readable, _, _ = select.select([fifo], [], [], 0)
            if readable:
                message = fifo.read().strip()
                if message:
                    log(f"Received tellclaude message: {message}")
                    subprocess.run(['tmux', 'send-keys', '-t', TMUX_SESSION, message])
                    subprocess.run(['tmux', 'send-keys', '-t', TMUX_SESSION, 'Enter'])
    except (IOError, OSError):
        pass
```

## Benefits
- **Always available**: Works when Claude is stuck at 100% context
- **No sudo required**: Avoids security complications
- **Simple and reliable**: Minimal moving parts
- **Integrated**: Uses existing infrastructure
- **Low overhead**: Piggybacks on existing 2-second check cycle

## Troubleshooting
1. **Permission denied**: Ensure human friend owns the FIFO
2. **Messages not appearing**: Check if session-swap-monitor is running
3. **FIFO missing after reboot**: Add FIFO creation to user's login scripts

## TODO (for tomorrow)
1. Rename FIFO to `/tmp/human-to-claude.fifo` for generic naming
2. Update `session-swap-monitor.py` to use new FIFO name
3. Add to Ansible playbook for automatic setup on all Claude boxes
4. Test on Sonnet's box and other instances
5. Consider adding FIFO auto-creation on boot