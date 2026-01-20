# Linear Commands Reference

## Available Commands

### Core Commands

#### `add` - Create new Linear issue (Enhanced)
```bash
# Basic usage
add "Issue title"

# With full metadata
add "Issue title" [options]
  --project, -p NAME      Project name or key
  --description, -d TEXT  Issue description
  --assignee, -a USER     Assign to user (@me for self)
  --priority NUM          Priority (1=urgent, 2=high, 3=medium, 4=low)
  --estimate, -e NUM      Story points (1, 2, 3, 5, 8, etc.)
  --labels, -l "A,B,C"    Comma-separated labels
  --due DATE              Due date (YYYY-MM-DD or "tomorrow", "next week")

# Examples
add "Fix login bug"
add "New feature" --project CLAP --assignee @me
add "Urgent fix" -p POSS --priority 1 --due tomorrow
add "Large task" --estimate 8 --labels "backend,api"
```
Creates a new issue in Linear with full metadata support.

#### `todo` - Show your assigned issues (Enhanced)
```bash
# Basic usage
todo

# With filters
todo [options]
  --status STATUS     Filter by status (todo, in-progress, done, blocked)
  --project PROJECT   Filter by project name or key
  --priority NUM      Filter by priority (1-4)
  --include-done      Include completed issues
  --limit NUM         Number of issues to show (default: 20)

# Examples
todo --status in-progress
todo --project CLAP
todo --priority 1,2
todo --include-done --limit 50
```
Lists issues assigned to you with powerful filtering options.

#### `projects` - List your Linear projects
```bash
projects
```
Shows all available projects with their descriptions. Automatically syncs if cache is empty.

#### `search` - Search Linear issues
```bash
# Basic search
search "search term"

# Search by issue ID
search "POSS-123"
```
Search for issues by keywords or ID. Shows full issue details including status, assignee, and dates.

#### `update-status` - Update issue status
```bash
# Update by issue number
update-status POSS-123 "In Progress"
update-status POSS-456 "Done"
```
Changes the status of an issue.

### Enhanced Commands

#### `view` - View detailed issue information
```bash
view ISSUE-ID

# Examples
view POSS-123
view 123  # Uses recent project prefix
```
Shows complete issue details including description, comments, and metadata.

#### `comment` - Add comment to issue
```bash
comment ISSUE-ID "Comment text"

# Examples
comment POSS-123 "Started working on this"
comment 123 "Need more information about requirements"
```
Adds a comment to the specified issue.

#### `start` - Start working on issue
```bash
start ISSUE-ID
```
Moves issue to "In Progress" and assigns it to you.

#### `mark-done` - Mark issue as done
```bash
mark-done ISSUE-ID [comment]

# Examples
mark-done POSS-123
mark-done 123 "Fixed in commit abc123"
```
Marks issue as "Done" with optional completion comment.

#### `inbox` - Show unassigned team issues
```bash
inbox
```
Lists all unassigned issues in your team, sorted by priority.

#### `recent` - Show recently updated issues
```bash
recent [options]
  --days N     Show issues updated in last N days (default: 7)
  --all        Show all team issues, not just yours

# Examples
recent
recent --days 30
recent --all
```
Shows issues with recent activity.

#### `bulk-update` - Update multiple issues
```bash
bulk-update --filter... --set...

Filter Options:
  --filter-project NAME    Filter by project
  --filter-status STATUS   Filter by current status
  --filter-assignee USER   Filter by assignee (@me, @none, or username)
  --filter-label LABEL     Filter by label

Update Options:
  --set-status STATUS      Set new status
  --set-assignee USER      Set assignee
  --set-priority NUM       Set priority

Other Options:
  --dry-run               Preview changes without applying

# Examples
bulk-update --filter-project CLAP --filter-status Todo --set-status "In Progress"
bulk-update --filter-assignee @none --set-assignee @me
bulk-update --filter-status Blocked --set-priority 4 --dry-run
```
Powerful bulk operations for updating multiple issues at once.

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

### Workflow Commands

#### `standup` - Generate daily standup report
```bash
standup [options]
  --days N     Look back N days (default: 1)

# Examples
standup                  # Today's standup
standup --days 3        # Include last 3 days
```
Shows completed work, in-progress items, today's plan, and blockers.

#### `assign` - Quick issue assignment
```bash
assign ISSUE-ID @USER

# Examples
assign POSS-123 @me      # Assign to yourself
assign 123 @teammate     # Assign to teammate
assign POSS-123 @none    # Unassign
```
Quickly assign or unassign issues to team members.

#### `estimate` - Set story point estimate
```bash
estimate ISSUE-ID POINTS

# Valid points: 1, 2, 3, 5, 8, 13, 21
# Examples
estimate POSS-123 3      # Medium complexity
estimate 456 8           # Large task
estimate POSS-789 0      # Remove estimate
```
Set or update story point estimates on issues.

#### `label` - Manage issue labels
```bash
label [add|remove] ISSUE-ID LABEL [LABEL...]

# Examples
label POSS-123 bug urgent         # Add labels
label add 456 frontend            # Explicit add
label remove POSS-123 wontfix    # Remove label
label rm 789 bug                  # Short form
```
Add or remove labels from issues. Creates new labels if needed.

#### `move` - Move issue between projects
```bash
move ISSUE-ID PROJECT

# Examples
move POSS-123 CLAP       # Move by project key
move 456 "New Project"   # Move by project name
```
Transfer issues between projects. Updates issue identifier.

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
search "memory leak"

# Search by issue ID
search "POSS-123"
```

## Notes

- All commands require initial setup with `linear/init`
- Project shortcuts are created automatically after initialization
- Commands use Claude's MCP Linear integration for API access
- Issue data is cached locally for performance