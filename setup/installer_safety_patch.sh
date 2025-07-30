#!/bin/bash
# Add this section after Step 12b (utility commands setup) in the installer

# Step 12c: Set up safety features and diagnostic tools
echo "🛡️  Step 12c: Setting up safety features and diagnostic tools..."

# Install enhanced health check
if [[ -f "$CLAP_DIR/utils/healthcheck_status_enhanced.py" ]]; then
    echo "   Installing enhanced health check with config verification..."
    # Backup original if it exists
    if [[ -f "$CLAP_DIR/utils/healthcheck_status.py" ]]; then
        cp "$CLAP_DIR/utils/healthcheck_status.py" "$CLAP_DIR/utils/healthcheck_status.py.backup"
    fi
    # Use enhanced version
    cp "$CLAP_DIR/utils/healthcheck_status_enhanced.py" "$CLAP_DIR/utils/healthcheck_status.py"
    echo "   ✅ Enhanced health check installed"
else
    echo "   ⚠️  Enhanced health check not found, using standard version"
fi

# Install config locations reference
if [[ -f "$CLAP_DIR/utils/config_locations.sh" ]]; then
    chmod +x "$CLAP_DIR/utils/config_locations.sh"
    echo "   ✅ Config locations reference script installed"
fi

# Install secret scanner utility
if [[ -f "$CLAP_DIR/utils/secret-scanner" ]]; then
    chmod +x "$CLAP_DIR/utils/secret-scanner"
    # Add to PATH via .bashrc if not already present
    if ! grep -q "$CLAP_DIR/utils/secret-scanner" "$BASHRC" 2>/dev/null; then
        # It's already in PATH from utils directory setup, just make executable
        echo "   ✅ Secret scanner utility installed"
    fi
else
    echo "   ⚠️  Secret scanner not found"
fi

# Install Git hooks
if [[ -f "$CLAP_DIR/setup/install_git_hooks.sh" ]]; then
    echo "   Installing Git commit hooks..."
    chmod +x "$CLAP_DIR/setup/install_git_hooks.sh"
    (cd "$CLAP_DIR" && ./setup/install_git_hooks.sh)
    echo "   ✅ Git hooks installed (pre-commit safety checks)"
else
    echo "   ⚠️  Git hooks installer not found"
fi

# Install Claude directory enforcer
if [[ -f "$CLAP_DIR/utils/claude_directory_enforcer.sh" ]]; then
    echo "   Installing Claude directory enforcer..."
    
    # Add to .bashrc if not already present
    ENFORCER_LINE="source $CLAP_DIR/utils/claude_directory_enforcer.sh"
    if ! grep -q "$ENFORCER_LINE" "$BASHRC" 2>/dev/null; then
        echo "" >> "$BASHRC"
        echo "# Claude directory enforcer - ensures correct working directory" >> "$BASHRC"
        echo "$ENFORCER_LINE" >> "$BASHRC"
        echo "   ✅ Claude directory enforcer added to .bashrc"
    else
        echo "   ✅ Claude directory enforcer already in .bashrc"
    fi
else
    echo "   ⚠️  Claude directory enforcer not found"
fi

# Clean up deprecated config locations
echo "   Checking for deprecated config files..."
DEPRECATED_CONFIGS=(
    "$CLAUDE_HOME/claude_config.json"
    "$CLAUDE_HOME/claude-autonomy-platform/claude_infrastructure_config.txt"
    "$CLAUDE_HOME/.claude_config.json"
)

FOUND_DEPRECATED=0
for deprecated in "${DEPRECATED_CONFIGS[@]}"; do
    if [[ -f "$deprecated" ]]; then
        echo "   ⚠️  Found deprecated config: $deprecated"
        ((FOUND_DEPRECATED++))
    fi
done

if [[ $FOUND_DEPRECATED -gt 0 ]]; then
    echo ""
    echo "   🚨 WARNING: Found $FOUND_DEPRECATED deprecated config file(s)!"
    echo "   These files are NOT being used and may cause confusion."
    echo "   Consider removing them or moving contents to the correct location:"
    echo "   ~/.config/Claude/.claude.json (for Claude Code config)"
    echo "   $CLAP_DIR/config/claude_infrastructure_config.txt (for ClAP config)"
    echo ""
fi

# Create a quick reference card
echo "   Creating configuration quick reference..."
cat > "$CLAP_DIR/CONFIG_LOCATIONS.txt" <<EOF
ClAP Configuration Quick Reference
==================================
Generated: $(date)

CURRENT CONFIGURATION LOCATIONS:
- Claude Code Config: ~/.config/Claude/.claude.json
- Infrastructure Config: ~/claude-autonomy-platform/config/claude_infrastructure_config.txt  
- Notification Config: ~/claude-autonomy-platform/config/notification_config.json
- Personal Repository: ~/$PERSONAL_REPO/

DIAGNOSTIC COMMANDS:
- Check system health: check_health
- Show config locations: ~/claude-autonomy-platform/utils/config_locations.sh
- Read Discord channel: read_channel <channel-name>
- Scan for secrets: secret-scanner check <files>

GIT SAFETY FEATURES:
- Pre-commit hook checks for:
  • Correct directory location
  • Hardcoded paths (e.g., /home/$LINUX_USER)
  • Potential secrets/credentials
  • Critical file deletion
- To bypass in emergency: git commit --no-verify

COMMON ISSUES:
- If Linear/MCP isn't working: Check you're editing the RIGHT config file!
- If services can't find config: Run check_health to see what's missing
- If you see old config files: They're deprecated - see locations above
- If commit is blocked: Check pre-commit output for specific issue

Last updated by ClAP installer v0.5
EOF

echo "   ✅ Configuration reference created: $CLAP_DIR/CONFIG_LOCATIONS.txt"
echo "   ✅ Safety features and diagnostics installed"
