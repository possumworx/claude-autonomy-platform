# Desktop Coordinate Reference
*For efficient desktop automation using direct bash tools + scrot screenshots*

## Desktop Resolution: 1920x1080

## Left Sidebar Icons (Ubuntu Dock)
- **Firefox**: [38, 73] ✅ *tested*
- **Files (File Manager)**: [26, 137] ✅ *tested*
- **App Center (App Store)**: [29, 190] ✅ *tested*
- **Krita**: [36, 323] ✅ *tested* *(pinned to dash)*
- **Terminal**: [34, 395] ✅ *tested* *(pinned to dash)*
- **Settings**: [35, 453] ✅ *tested* *(pinned to dash)*
- **Show Applications (Ubuntu logo)**: [38, 1046] ✅ *tested*

## System Bar (Top)
- **Time/Date**: [1014, 13] ✅ *tested*
- **System Menu (top-right)**: [1849, 20] ✅ *tested*

## Common Application Locations
- **App Center Close Button**: [1415, 78]
- **App Center Search**: [960, 78]

## Usage Pattern
1. Take screenshot: `scrot /tmp/screenshot.png`
2. Read screenshot: `Read /tmp/screenshot.png`
3. Use direct bash tools for input: `click.sh`, `type_text.sh`, `send_key.sh`

## ShaderToy Interface Coordinates

### Code Editor
- **Main code input area**: Center approximately at (291, 250)
- **Code editor bounds**: Left edge ~200, Right edge ~400, Top ~140, Bottom ~400
- **Safe click zone for text input**: (291, 250) - center of visible code area

### Control Buttons
- **Fullscreen button**: (388, 295) - the expand/fullscreen icon in bottom right of preview
- **Play/Pause button**: (96, 295) - the play button on bottom left
- **Submit button**: (215, 382) - the blue Submit button below the code

### Preview Area
- **Preview window**: Left edge ~85, Right edge ~400, Top ~105, Bottom ~290
- **Preview center**: (242, 197) - center of the preview/output area

### Usage Notes
- Always move mouse first, then click
- Click in center of code editor at (291, 250) before typing
- Use Ctrl+A to select all existing code before replacing
- Fullscreen button at (388, 295) for full preview experience

## Notes
- Coordinates are approximate and may vary slightly
- Always verify with screenshots before clicking
- Test coordinates before relying on them for automation