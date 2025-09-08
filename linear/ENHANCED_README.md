# Linear CLI - Enhanced Natural Language Interface

A comprehensive command-line interface for Linear project management with natural language commands, advanced filtering, and powerful automation features.

## Quick Start

```bash
# First time setup
linear/init

# Create an issue
add "Fix navigation bug" --project CLAP --priority 1

# View your tasks
todo                    # All assigned issues
urgent                  # High priority only  
blocked                 # Blocked issues

# Quick actions
start POSS-123          # Start working (assign + in progress)
complete POSS-123       # Mark as done
view POSS-123          # See full details
```

## Core Features

### 🚀 Enhanced Issue Creation
```bash
add "Issue title" [options]
  --project NAME       # Project name or key
  --description TEXT   # Full description
  --assignee @me       # Assign to yourself
  --priority 1-4       # 1=urgent, 4=low
  --estimate 1-8       # Story points
  --labels "A,B,C"     # Comma-separated
  --due tomorrow       # Or YYYY-MM-DD
```

### 📋 Smart Task Views
```bash
todo [options]
  --status STATUS      # Filter by status
  --project PROJECT    # Filter by project
  --priority 1,2       # Filter by priority
  --include-done       # Show completed too
  --limit 50           # Number to show

# Quick shortcuts
mine                   # Your issues
urgent                 # Priority 1-2
recent --days 7        # Recent updates
inbox                  # Unassigned team issues
```

### 🔍 Powerful Search
```bash
search-issues "query"   # Search by text
view POSS-123          # View full details
comment POSS-123 "text" # Add comment
```

### ⚡ Quick Actions
```bash
start ISSUE-ID         # Assign to self + In Progress
complete ISSUE-ID      # Mark as Done
update-status ID STATUS # Custom status change
```

### 🔄 Bulk Operations
```bash
bulk-update --filter... --set...

Examples:
# Move all TODO in project to In Progress
bulk-update --filter-project CLAP --filter-status Todo \
            --set-status "In Progress"

# Assign all unassigned urgent issues to me
bulk-update --filter-assignee @none --filter-priority 1,2 \
            --set-assignee @me

# Preview changes without applying
bulk-update --filter-status Blocked --set-priority 4 --dry-run
```

## Natural Language Aliases

All commands are available as natural shell commands:

```bash
# Core commands
add          # Create issue
todo         # Show tasks
view         # Issue details
comment      # Add comment

# Quick actions  
start        # Start working
complete     # Mark done
inbox        # Team inbox
recent       # Recent updates

# Shortcuts
mine         # Your issues
urgent       # High priority
blocked      # Blocked issues
done         # Recently completed

# Project shortcuts (auto-generated)
clap         # Show ClAP issues
poss         # Show POSS issues
```

## Advanced Usage

### Filtering & Queries
```bash
# Complex todo filters
todo --project CLAP --status "In Progress" --priority 1,2

# Recent updates with options
recent --days 30 --all    # All team updates in 30 days

# Search with context
search-issues "memory leak in production"
```

### Date Shortcuts
```bash
add "Task" --due today
add "Task" --due tomorrow  
add "Task" --due "next week"
add "Task" --due 2024-12-25
```

### Issue ID Shortcuts
```bash
# Use full ID or just number
view POSS-123
view 123        # Uses recent project prefix
```

### Assignee Shortcuts
```bash
--assignee @me    # Assign to yourself
--assignee @none  # Leave unassigned
```

## Command Reference

Run `linear-help` for full command documentation.

### Setup Commands
- `linear/init` - Initial authentication and setup
- `linear/sync_projects` - Refresh project list
- `linear/help` - Show comprehensive help

### Issue Management  
- `add` - Create issue with full metadata
- `view` - Show detailed issue info
- `comment` - Add comment to issue
- `update-status` - Change issue status

### Task Views
- `todo` - Your assigned issues
- `inbox` - Unassigned team issues  
- `recent` - Recently updated
- `search-issues` - Search by text

### Quick Actions
- `start` - Begin work on issue
- `complete` - Mark as done

### Bulk Operations
- `bulk-update` - Update multiple issues

## Tips & Tricks

1. **Issue IDs**: Use full format (POSS-123) or just number (123)
2. **Filters**: Combine multiple filters for precise queries
3. **Dry Run**: Use `--dry-run` with bulk operations to preview
4. **Help**: Add `--help` to any command for usage info

## Implementation Details

- Commands use Claude's MCP Linear integration
- State cached in `data/linear_state.json`
- Project shortcuts in natural commands
- Common functions in `lib/linear_common.sh`

## Troubleshooting

### "Linear not initialized"
Run `linear/init` to set up authentication

### "Not in Claude Code session"  
Start Claude Code with `Claude` command first

### Project not found
Run `linear/sync_projects` to refresh project list