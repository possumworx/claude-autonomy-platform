# Session File Audit Tool

A utility for analyzing Claude Code session files to help with context monitoring and session management.

## Usage

```bash
python3 session_audit.py [session_directory] [-o output.csv] [--limit N]
```

## Parameters

- `session_directory`: Directory containing JSONL session files (default: `~/.config/Claude/tmp/sessions`)
- `-o, --output`: Output CSV filename (default: `session_audit.csv`)
- `--limit`: Limit number of files to analyze (useful for testing)

## Example

```bash
# Analyze session files in Claude project directory
python3 session_audit.py ~/.config/Claude/projects/-home-delta-claude-autonomy-platform

# Analyze only last 20 sessions
python3 session_audit.py ~/.config/Claude/projects/-home-delta-claude-autonomy-platform --limit 20 -o recent_sessions.csv
```

## Output

The script generates a CSV file with:
- `filename`: Session file name
- `file_size_bytes`: File size in bytes
- `file_size_mb`: File size in MB
- `turn_count`: Number of conversation turns
- `last_modified`: Timestamp of last modification
- `ended_with_error`: Boolean indicating if session ended with error
- `last_messages`: Last 5 conversation messages (truncated)

## Summary Statistics

After analysis, the script displays:
- Total files analyzed
- Files ending with errors
- Average file size and turn count
- Size thresholds for errors vs successful sessions
- Suggested safe swap threshold

## Use Cases

1. **Context Monitoring**: Track session file growth to predict when to swap
2. **Error Analysis**: Identify patterns in sessions that hit context limits
3. **Threshold Tuning**: Find optimal file size for triggering session swaps
4. **Historical Analysis**: Review past session patterns and durations