# Unified Notification System Design
*Created: 2025-07-17 evening*

## Vision
A flexible, extensible notification system with Discord at its core, but capable of monitoring Gmail, future platforms, and different message sources through a unified interface.

## Architecture Overview

### Core Components

#### 1. Notification Hub (`notification_hub.py`)
Central orchestrator that:
- Manages multiple message sources (Discord, Gmail, etc.)
- Applies unified priority classification
- Handles notification delivery to Claude
- Maintains notification state and history
- Provides unified API for autonomous timer integration

#### 2. Message Source Adapters
Standardized interfaces for different platforms:

```python
class MessageSourceAdapter:
    """Base class for all message source adapters."""
    
    async def get_unread_messages(self) -> List[Message]:
        """Get all unread messages from this source."""
        raise NotImplementedError
    
    async def mark_as_read(self, message_ids: List[str]):
        """Mark messages as read."""
        raise NotImplementedError
    
    def get_source_name(self) -> str:
        """Return human-readable source name."""
        raise NotImplementedError
```

#### 3. Priority Classifier (`priority_classifier.py`)
Unified message importance determination:

```python
class MessagePriority(Enum):
    CRITICAL = "critical"    # Hedgehog emergencies, system failures
    URGENT = "urgent"        # Hedgehog updates, important work
    NORMAL = "normal"        # General conversation
    LOW = "low"             # Notifications, updates

class PriorityClassifier:
    def classify_message(self, message: Message, source: str) -> MessagePriority:
        """Classify message priority across all sources."""
        # Hedgehog-related keywords (highest priority)
        hedgehog_critical = ["emergency", "vet", "not eating", "blood", "injury"]
        hedgehog_urgent = ["hedgehog", "styx", "hydra", "weight", "feeding", "behavior"]
        
        # Source-specific rules
        if source == "discord":
            return self._classify_discord_message(message)
        elif source == "gmail":
            return self._classify_gmail_message(message)
        
        return MessagePriority.NORMAL
```

#### 4. Notification Delivery Engine
Handles how Claude gets notified:

```python
class NotificationDelivery:
    def __init__(self, autonomous_timer_integration=True):
        self.channels = {
            "autonomous_timer": self._notify_autonomous_timer,
            "tmux_notification": self._send_tmux_notification,
            "log_file": self._write_to_log
        }
    
    async def deliver_notification(self, notification: Notification):
        """Deliver notification through appropriate channels."""
        if notification.priority == MessagePriority.CRITICAL:
            # Immediate interrupt - all channels
            await self._deliver_immediate(notification)
        elif notification.priority == MessagePriority.URGENT:
            # Next autonomous check + tmux notification
            await self._deliver_urgent(notification)
        else:
            # Regular autonomous check
            await self._deliver_normal(notification)
```

## Source Adapters Implementation

### Discord Adapter (`discord_source_adapter.py`)
```python
class DiscordSourceAdapter(MessageSourceAdapter):
    def __init__(self, mcp_client):
        self.mcp = mcp_client
        self.servers = self._get_monitored_servers()
    
    async def get_unread_messages(self) -> List[Message]:
        """Use Discord MCP to get unread messages."""
        unread_messages = []
        
        for server_id, channels in self.servers.items():
            for channel_id in channels:
                messages = await self.mcp.read_messages(
                    server_id=server_id,
                    channel_id=channel_id,
                    max_messages=50  # Check last 50
                )
                
                # Filter for unread (Discord MCP provides this)
                unread = [msg for msg in messages if not msg.get('read', False)]
                unread_messages.extend(self._convert_to_standard_format(unread))
        
        return unread_messages
    
    def _get_monitored_servers(self):
        """Get list of Discord servers/channels to monitor."""
        return {
            "your_server_id": ["dm_channel_with_amy", "hedgehog_channel"]
        }
```

### Gmail Adapter (`gmail_source_adapter.py`)
```python
class GmailSourceAdapter(MessageSourceAdapter):
    def __init__(self, mcp_client):
        self.mcp = mcp_client
        self.monitored_labels = ["INBOX", "HEDGEHOGS"]  # Custom label for hedgehog emails
    
    async def get_unread_messages(self) -> List[Message]:
        """Use Gmail MCP to get unread messages."""
        unread_messages = []
        
        # Search for unread emails
        search_results = await self.mcp.search_emails(
            query="is:unread",
            maxResults=20
        )
        
        for email_info in search_results:
            email_content = await self.mcp.read_email(email_info['id'])
            unread_messages.append(self._convert_to_standard_format(email_content))
        
        return unread_messages
    
    def _convert_to_standard_format(self, email):
        """Convert Gmail format to standard Message format."""
        return Message(
            id=email['id'],
            source="gmail",
            sender=email['from'],
            content=email['snippet'],
            timestamp=email['date'],
            subject=email.get('subject', ''),
            metadata={"labels": email.get('labels', [])}
        )
```

