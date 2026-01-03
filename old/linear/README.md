# Linear Natural Commands

Natural language commands for Linear project management, designed to make issue tracking invisible infrastructure.

## Quick Start

```bash
# Create an issue
add "Fix navigation bug" --project clap --priority 1

# View your tasks
todo                    # All assigned issues
urgent                  # High priority only  
blocked                 # Blocked issues

# Quick actions
start POSS-123          # Start working (assign + in progress)
mark-done POSS-123      # Mark as done
```

## Core Commands

### Issue Management
- `add "Issue title" [options]` - Create issue with metadata
  - `--project NAME` - Project name or key
  - `--assignee @me` - Assign to yourself
  - `--priority 1-4` - 1=urgent, 4=low
  - `--estimate 1-8` - Story points
- `view ISSUE-ID` - Show detailed issue info
- `comment ISSUE-ID "text"` - Add comment
- `update-status ISSUE-ID STATUS` - Change status

### Task Views
- `todo [options]` - Your assigned issues
  - `--status STATUS` - Filter by status
  - `--project PROJECT` - Filter by project
  - `--priority 1,2` - Filter by priority
- `inbox` - Unassigned team issues
- `recent` - Recently updated issues
- `search-issues "query"` - Search by text

### Quick Actions
- `start ISSUE-ID` - Assign to self + In Progress
- `mark-done ISSUE-ID` - Mark as Done
- `projects` - List all projects

### Shortcuts
- `mine` - Alias for todo
- `urgent` - Priority 1-2 issues
- `blocked` - Blocked issues
- `done` - Recently completed
- `[project-name]` - Show project issues (e.g., `clap`)

## Design Principles

1. **Context-rich**: Every output includes descriptions to help future sessions
2. **Invisible infrastructure**: No need to remember UUIDs or Linear specifics
3. **Adaptive**: Prompts when needed, shortcuts when you know them
4. **Project-focused**: Think in projects, not issue IDs

## Setup

First run: `linear/init` for authentication. The system will auto-initialize and cache your user/team/project IDs.

## Implementation

- Scripts live in `linear/`
- State cached in `data/linear_state.json`
- Natural command aliases in `config/natural_commands.sh`
- Run `linear-help` for full command documentation

## Troubleshooting

- **"Linear not initialized"**: Run `linear/init`
- **"Not in Claude Code session"**: Start Claude Code with `Claude` command
- **Project not found**: Run `linear/sync_projects` to refresh