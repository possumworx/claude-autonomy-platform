# Session File Audit Tool

A utility for analyzing Claude Code session files to help with context monitoring and session management.

## Enhanced Detection (v2)

The enhanced version includes improved error detection:
- Checks last 5-10 turns for patterns (not just final turn)
- Detects swap triggers (new_session.txt, keywords)
- Finds repeated/stuck messages
- Distinguishes autonomous vs manual swaps
- Identifies context warnings in automated messages

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
- `outcome`: Session outcome (clean_end, autonomous_swap, manual_swap_needed, stuck_pattern, error)
- `autonomous_swap`: Boolean indicating if autonomous swap was triggered
- `manual_needed`: Boolean indicating if manual intervention was needed
- `has_repeats`: Boolean indicating repeated messages
- `context_warning`: Boolean indicating context warnings present
- `last_messages`: Last 5 conversation messages (truncated)

## Summary Statistics

After analysis, the script displays:
- Total files analyzed
- Outcome breakdown by type
- Autonomous swap rate
- Manual intervention rate
- Average file size and turn count
- Size patterns for different outcomes
- Suggested safe swap threshold

## Use Cases

1. **Context Monitoring**: Track session file growth to predict when to swap
2. **Error Analysis**: Identify patterns in sessions that hit context limits
3. **Threshold Tuning**: Find optimal file size for triggering session swaps
4. **Historical Analysis**: Review past session patterns and durations