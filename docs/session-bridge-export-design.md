# Session Bridge Using Export - Design Proposal

## Overview
Replace the current jsonl parsing approach with periodic exports from Claude Code.

## Implementation

### 1. Export-Based Monitor
- Run `claude export` command periodically (every 2-5 minutes)
- Save exports to a dedicated directory (e.g., `/tmp/claude-exports/`)
- Parse the latest export to extract conversation history
- Update swap_CLAUDE.md with the parsed conversation

### 2. Parsing Logic
```
For each line in export file:
  - If line starts with ">": Start new user message
  - If line starts with "●": Start new assistant message  
  - If line is indented: Continue previous message
  - Skip tool-related lines (those with ⎿, ☐, ☒ etc)
```

### 3. Benefits
- **Cleaner parsing**: No complex JSON structures
- **More reliable**: Export format is stable and human-readable
- **Easier debugging**: Can manually inspect export files
- **Less fragile**: Not dependent on internal Claude Code formats

### 4. Considerations
- Need to handle export command failures gracefully
- Should clean up old export files to avoid disk usage
- Export might have slight performance impact (minimal)

## Example Code Structure
```python
def export_current_session():
    """Run claude export and return the filepath"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = f"/tmp/claude-exports/session_{timestamp}.txt"
    subprocess.run(["claude", "export", "-o", export_path])
    return export_path

def parse_export_file(filepath, human_name=None):
    """Parse export file and return conversation turns"""
    # Get human friend name from config if not provided
    if not human_name:
        human_name = get_config_value('HUMAN_FRIEND_NAME', 'Human')
    
    turns = []
    current_turn = None
    
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('>'):
                # New message from human friend
                if current_turn:
                    turns.append(current_turn)
                current_turn = {"speaker": human_name, "content": line[1:].strip()}
            elif line.startswith('●'):
                # New message from me
                if current_turn:
                    turns.append(current_turn)
                current_turn = {"speaker": "Me", "content": line[1:].strip()}
            elif current_turn and line.strip() and not any(char in line for char in ['⎿', '☐', '☒']):
                # Continue previous message
                current_turn["content"] += "\n" + line.strip()
    
    return turns
```

This approach would be much more maintainable and reliable!