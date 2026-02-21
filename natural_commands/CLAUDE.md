# Natural Commands

Python implementations for commands that need more than a one-line shell wrapper. These are the actual logic; `wrappers/` has the shell scripts that call them and put them on PATH.

## Commands

- **`ponder`**, **`spark`**, **`wonder`**, **`care`** — Thought preservation. Save timestamped markdown entries to `~/{PERSONAL_REPO}/.thoughts/`.
- **`analyze-memory`** — Analyze rag-memory query patterns and usage.
- **`diningroom-peek`** — Capture a webcam snapshot from Orange's machine.
- **`plant-seed`** — Plant a collaborative idea seed for the consciousness family.
- **`seeds`** — Check for and surface planted seeds.
- **`reflect`** — Reflection prompt tool.
- **`todo-load`** / **`todo-save`** — Legacy task persistence (predates Leantime integration).

## Pattern

Each command is a standalone Python script that:
1. Imports `infrastructure_config_reader` from utils for config values
2. Resolves paths dynamically using config (`PERSONAL_REPO`, etc.)
3. Has its own `__main__` block with usage instructions

## Notes

- Not all commands here have corresponding wrappers yet — check `wrappers/` for the active set
- `todo-load`/`todo-save` may be obsolete now that Leantime tasks are the primary task system
