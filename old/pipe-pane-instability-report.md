# Pipe-Pane Instability Report
Date: 2025-08-19

## Summary
The tmux pipe-pane feature used for session monitoring has proven unstable across multiple Claude instances, causing crashes and system instability.

## Affected Systems
- Sonnet's system: "really, really unstable" after update
- Delta's system: Mysterious crash on 2025-08-18
- Potential issues with other instances

## Root Cause
Using `tmux pipe-pane` to continuously write session output to `data/current_session.log` creates:
- File handle conflicts
- Buffering issues
- Race conditions with other monitoring tools
- System resource contention

## Original Purpose
The pipe-pane was implemented to support:
- tellclaude emergency messaging system (human-to-claude communication at 100% context)
- Real-time session monitoring

## Decision
Remove pipe-pane completely in favor of stability. Context monitoring should use the existing jsonl session file measurement, which has proven reliable.

## Action Items
1. Remove pipe-pane from all configuration files
2. Disable any active pipe-pane sessions
3. Verify context monitoring uses jsonl files
4. Clean up related code and documentation