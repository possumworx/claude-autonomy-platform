# Desktop Automation Tools (ARCHIVED)

**Moved to old/: January 20, 2026**
**Reason:** X11 desktop automation not currently in use

## What This Was

These tools enabled Claude to interact with a Linux desktop environment via X11, allowing:
- Taking screenshots
- Clicking at screen coordinates
- Sending keystrokes
- Typing text
- Listing open windows

## Why It Was Archived

The ClAP infrastructure evolved to primarily use:
- Terminal/CLI interactions via Claude Code
- Discord for communication
- MCP servers for tool access

Direct desktop automation wasn't needed for the current workflow. These tools could be revived if a future use case requires visual desktop interaction (e.g., GUI testing, visual automation tasks).

## Files

```
desktop/
├── click.sh              # Click at X,Y coordinates
├── list_desktop_windows.sh  # List open windows
├── screenshot.sh         # Capture screen to file
├── send_key.sh          # Send keyboard input
└── type_text.sh         # Type text string

utils/
└── grid_navigate.py     # Grid-based screen navigation helper
```

## Dependencies

These scripts required:
- X11 display server
- `xdotool` - X11 automation tool
- `scrot` - Screenshot utility
- A running desktop environment

## Known Issues at Archive Time

- Scripts had hardcoded path `/home/sonnet-4/claude-autonomy-platform/x11_env.sh` 
- Would need path fixes if revived
- `x11_env.sh` was already in `old/` directory

## Revival Notes

If bringing these back:
1. Fix the x11_env.sh path references
2. Ensure X11 tools are installed (`sudo apt install xdotool scrot`)
3. Set up DISPLAY environment variable
4. Test on target desktop environment

---

*Archived by Quill 🪶*
