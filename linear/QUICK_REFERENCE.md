# Linear Quick Reference Card

## Essential Commands

```bash
# Your tasks
todo                    # Show issues assigned to you

# Create issues  
add "Issue title"       # Create in default location
add "Title" -p CLAP     # Create in specific project

# View projects
projects                # List all projects
clap                    # View ClAP project issues
laser                   # View Laser project issues

# Search & update
search-issues "keyword" # Find issues
update-status POSS-123 "In Progress"  # Change status
```

## Common Statuses
- `Backlog` - Not started
- `Todo` - Ready to work on
- `In Progress` - Currently working
- `Done` - Completed
- `Canceled` - Won't do

## Pro Tips
1. Run `linear/init` first time only
2. Use project shortcuts (e.g., `clap`) for quick views
3. Add `-p PROJECT` to target specific projects
4. Sync projects with `linear/sync_projects` if needed

## Example Workflow
```bash
# Morning check
todo                    # What's assigned to me?
clap                    # Check project status

# Start work
update-status POSS-123 "In Progress"

# Create follow-up
add "Fix related bug" -p CLAP

# Complete work  
update-status POSS-123 "Done"
```