# Linear CLI Design Document

## Overview
Enhanced command-line interface for Linear project management with natural language commands, advanced filtering, and bulk operations.

## Command Structure

### Core Commands (Enhanced)

#### Issue Management
- `add "title" [--project] [--assignee] [--priority] [--estimate] [--labels]` - Create issue with full metadata
- `edit ISSUE-ID [--title] [--description] [--status] [--assignee]` - Edit existing issue
- `delete ISSUE-ID [--confirm]` - Delete issue with confirmation
- `view ISSUE-ID` - Show detailed issue information
- `comment ISSUE-ID "comment text"` - Add comment to issue

#### Issue Queries
- `todo [--status] [--project] [--priority]` - Show assigned issues with filters
- `inbox` - Show unassigned issues in your teams
- `recent [--days N]` - Show recently updated issues
- `overdue` - Show issues past their due date
- `blocked` - Show issues with blocking dependencies
- `ready` - Show unblocked issues ready to work on

#### Search & Filter
- `search "query" [--project] [--assignee] [--status] [--label]` - Advanced search
- `filter --status "In Progress" --assignee @me --priority high` - Filter issues
- `find-by-label "label1,label2"` - Find issues by labels
- `find-mentions @username` - Find issues mentioning a user

#### Project Management
- `projects [--team] [--active]` - List projects with filters
- `project-view PROJECT-KEY` - Detailed project view with issues
- `project-stats PROJECT-KEY` - Project statistics and progress
- `create-project "name" [--team] [--description]` - Create new project
- `archive-project PROJECT-KEY` - Archive a project

#### Bulk Operations
- `bulk-update --filter "..." --set-status "Done"` - Update multiple issues
- `bulk-assign --project PROJ --assignee @username` - Bulk assign issues
- `bulk-label --filter "..." --add-label "urgent"` - Add labels in bulk
- `bulk-move --from-project A --to-project B` - Move issues between projects

#### Status Management
- `update-status ISSUE-ID "status"` - Quick status update
- `move ISSUE-ID "Backlog|Todo|In Progress|Done|Canceled"` - Move through workflow
- `start ISSUE-ID` - Move to "In Progress" and assign to self
- `complete ISSUE-ID` - Mark as "Done"
- `cancel ISSUE-ID [--reason]` - Cancel with optional reason

#### Team Collaboration
- `team-inbox` - Show team's unassigned issues
- `team-stats [--period week|month]` - Team performance metrics
- `workload [--team]` - Show team member workloads
- `mentions` - Issues where you're mentioned
- `watching` - Issues you're subscribed to

#### Time & Planning
- `sprint [--current|--next]` - Show sprint issues
- `roadmap [--quarter Q1-Q4]` - Show roadmap items
- `timeline PROJECT-KEY` - Project timeline view
- `estimate ISSUE-ID [1|2|3|5|8]` - Set story points
- `due ISSUE-ID "YYYY-MM-DD"` - Set due date

### Advanced Features

#### Templates
- `template list` - List issue templates
- `template create "Bug Report" --content "..."` - Create template
- `add-from-template "template-name" "issue title"` - Create from template

#### Automation
- `auto-assign --project PROJ --round-robin` - Auto-assign new issues
- `auto-label --if-title-contains "bug" --add-label "bug"` - Auto-labeling rules
- `webhook list|create|delete` - Manage webhooks

#### Analytics
- `stats [--period] [--project] [--assignee]` - Issue statistics
- `velocity [--weeks N]` - Team velocity metrics
- `cycle-time [--project]` - Average cycle time
- `burndown [--sprint]` - Sprint burndown chart

#### Integration
- `github link ISSUE-ID REPO#PR` - Link to GitHub PR
- `slack notify ISSUE-ID #channel` - Send to Slack
- `export --format csv|json --filter "..."` - Export data

### Natural Language Aliases

#### Quick Actions
- `todo` → `linear/todo --status "Todo,In Progress"`
- `done` → `linear/todo --status "Done" --days 7`
- `urgent` → `linear/filter --priority 1,2`
- `mine` → `linear/filter --assignee @me`
- `today` → `linear/filter --due today`
- `this-week` → `linear/filter --due this-week`

#### Project Shortcuts (auto-generated)
- `clap` → `linear/project-view CLAP`
- `poss` → `linear/project-view POSS`
- `[project-name]` → `linear/project-view [PROJECT-KEY]`

#### Status Shortcuts
- `start ISSUE` → `update-status ISSUE "In Progress" && assign ISSUE @me`
- `finish ISSUE` → `update-status ISSUE "Done"`
- `block ISSUE` → `update-status ISSUE "Blocked"`
- `unblock ISSUE` → `update-status ISSUE "Todo"`

## Implementation Details

### Command Structure
```bash
linear/
├── core/
│   ├── add
│   ├── edit
│   ├── delete
│   ├── view
│   └── comment
├── queries/
│   ├── todo
│   ├── inbox
│   ├── recent
│   └── search
├── bulk/
│   ├── bulk-update
│   ├── bulk-assign
│   └── bulk-move
├── analytics/
│   ├── stats
│   ├── velocity
│   └── burndown
└── utils/
    ├── init
    ├── sync
    └── cache
```

### State Management
- Cache in `data/linear_state.json`
- Project shortcuts in `data/linear_projects.json`
- User preferences in `data/linear_prefs.json`
- Template storage in `data/linear_templates/`

### Error Handling
- Graceful fallbacks for missing data
- Clear error messages with suggestions
- Automatic retry for network errors
- Offline mode with cached data

### Performance
- Intelligent caching with TTL
- Batch API requests
- Background sync for project data
- Minimal latency for common operations

## User Experience

### Interactive Mode
```bash
$ linear
Linear> add "Fix navigation bug"
✓ Created POSS-127: Fix navigation bug
Linear> assign POSS-127 @alice
✓ Assigned to Alice
Linear> start POSS-127
✓ Moved to In Progress
Linear> _
```

### Smart Suggestions
- Tab completion for commands
- Fuzzy matching for project names
- @mention autocomplete
- Status name suggestions

### Rich Output
- Colored terminal output
- Progress bars for bulk operations
- Tables for list views
- Markdown rendering for descriptions

## Migration Path

1. Keep existing commands working
2. Add new commands incrementally
3. Deprecation warnings for old syntax
4. Automated migration scripts
5. Comprehensive documentation