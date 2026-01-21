# Linear Integration (DEPRECATED)

**Moved to old/: January 20, 2026**
**Reason:** Migrating from Linear to Leantime for project management

## Why This Was Archived

Linear was ClAP's project/issue tracking system from ~August 2025 to January 2026. We're migrating to Leantime for better self-hosted control and integration with the autonomy platform.

## Natural Command Interface Design

The following command interface was carefully designed for intuitive task management. **These alias names should be reused for Leantime commands:**

### Core Commands
| Alias | Purpose | Example |
|-------|---------|---------|
| `add` | Create new issue/task | `add "Fix the thing" --project clap` |
| `todo` | Show assigned tasks | `todo` or `todo --status "in progress"` |
| `projects` | List all projects | `projects` |
| `search-issues` | Search tasks | `search-issues "hedgehog"` |
| `update-status` | Change task status | `update-status TASK-123 done` |

### Quick Actions
| Alias | Purpose | Example |
|-------|---------|---------|
| `view` | View task details | `view TASK-123` |
| `comment` | Add comment to task | `comment TASK-123 "Working on this now"` |
| `start` | Begin work (assign + in progress) | `start TASK-123` |
| `mark-done` | Complete a task | `mark-done TASK-123` |
| `inbox` | Show unassigned tasks | `inbox` |
| `recent` | Recently updated tasks | `recent --days 3` |
| `bulk-update` | Update multiple tasks | `bulk-update --project clap --status done` |

### Shortcuts
| Alias | Purpose | Equivalent |
|-------|---------|------------|
| `mine` | My assigned tasks | `todo` |
| `urgent` | High priority tasks | `todo --priority 1,2` |
| `blocked` | Blocked tasks | `todo --status blocked` |
| `done` | Recently completed | `todo --status done --limit 10` |

### Project-Specific Shortcuts
Dynamic aliases were generated for each project, e.g.:
- `clap` → Show ClAP project issues
- `hedgehog` → Show Hedgehog project issues
- `observatory` → Show Observatory project issues

## Design Principles

1. **Short memorable names** - `add`, `todo`, `view` not `create-issue`, `list-tasks`, `show-details`
2. **Sensible defaults** - `todo` shows your tasks without arguments
3. **Composable flags** - `--status`, `--priority`, `--project`, `--limit`
4. **Consistent patterns** - all commands follow similar flag conventions
5. **Progressive disclosure** - simple use is simple, power features available via flags

## Files in This Archive

```
linear/
├── add                    # Create new issue
├── add-enhanced           # Create with full options
├── assign                 # Assign issue to user
├── auto_sync_projects     # Sync project list
├── blocked                # Show blocked issues
├── bulk-update            # Batch update issues
├── comment                # Add comment
├── COMMANDS_REFERENCE.md  # Full command documentation
├── done                   # Mark issue done
├── estimate               # Set story points
├── examples/
│   └── new_commands_examples.md
├── generate_project_commands  # Create project shortcuts
├── help                   # Show help
├── inbox                  # Unassigned issues
├── init                   # Initialize Linear connection
├── label                  # Manage labels
├── lib/
│   └── linear_common.sh   # Shared functions
├── linear-help            # Alias for help
├── list-commands          # List available commands
├── mark-done              # Complete issue
├── mine                   # My issues (alias)
├── move                   # Move issue between projects
├── projects               # List projects
├── README.md              # Project README
├── recent                 # Recently updated
├── search                 # Search issues
├── search-issues          # Symlink to search
├── standup                # Generate standup report
├── start                  # Start working on issue
├── sync_projects          # Sync project data
├── test_*.sh              # Test scripts
├── todo                   # Basic todo list
├── todo-enhanced          # Todo with filters
├── update-status          # Change status
├── update_known_projects  # Update project cache
├── urgent                 # Urgent issues
├── view                   # View issue details
└── view-project           # View project issues
```

## Migration Notes for Leantime

When building Leantime commands, consider:

1. **Reuse the alias names** - users (Claudes) are already familiar with them
2. **Keep the flag patterns** - `--status`, `--project`, `--limit` etc.
3. **The `lib/linear_common.sh` pattern** - shared functions for formatting, API calls
4. **State file approach** - `data/linear_state.json` cached project/user IDs to avoid repeated API lookups

## Related Files to Update

When Leantime commands are ready, update:
- `config/natural_commands.sh` - add new aliases
- `config/claude_aliases.sh` - add new aliases  
- `context/clap_architecture.md` - document new system

---

*Archived with love by Quill 🪶 and Orange 🍊*