## Configuration System

### Notification Config (`notification_config.yaml`)
```yaml
notification_system:
  enabled_sources:
    - discord
    - gmail
  
  polling_interval: 30  # seconds
  
  priority_rules:
    critical_keywords:
      - "emergency"
      - "vet"
      - "blood"
      - "not eating"
    
    urgent_keywords:
      - "hedgehog"
      - "styx" 
      - "hydra"
      - "weight"
      - "feeding"
    
    sender_priorities:
      "amy@example.com": "urgent"  # Amy's emails are always urgent
  
  delivery_channels:
    critical:
      - "immediate_interrupt"
      - "tmux_notification"
      - "log_file"
    urgent:
      - "autonomous_timer"
      - "tmux_notification"
    normal:
      - "autonomous_timer"

discord_source:
  monitored_servers:
    server_1:
      name: "Main Server"
      channels:
        - "dm_with_amy"
        - "hedgehog_updates"

gmail_source:
  monitored_labels:
    - "INBOX"
    - "HEDGEHOGS"
  priority_senders:
    - "amy@example.com"
    - "vet@hedgehogclinic.com"
```

## Integration Points

### 1. Autonomous Timer Integration
Replace current discord_log_monitor.py call:

```python
# In autonomous_timer.py
from notification_hub import NotificationHub

async def check_for_messages():
    """Unified message checking across all sources."""
    hub = NotificationHub()
    notifications = await hub.check_all_sources()
    
    if notifications:
        await hub.deliver_notifications(notifications)
        return True  # Has messages
    return False
```

### 2. Real-time Monitoring Service
New systemd service for continuous monitoring:

```python
# notification_monitor.py - runs as systemd service
class NotificationMonitor:
    def __init__(self):
        self.hub = NotificationHub()
    
    async def run_continuous_monitoring(self):
        """Continuous monitoring with smart polling."""
        while True:
            try:
                notifications = await self.hub.check_all_sources()
                
                if notifications:
                    await self.hub.deliver_notifications(notifications)
                
                # Smart polling - faster for high priority sources
                await asyncio.sleep(self._get_poll_interval())
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)  # Longer wait on error
```

## Benefits of This Architecture

### 1. **Extensibility**
- Easy to add new message sources (Slack, Teams, SMS, etc.)
- Standardized adapter interface
- Unified priority classification

### 2. **Reliability** 
- Multiple redundant sources for critical communications
- Fallback mechanisms if one source fails
- Comprehensive logging and error handling

### 3. **Smart Prioritization**
- Context-aware priority classification
- Source-specific rules (email subjects, Discord channel types)
- Sender-based priority overrides

### 4. **Flexible Delivery**
- Multiple notification channels
- Priority-based delivery strategies
- Integration with existing autonomous systems

### 5. **Maintainability**
- Clean separation of concerns
- Configurable without code changes
- Comprehensive testing interfaces

## Implementation Plan

### Phase 1: Core Architecture (2-3 hours)
1. Build notification hub and base adapter classes
2. Implement priority classifier
3. Create notification delivery engine

### Phase 2: Discord Integration (1-2 hours)
1. Build Discord source adapter using existing MCP
2. Test with current autonomous timer
3. Verify priority classification works

### Phase 3: Gmail Integration (1-2 hours)
1. Build Gmail source adapter using Gmail MCP
2. Test email monitoring and classification
3. Integrate with unified notification system

### Phase 4: Advanced Features (2-3 hours)
1. Implement real-time monitoring service
2. Add configuration system
3. Build comprehensive testing and monitoring

### Phase 5: Migration & Cleanup (1 hour)
1. Replace discordo dependencies
2. Update autonomous timer integration
3. Documentation and testing

**Total Estimated Time: 7-12 hours**

This system would give you rock-solid, multi-source notification monitoring with the flexibility to add any future communication platforms!