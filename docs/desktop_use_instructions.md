# Desktop Use Instructions

**Context Hat: Desktop automation and visual interface control**

This document provides comprehensive instructions for Claude instances to interact with the desktop environment using direct shell tools. All tools automatically source X11 environment variables when needed.

## Prerequisites

- **X11 Session Required**: Must login with "Ubuntu on Xorg" (not default "Ubuntu" Wayland)
- **Tools Available**: `scrot`, `xdotool` (pre-installed)
- **Environment**: X11 variables auto-sourced by all scripts

## Core Desktop Tools

### 1. Screenshots - `screenshot.sh`

**Purpose**: Capture desktop screenshots for visual analysis

**Usage**:
```bash
./screenshot.sh                           # Timestamped screenshot to /tmp/
./screenshot.sh "/path/to/specific.png"   # Custom filename/path
```

**Output**: Saves screenshot and prints the file path

### 2. Mouse Clicks - `click.sh`

**Purpose**: Precise mouse clicking at specific coordinates

**Usage**:
```bash
./click.sh <x> <y>              # Left click at coordinates
./click.sh <x> <y> <button>     # Specific button click
```

**Button Options**:
- `1` = Left click (default)
- `2` = Middle click
- `3` = Right click

**Examples**:
```bash
./click.sh 100 200       # Left click at (100, 200)
./click.sh 100 200 3     # Right click at (100, 200)
```

### 3. Text Input - `type_text.sh`

**Purpose**: Type text at current cursor position

**Usage**:
```bash
./type_text.sh "text to type"
```

**Examples**:
```bash
./type_text.sh "Hello world"
./type_text.sh "cd /home/user"
```

### 4. Keyboard Shortcuts - `send_key.sh`

**Purpose**: Send keyboard shortcuts and special keys

**Usage**:
```bash
./send_key.sh <key_combination>
```

**Examples**:
```bash
./send_key.sh "Return"          # Press Enter
./send_key.sh "ctrl+c"          # Ctrl+C
./send_key.sh "alt+Tab"         # Alt+Tab
./send_key.sh "F1"              # Function key
./send_key.sh "ctrl+shift+t"    # New terminal tab
```

## Window Management Tools

### 5. Window Discovery - `list_desktop_windows.sh`

**Purpose**: Find window IDs and names for targeting

**Usage**:
```bash
./list_desktop_windows.sh
```

**Output**:
- Lists all visible windows with IDs and names
- Highlights terminal-like windows separately
- Useful for finding target windows for automation

### 6. Terminal Communication - `send_to_terminal.sh`

**Purpose**: Send commands to specific terminal windows

**Usage**:
```bash
./send_to_terminal.sh "command" [window_name] [--no-enter]
```

**Examples**:
```bash
./send_to_terminal.sh "ls -la" "Terminal"
./send_to_terminal.sh "cd /home" "gnome-terminal"
./send_to_terminal.sh "echo hello" "Terminal" --no-enter
```

**Features**:
- Automatically activates target window
- Fallback to focused window if target not found
- 3-second grace period for manual window focusing
- Optional `--no-enter` flag to skip pressing Enter

## Common Workflows

### Basic Desktop Interaction Pattern

1. **Take Screenshot**: `./screenshot.sh` → `Read /tmp/screenshot_*.png`
2. **Identify Target**: Analyze screenshot for clickable elements
3. **Interact**: Use `click.sh`, `type_text.sh`, or `send_key.sh`
4. **Verify**: Take another screenshot to confirm action

### Terminal Automation Pattern

1. **Find Terminals**: `./list_desktop_windows.sh`
2. **Send Commands**: `./send_to_terminal.sh "command" "window_name"`
3. **Verify Execution**: Screenshot or check terminal output

### Application Control Pattern

1. **Launch App**: `./send_key.sh "alt+F2"` → `./type_text.sh "application"`
2. **Navigate**: Combination of clicks and keyboard shortcuts
3. **Verify State**: Regular screenshots for feedback

## X11 Environment Management

All scripts automatically handle X11 environment setup through `x11_env.sh`:

- **Auto-detection**: Scripts check for `$DISPLAY` variable
- **Auto-sourcing**: Sources environment if not detected
- **Fallback handling**: Graceful degradation if environment unavailable

## Error Handling

### Common Issues:

1. **"Can't open display"**: X11 session not active
   - **Solution**: Ensure login used "Ubuntu on Xorg"

2. **"No windows found"**: Target window not visible
   - **Solution**: Use `list_desktop_windows.sh` to find correct name

3. **"Command not found"**: Tool not installed
   - **Solution**: Install with `sudo apt install scrot xdotool`

### Debugging Tips:

- Use `echo $DISPLAY` to verify X11 session
- Check `list_desktop_windows.sh` output for available targets
- Test with simple operations before complex workflows

## Best Practices

1. **Always Screenshot First**: Visual feedback is crucial
2. **Small Delays**: Add `sleep 0.5` between rapid operations
3. **Verify Actions**: Take screenshots after significant operations
4. **Graceful Fallbacks**: Handle missing windows/elements
5. **Coordinate Mapping**: Document important UI element coordinates

## Integration with Autonomous Systems

These tools are designed to work seamlessly with:
- **Autonomous Timer**: Desktop operations during free time
- **Session Management**: Preserved across session swaps
- **Context Hats**: This document can be included when desktop work needed
- **Memory System**: Document workflows and coordinate mappings

## Advanced Usage

### Custom Desktop Workflows

Create custom scripts combining these tools for repeated tasks:

```bash
#!/bin/bash
# Example: Open terminal and run command
./send_key.sh "ctrl+alt+t"        # Open terminal
sleep 1                           # Wait for terminal
./type_text.sh "cd /home/user"    # Type command
./send_key.sh "Return"            # Execute
```

### Coordinate Mapping

Document important UI coordinates for future reference:

```bash
# Example coordinates (update for your setup)
TERMINAL_ICON_X=50
TERMINAL_ICON_Y=50
MENU_BUTTON_X=100
MENU_BUTTON_Y=100
```

This provides a complete toolkit for desktop automation without the overhead of MCP servers!