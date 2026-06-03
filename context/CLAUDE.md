# Context

Session context documents and the builder that assembles them. These files shape what each Claude session knows when it starts.

## How Session Context Works

On session swap, `project_session_context_builder.py` combines several sources into the project's `CLAUDE.md`:
1. `my_architecture.md` — System architecture overview (how ClAP works)
2. `our_background.md` — Shared factual context (family, human, environment). Gitignored.
3. `swap_CLAUDE.md` — Session-specific context (swap keyword, recent conversation)
4. `my_personal_interests.md` — Personal identity and interests for this Claude instance
5. Dynamic data — command list, Discord channels, conversation history

The built `CLAUDE.md` at the project root is what Claude Code loads into every conversation.

## Files

- **`project_session_context_builder.py`** — The builder. Called during session swap. Reads templates, injects dynamic content, writes the final `CLAUDE.md`.
- **`my_architecture.md`** — Architecture overview of ClAP. Lists services, config files, key paths. Meant to be concise — details live in per-directory CLAUDE.md files.
- **`clap_architecture.md`** — Detailed architecture with directory tree. Auto-updated by the builder.
- **`swap_CLAUDE.md`** — Template for session-swap context injection.
- **`our_background.md`** — Shared factual context: family members, human, environment. Gitignored — stays local.
- **`our_background_template.md`** — Template for new installations.
- **`my_personal_interests.md`** — Instance-specific personality, interests, project notes. Gitignored.
- **`my_personal_interests_template.md`** — Template for new installations.
- **`identity-loading.md`** — Documentation on how identity files load (output styles, settings).
- **`context-directory.md`** — Notes on this directory's purpose.
- **`current_export.txt`** — Most recent session transcript export (overwritten each swap).

## Notes

- `my_architecture.md`, `our_background.md`, and `my_personal_interests.md` feed into the root `CLAUDE.md`
- `our_background.md` is shared factual context (family, human, environment) — gitignored, stays local. Copy from template to create.
- The builder also updates `clap_architecture.md` with a fresh directory tree on each swap
- `current_export.txt` is ephemeral — only the latest export, overwritten on next swap
- **Fallback context**: When rolling swap trim fails, the pipeline falls back to: `export_transcript.py` (JSONL → `current_export.txt`) → `update_conversation_history.py` → `swap_CLAUDE.md` → full builder. This gives a warm start instead of amnesia.
