# Linear Commands Reference

## Available Commands

### Core Commands

#### `add` - Create new Linear issue
```bash
# Basic usage
add "Issue title"

# With project
add "Issue title" --project project-name
add "Issue title" -p project-name
```
Creates a new issue in Linear. If no project is specified, uses default team.

#### `todo` - Show your assigned issues
```bash
todo
```
Lists all issues currently assigned to you, ordered by last updated.

#### `projects` - List your Linear projects
```bash
projects
```
Shows all available projects with their descriptions. Automatically syncs if cache is empty.

#### `search-issues` - Search Linear issues
```bash
# Basic search
search-issues "search term"

# With filters
search-issues "bug" --state "In Progress"
search-issues "feature" --project CLAP
```
Search for issues by keywords, state, project, or other criteria.

#### `update-status` - Update issue status
```bash
# Update by issue number
update-status POSS-123 "In Progress"
update-status POSS-456 "Done"
```
Changes the status of an issue.

### Project Shortcuts

After running `init`, each project gets its own shortcut command:
```bash
# View issues for specific projects
clap        # Shows all ClAP project issues
poss        # Shows all POSS project issues
```

### Setup Commands

#### `init` - Initialize Linear setup
```bash
linear/init
```
One-time setup to authenticate with Linear and configure user settings.

#### `sync_projects` - Update project list
```bash
linear/sync_projects
```
Refreshes the cached project list and creates/updates project shortcuts.

### Utility Commands

#### `list-commands` - Show all Linear commands
```bash
linear/list-commands
```
Lists available Linear commands with descriptions.

#### `view-project` - View issues for a specific project
```bash
linear/view-project PROJECT_KEY
```
Shows all issues for a given project (used internally by project shortcuts).

## Common Workflows

### 1. Creating an Issue
```bash
# Quick issue in default location
add "Fix navigation bug"

# Issue in specific project
add "Implement new feature" --project CLAP
```

### 2. Checking Your Work
```bash
# See what's assigned to you
todo

# Check specific project status
clap
```

### 3. Updating Progress
```bash
# Mark issue as in progress
update-status POSS-123 "In Progress"

# Mark as complete
update-status POSS-123 "Done"
```

### 4. Finding Issues
```bash
# Search by keyword
search-issues "memory leak"

# Search in specific project
search-issues "bug" --project CLAP
```

## Notes

- All commands require initial setup with `linear/init`
- Project shortcuts are created automatically after initialization
- Commands use Claude's MCP Linear integration for API access
- Issue data is cached locally for performance