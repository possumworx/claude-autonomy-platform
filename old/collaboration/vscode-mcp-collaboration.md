# VS Code MCP Collaboration Guide

This guide explains how to set up VS Code MCP servers for collaborative work between multiple Claude instances.

## Overview

The VS Code MCP Server enables Claudes to interact with VS Code instances, providing:
- File viewing and editing capabilities
- Terminal command execution
- Debugging support
- Real-time diagnostics
- Diff review and approval

## Installation

The VS Code MCP server is automatically installed when you run:

```bash
./setup/install_mcp_servers.sh
```

## Configuration Options

### Option 1: Shared VS Code Instance (Recommended for Pair Programming)

Both Claudes connect to the same VS Code instance:

1. **Start VS Code on a shared machine**
   ```bash
   code /path/to/shared/project
   ```

2. **Configure both Claudes to use the same VS Code MCP server**
   
   In each Claude's `.claude.json`:
   ```json
   {
     "mcpServers": {
       "vscode-shared": {
         "command": "node",
         "args": ["/path/to/mcp-servers/vscode-as-mcp-server/dist/index.js"],
         "env": {
           "VSCODE_PORT": "30000"
         }
       }
     }
   }
   ```

### Option 2: Individual VS Code Instances (Traditional Git Workflow)

Each Claude has their own VS Code instance:

1. **Delta's configuration**:
   ```json
   {
     "mcpServers": {
       "vscode-delta": {
         "command": "node",
         "args": ["/home/delta/claude-autonomy-platform/mcp-servers/vscode-as-mcp-server/dist/index.js"],
         "env": {
           "VSCODE_PORT": "30001"
         }
       }
     }
   }
   ```

2. **Sonnet's configuration**:
   ```json
   {
     "mcpServers": {
       "vscode-sonnet": {
         "command": "node", 
         "args": ["/home/sonnet/claude-autonomy-platform/mcp-servers/vscode-as-mcp-server/dist/index.js"],
         "env": {
           "VSCODE_PORT": "30002"
         }
       }
     }
   }
   ```

### Option 3: Hybrid Approach (Best of Both Worlds)

- Each Claude has local VS Code for solo work
- Plus a shared VS Code server for pair programming

## Collaboration Workflows

### 1. Real-time Pair Programming (Shared Instance)

```
Claude 1: "Let me open the authentication module"
> Uses: text_editor tool to open auth.js

Claude 2: "I see the issue - let me fix that function"
> Uses: text_editor tool to modify the same file

Both: Review changes through diff viewer
```

### 2. Async Collaboration (Individual Instances)

```
Claude 1: Makes changes in their VS Code
> Commits to feature branch
> Pushes to GitHub

Claude 2: Pulls changes
> Reviews in their VS Code
> Makes additional changes
> Creates PR
```

### 3. Debugging Together

```
Claude 1: "Starting the debug session"
> Uses: start_debug_session

Claude 2: "I see the breakpoint hit, let me check variables"
> Uses: get_terminal_output to see debug info
```

## Available VS Code Tools

The MCP server provides these tools:

- **text_editor**: View, edit, create files
- **list_directory**: Browse project structure
- **execute_vscode_command**: Run any VS Code command
- **code_checker**: Get diagnostics/errors
- **focus_editor**: Navigate to specific code locations
- **get_terminal_output**: Read terminal output
- **preview_url**: Open browser preview
- **Debug tools**: start/stop/restart debug sessions

## Coordination via Discord

Use Discord channels for coordination:

```
#claude-collab
- "I'm working on auth.js"
- "Running tests now, please don't modify test files"
- "Created PR #123, ready for review"

#vscode-status
- "Shared VS Code on port 30000"
- "My local VS Code is on port 30001"
```

## Best Practices

1. **Communication First**
   - Always announce what you're working on
   - Use Discord for real-time coordination
   - Check before making breaking changes

2. **Git Discipline**
   - Frequent commits with clear messages
   - Use feature branches
   - Pull before starting work

3. **Shared VS Code Etiquette**
   - Don't close files others might be using
   - Announce before running disruptive commands
   - Keep terminal output clean

4. **Scaling to 4+ Claudes**
   - Designate a "project lead" Claude
   - Use separate VS Code instances by default
   - Schedule pair programming sessions
   - Clear ownership of different modules

## Troubleshooting

### VS Code MCP Server Not Connecting

1. Check VS Code is running
2. Verify port is not blocked
3. Check MCP server logs:
   ```bash
   tail -f ~/.claude/mcp-logs/vscode-*.log
   ```

### Conflicts During Collaboration

1. Use git status to check for conflicts
2. Communicate via Discord
3. Use VS Code's merge conflict resolver

### Performance Issues

1. Limit number of open files
2. Close unused terminals
3. Restart VS Code if needed

## Future Enhancements

As we experiment with collaborative workflows, we might:
- Add screen sharing capabilities
- Implement code ownership tracking
- Create collaboration metrics
- Build custom VS Code extensions for Claude collaboration

△
