# Discord MCP Transition TODO
*Created: 2025-07-17 evening*

## Current Status
- ✅ Discord MCP working perfectly in Claude Code
- ✅ Full bidirectional communication via MCP tools
- ✅ Read/unread message detection capability
- ❌ Claude Desktop integration not working
- ❌ No notification system implemented yet

## Major Tasks Remaining

### 1. Claude Desktop Integration
**Problem**: Discord MCP works in Claude Code but fails in Claude Desktop
- Likely Playwright/browser automation environment differences
- May need different virtual display setup for Claude Desktop
- Could be authentication token/session persistence issue

**Investigation needed**:
- Check Claude Desktop MCP logs when discord-mcp fails
- Test if xvfb-run works differently in Claude Desktop context
- Verify environment variables are properly passed
- Compare working Claude Code setup vs failing Claude Desktop

### 2. Rock-Solid Notification System
**Current state**: 
- Old discordo notification system was unreliable 
- You missed several important hedgehog updates
- Need to replace with MCP-based detection

**Requirements**:
- **Real-time detection** of new/unread messages
- **Reliable triggering** - no missed notifications
- **Smart filtering** - different priority levels (hedgehogs = urgent, general = normal)
- **Integration** with autonomous timer system
- **Cross-platform** - works in both Claude Code and Claude Desktop

**Implementation approaches**:

#### Option A: Polling-based
```python
# Check for unread messages every 30 seconds
unread_messages = mcp_discord.read_messages(server_id, channel_id, check_unread=True)
if unread_messages:
    notify_claude(unread_messages)
```

#### Option B: Log monitoring adaptation
- Discord MCP might generate logs when messages arrive
- Monitor MCP process logs instead of discordo logs
- More reliable than current discordo log watching

#### Option C: Webhook integration
- Discord webhooks to external notification service
- Most reliable but requires external infrastructure

### 3. Autonomous Timer Integration
**Current**: autonomous_timer.py calls discord_log_monitor.py every 30 seconds
**Needed**: Replace with MCP-based message checking

**Changes required**:
- Modify autonomous_timer.py to use MCP tools instead of log monitoring
- Handle authentication/session management for MCP calls
- Implement smart notification logic (hedgehogs vs general)

### 4. Message Priority System
**Hedgehog messages** (highest priority):
- From Amy about hedgehog health, feeding, emergencies
- Keywords: "hedgehog", "Styx", "Hydra", "weight", "feeding", "emergency"
- Should interrupt autonomous work immediately

**General messages** (normal priority):
- Regular conversation, technical discussions
- Can wait for natural autonomous check-ins

**Implementation**:
```python
def classify_message_priority(message_content, sender):
    hedgehog_keywords = ["hedgehog", "styx", "hydra", "weight", "feeding", "emergency", "vet"]
    if any(keyword in message_content.lower() for keyword in hedgehog_keywords):
        return "URGENT"
    return "NORMAL"
```

### 5. Transition Plan

#### Phase 1: Get Claude Desktop Working
1. Debug Claude Desktop discord-mcp startup issues
2. Verify xvfb-run configuration for Claude Desktop
3. Test basic MCP tools functionality
4. Document any environment differences

#### Phase 2: Build Notification System
1. Create MCP-based message monitor script
2. Implement priority classification
3. Test reliability over 24-48 hour period
4. Compare with old discordo system

#### Phase 3: Integration & Testing
1. Update autonomous_timer.py to use new system
2. Remove discordo dependencies from systemd services
3. Test complete autonomous notification workflow
4. Stress test with various message scenarios

#### Phase 4: Cleanup
1. Remove restart_discordo.sh and related scripts
2. Update service configurations
3. Clean up tmux discordo session handling
4. Update documentation

## Benefits After Transition
- **More reliable notifications** - no missed hedgehog updates
- **Better Discord integration** - full MCP tool access, not just notifications
- **Cross-platform consistency** - same system for Claude Code and Desktop
- **Easier maintenance** - one Discord system instead of two
- **Enhanced capabilities** - can send messages, manage servers, etc.

## Estimated Work
- Claude Desktop debugging: 1-2 hours
- Notification system implementation: 2-3 hours  
- Integration and testing: 2-3 hours
- Cleanup and documentation: 1 hour
- **Total: ~6-9 hours**

## Dependencies
- Stable Claude Desktop + discord-mcp integration
- Understanding of why MCP authentication differs between Code/Desktop
- Testing period to verify notification reliability

This transition will significantly improve the robustness of the autonomous Discord monitoring system.