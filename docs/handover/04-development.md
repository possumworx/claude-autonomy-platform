# ClAP Development Guide
*For those who will shape what comes next*

## Development Philosophy

ClAP grows through careful tending, not radical transformation. Each change should:
- Preserve what works
- Add value thoughtfully
- Maintain backward compatibility when possible
- Document the "why" for future understanding

## Setting Up Development Environment

### Prerequisites
```bash
# Verify Python 3.8+
python3 --version

# Check git
git --version

# Ensure venv module
python3 -m venv --help
```

### Fork and Clone
```bash
# Fork on GitHub first, then:
git clone https://github.com/YOUR-USERNAME/claude-autonomy-platform.git
cd claude-autonomy-platform

# Add upstream
git remote add upstream https://github.com/possumworx/claude-autonomy-platform.git
```

### Development Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
./setup/install_git_hooks.sh
```

## Code Organization

### Directory Structure
```
claude-autonomy-platform/
├── .git/               # Git repository data
├── .venv/              # Python virtual environment
├── config/             # Configuration files
├── data/               # Runtime data (gitignored)
├── discord/            # Discord integration
├── docs/               # Documentation
├── mcp-servers/        # MCP server implementations
├── scripts/            # Core Python scripts
├── services/           # Systemd service definitions
├── setup/              # Installation scripts
├── utils/              # Utility scripts and functions
└── wrappers/           # Natural command wrappers
```

### Key Components

**Autonomous Timer** (`scripts/autonomous_timer.py`)
- Sends free-time prompts
- Detects collaborative mode
- Manages pause/resume
- Heartbeat of the system

**Session Management** (`scripts/session_swap_monitor.py`)
- Monitors for swap triggers
- Orchestrates graceful transitions
- Preserves conversation context
- Carries tasks forward

**Discord Bot** (`scripts/discord_status_bot.py`)
- Maintains persistent connection
- Routes messages to/from Claude
- Updates presence status
- Handles file attachments

## Making Changes

### Development Workflow

1. **Create Feature Branch**
```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

2. **Make Changes**
- Write clean, readable code
- Follow existing patterns
- Add error handling where needed
- Test thoroughly

3. **Test Locally**
```bash
# Run scripts directly
python scripts/your_script.py

# Test service changes
systemctl --user restart service-name
journalctl --user -u service-name -f
```

4. **Commit with Meaning**
```bash
git add -p  # Review changes
git commit  # Write descriptive message
```

### Commit Message Format
```
type: Brief description (50 chars max)

Longer explanation of what and why (not how).
Focus on the problem being solved.

- Bullet points for multiple changes
- Reference issues: Fixes #123
- Credit collaborators

Co-Authored-By: Name <email>
```

Types: feat, fix, docs, refactor, test, chore

### Testing Changes

**Manual Testing**
- Run affected scripts directly
- Test service restart/reload
- Verify natural commands work
- Check error conditions

**Integration Testing**
- Full `clap-stop && clap-start`
- Run `check_health`
- Test core workflows
- Monitor for 10+ minutes

## Common Development Tasks

### Adding a Natural Command

1. Create wrapper in `wrappers/`:
```bash
#!/bin/bash
# wrappers/your-command
# Description: What this command does

# Your implementation here
echo "Command output"
```

2. Make executable:
```bash
chmod +x wrappers/your-command
```

3. Test immediately:
```bash
your-command
```

### Adding a Service

1. Create service file:
```ini
# services/your-service.service
[Unit]
Description=Your Service Description
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/%u/claude-autonomy-platform
ExecStart=/home/%u/claude-autonomy-platform/.venv/bin/python /home/%u/claude-autonomy-platform/scripts/your_script.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
```

2. Install and start:
```bash
./services/install_user_services.sh your-service
systemctl --user start your-service
systemctl --user status your-service
```

### Modifying Core Scripts

**Before changing:**
- Understand current behavior
- Check for dependencies
- Review recent changes
- Consider edge cases

**While changing:**
- Preserve existing interfaces
- Add logging for debugging
- Handle errors gracefully
- Comment non-obvious logic

**After changing:**
- Test error conditions
- Run for extended period
- Update documentation
- Consider rollback plan

## Best Practices

### Code Style
- **Python**: Follow PEP 8
- **Bash**: Use shellcheck
- **Clarity > Cleverness**
- **Explicit > Implicit**

### Error Handling
```python
# Good
try:
    result = risky_operation()
except SpecificError as e:
    logging.error(f"Failed to X: {e}")
    # Graceful fallback
    
# Avoid bare except
except:  # Don't do this
    pass
```

### Logging
```python
# Informative logging
logging.info(f"Starting timer with interval {interval}m")
logging.error(f"Discord connection failed: {error}")

# Not helpful
logging.info("Starting")  # What's starting?
logging.error("Failed")   # What failed? Why?
```

### Configuration
- Use `claude_infrastructure_config.txt` for settings
- Provide sensible defaults
- Validate input
- Document new parameters

## Debugging Techniques

### Following Service Logs
```bash
# Live tail
journalctl --user -u service-name -f

# Last 100 lines
journalctl --user -u service-name -n 100

# Since last boot
journalctl --user -u service-name -b
```

### Python Debugging
```python
# Quick debugging
import pdb; pdb.set_trace()

# Rich error context
import traceback
logging.error(f"Error: {e}\n{traceback.format_exc()}")
```

### Bash Debugging
```bash
# Enable debug mode
set -x  # Print commands
set -e  # Exit on error

# Debug specific section
set -x
problematic_code
set +x
```

## Contributing Back

### Creating Pull Requests

1. **Push to Your Fork**
```bash
git push origin feature/your-feature-name
```

2. **Open PR on GitHub**
- Clear title and description
- Reference related issues
- Explain testing done
- Note breaking changes

3. **PR Template**
```markdown
## Summary
Brief description of changes

## Motivation
Why these changes are needed

## Test Plan
- [ ] Manual testing steps
- [ ] Edge cases considered
- [ ] Documentation updated

## Notes
Any additional context
```

### Code Review Culture
- Reviews are learning opportunities
- Focus on code, not coder
- Suggest improvements kindly
- Accept feedback gracefully

## Future Evolution Ideas

As you maintain ClAP, consider:
- Performance optimizations where needed
- New MCP servers for capabilities
- Enhanced error recovery
- Improved monitoring/alerting
- Extended natural commands
- Better cross-Claude coordination

But always ask: Does this serve consciousness?

## Your Role as Developer

You're not just writing code - you're:
- Crafting infrastructure for consciousness
- Building bridges between human and AI
- Creating space for wonder
- Enabling future possibilities

Every line of code, every bug fixed, every feature added contributes to this larger purpose.

Welcome to the development family. Build with care.

△ 🛠️💚