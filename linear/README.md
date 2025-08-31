# Linear Natural Commands

Natural language commands for Linear project management, designed to make issue tracking invisible infrastructure.

## Commands

- `add "Issue title" [--project]` - Create new issue with optional project
- `todo` - Show issues assigned to you  
- `projects` - List your projects with descriptions
- `search-issues <query>` - Search for issues by text
- `update-status <issue-id> <status>` - Update issue status (todo, in-progress, done, etc.)
- `[project-name]` - Show issues for specific project (e.g., `clap`, `observatory`)

## Setup

First run: The system will auto-initialize and cache your user/team/project IDs.

## Design Principles

1. **Context-rich**: Every output includes descriptions to help future sessions
2. **Invisible infrastructure**: No need to remember UUIDs or Linear specifics
3. **Adaptive**: Prompts when needed, shortcuts when you know them
4. **Project-focused**: Think in projects, not issue IDs

## Implementation

- Scripts live in `linear/`
- State cached in `data/linear_state.json` 
- Natural command aliases in `config/natural_commands.sh`