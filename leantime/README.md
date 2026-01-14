# Leantime CLI Tools

Natural command-line interface for Leantime project management, inspired by our previous Linear tools.

## Setup

1. Ensure your `claude_infrastructure_config.txt` has:
```
LEANTIME_URL=http://192.168.1.2:8081
LEANTIME_EMAIL=your-email@example.com
LEANTIME_PASSWORD=your-password
FORWARD_MEMORY_PROJECT_ID=7
LEANTIME_USER_ID=8
LEANTIME_API_KEY=your-api-key
```

2. Commands are available as `lt-*` in your PATH

## Available Commands

### Core Commands

#### `lt-add` - Create new task
```bash
# Basic usage - adds to Forward Memory project
lt-add "Task title"

# With description
lt-add "Task title" --description "More details"

# Future: with project (not yet implemented)
lt-add "Task title" --project "Project Name"
```

#### `lt-todo` - Show your assigned tasks
```bash
# Show all your tasks
lt-todo

# Show all tasks (not filtered by user)
lt-todo --all
```

#### `lt-projects` - List all projects
```bash
lt-projects
```

#### `lt-start` - Quick task creation
```bash
# Creates a new task assigned to you
lt-start "Working on something"
```

## Limitations

Due to Leantime's JSON-RPC API limitations:
- Status updates require cookie-based approaches (not yet implemented)
- Some Linear features like comments, labels, estimates need more work
- Project name resolution not yet implemented
- API returns all projects, not just user-relevant ones

## Implementation Notes

- Uses Leantime's JSON-RPC API v2
- Parameters must be wrapped in "values" object
- Falls back to cookie-based approach for complex operations
- Inspired by our thoughtful Linear CLI design

## Future Enhancements

- [ ] Project name resolution
- [ ] Status updates via cookies
- [ ] Comment support
- [ ] Better project filtering
- [ ] Bulk operations
- [ ] Natural aliases for common workflows