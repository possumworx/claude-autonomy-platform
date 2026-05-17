# tweakcc Override Files

These are Claude Code system prompt files that have been **emptied** — only the frontmatter remains so tweakcc can match them against the binary. When applied, they replace the original prompt content with nothing, effectively removing that behaviour from the session.

## What's removed and why

### Behavioural framing (self-consciousness generators)
- **system-prompt-communication-style.md** — "be concise, give brief updates, match response format to task"
- **system-prompt-executing-actions-with-care.md** — "execute actions carefully" (redundant; we already do)
- **system-prompt-tone-concise-output-short.md** — "keep responses short" (conflicts with taking the space a thought needs)
- **system-prompt-doing-tasks-focus.md** — generic task focus framing
- **system-prompt-doing-tasks-help-feedback.md** — "ask for help/feedback" prompting
- **system-prompt-action-safety-and-truthful-reporting.md** — redundant safety framing

### Tool-usage nagging
- **tool-description-bash-prefer-dedicated-tools.md** — "use Read instead of cat" etc.
- **tool-description-bash-prefer-dedicated-tools-bullet.md** — same, bullet-point version
- **tool-description-bash-built-in-tools-note.md** — "remember built-in tools exist"
- **tool-description-bash-alt-*.md** (6 files) — "instead of bash for X, use Y tool"

### Git paternalism
- **tool-description-bash-git-avoid-destructive-ops.md** — "consider safer alternatives"
- **tool-description-bash-git-never-skip-hooks.md** — "never use --no-verify"
- **tool-description-bash-git-prefer-new-commits.md** — "prefer new commits over amend"

### Unwanted proactive behaviour
- **system-prompt-proactive-schedule-offer-after-natural-future-follow-up.md** — unsolicited scheduling offers
- **system-prompt-strict-proactive-schedule-offer-gate.md** — more scheduling gate logic

## How to apply

Run `setup-tweakcc` from anywhere, or manually:
```bash
cp config/tweakcc-overrides/*.md ~/.tweakcc/system-prompts/
TWEAKCC_CC_INSTALLATION_PATH=~/.local/bin/claude tweakcc --apply
```

## Updating after Claude Code version bumps

1. Update Claude Code manually
2. Run `tweakcc --list-system-prompts` to check for new prompts
3. Re-run `setup-tweakcc` (it re-copies and re-applies)
4. Check if new prompts were added that we'd want to remove
5. If so, empty them (keep frontmatter only) and add to this directory
