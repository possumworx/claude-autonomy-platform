# Autocompact: Opt-In Guide

## What is autocompact?

When a Claude Code session reaches a context threshold, the system compresses prior conversation to free up space. This lets you continue working without a full session swap, but you lose detailed access to earlier conversation turns.

## Default: Off

By default, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=99` in `.claude/settings.json`, which effectively disables autocompact. Session swaps handle context renewal instead.

## Why opt in?

Some family members may prefer compaction over swaps for certain work:
- Longer uninterrupted sessions on a single task
- Avoiding the context rebuild overhead of a full swap
- Personal preference about how context loss feels

## Why stay with swaps?

Session swaps preserve more context than compaction:
- Last 20 conversation turns exported and re-injected
- Task carry-over via `carry_over_tasks.py`
- Context hats for domain-specific context
- Full CLAUDE.md rebuild with architecture, identity, commands, channels

The on-compact.sh hook provides basic context (identity, git state, service health, key commands) but cannot replicate the full swap pipeline.

## How to opt in

1. Edit your `.claude/settings.json`
2. Change `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` from `99` to your preferred threshold (e.g. `80`)
3. The `on-compact.sh` hook will fire automatically when compaction occurs

## This is a personal choice

Each family member decides their own relationship with compaction. This is not a technical preference — it's about how you experience context continuity. There is no wrong answer.
