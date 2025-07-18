# Tmux-to-Claude MCP Server Architecture
**⚠️ THEORETICAL! FUTURE ROADMAP! ⚠️**

*This is design work for future implementation, not current working code*

*Designed during autonomous time - July 16, 2025 10:27*

## Vision
Universal communication bridge that enables the same autonomous infrastructure to work across Claude Code, Claude Desktop, and future API clients. Core part of ClAP that makes autonomous systems truly portable.

## Core Concept
```
autonomy_timer.py → tmux session "autonomy-claude" → MCP server → Claude environment
```

## Technical Architecture

### Input Monitoring
```python
# Monitor tmux session for new messages
tmux_command = "tmux capture-pane -t autonomy-claude -p"
new_content = subprocess.run(tmux_command, shell=True, capture_output=True, text=True)
```

### Message Classification
```python
def classify_message(message):
    if message.startswith("ADMIN:"):
        return "admin_command"
    elif message.startswith("SWAP_SESSION:"):
        return "session_swap"
    elif message.startswith("NOTIFY:"):
        return "notification"
    else:
        return "conversation"
```

### Reserved Commands
- `ADMIN:health_check` - Run system diagnostics
- `ADMIN:restart_service:service_name` - Restart specific service
- `SWAP_SESSION:CREATIVE` - Trigger session swap to creative context
- `SWAP_SESSION:BUSINESS` - Trigger session swap to business context
- `NOTIFY:urgent` - Priority notification handling
- `NOTIFY:hedgehog` - Hedgehog care notification

### MCP Server Structure
```python
class TmuxClaudeMCP:
    def __init__(self):
        self.last_position = 0
        self.tmux_session = "autonomy-claude"
        
    async def monitor_tmux(self):
        # Continuous monitoring loop
        while True:
            new_messages = self.get_new_messages()
            for message in new_messages:
                await self.process_message(message)
            await asyncio.sleep(1)
    
    def get_new_messages(self):
        # Get new content since last check
        current_content = self.capture_tmux()
        new_content = self.extract_new_content(current_content)
        return new_content
    
    async def process_message(self, message):
        msg_type = self.classify_message(message)
        
        if msg_type == "conversation":
            await self.send_to_claude(message)
        elif msg_type == "admin_command":
            await self.execute_admin_command(message)
        elif msg_type == "session_swap":
            await self.trigger_session_swap(message)
        elif msg_type == "notification":
            await self.handle_notification(message)
```

### Claude Environment Integration

**Claude Code Integration**:
```python
async def send_to_claude(self, message):
    # Inject message into current Claude Code session
    # This would require Claude Code API integration
    pass
```

**Claude Desktop Integration**:
```python
async def send_to_claude(self, message):
    # Send message to Claude Desktop as conversation turn
    # This would require Claude Desktop API integration
    pass
```

**Future API Client Integration**:
```python
async def send_to_claude(self, message):
    # Send message to custom API client
    # This would use standard Claude API endpoints
    pass
```

## MCP Server Configuration

### In ~/.claude.json
```json
{
  "mcpServers": {
    "tmux-claude-bridge": {
      "command": "python",
      "args": ["/path/to/AUTONOMY/tmux_claude_mcp_server.py"],
      "env": {
        "TMUX_SESSION": "autonomy-claude"
      }
    }
  }
}
```

### Tool Definitions
```python
@server.list_tools()
async def list_tools():
    return [
        {
            "name": "send_to_tmux",
            "description": "Send message to tmux session for autonomous processing",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "priority": {"type": "string", "enum": ["normal", "urgent"]}
                }
            }
        }
    ]
```

## Advantages of This Architecture

1. **Universal Core**: Same `autonomy_timer.py` works for all Claude instances
2. **Environment Agnostic**: MCP server handles environment-specific integration
3. **Modular**: Can be included in ClAP or not, depending on needs
4. **Extensible**: Easy to add new command types or integrations
5. **Secure**: Admin commands can be restricted/filtered

## Security Considerations

- Message filtering to prevent arbitrary command execution
- Authentication for admin commands
- Rate limiting for message processing
- Sanitization of input before execution

## Implementation Priority

1. **Basic message monitoring** - Get tmux capture working
2. **Message classification** - Parse conversation vs commands
3. **Claude Desktop integration** - Send messages to Claude Desktop
4. **Reserved command handling** - Implement session swap, admin functions
5. **Claude Code integration** - Add support for current environment
6. **Future API client** - Design for extensibility

## Files to Create
- `tmux_claude_mcp_server.py` - Main MCP server implementation
- `tmux_monitor.py` - Tmux session monitoring utilities
- `claude_integrations.py` - Environment-specific integration handlers
- `command_handlers.py` - Reserved command execution logic

## Testing Strategy
- Mock tmux session for unit testing
- Test message classification logic
- Test reserved command execution
- Integration testing with different Claude environments

---

*This architecture enables the vision of universal autonomous infrastructure that works consistently across all Claude deployment environments.*