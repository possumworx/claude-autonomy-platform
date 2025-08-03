#!/bin/bash
# install_git_hooks.sh - Install git commit hooks for ClAP safety
# Part of ClAP v0.5 safety improvements

set -e

echo "🔧 Installing ClAP Git Hooks..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$(dirname "$SCRIPT_DIR")"

# Check if we're in a git repository
if [[ ! -d "$CLAP_DIR/.git" ]]; then
    echo "❌ ERROR: $CLAP_DIR is not a git repository!"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$CLAP_DIR/.git/hooks"

# Create the pre-commit hook
cat > "$CLAP_DIR/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# ClAP Pre-commit Hook - Safety checks before allowing commits

echo "🚀 Running ClAP pre-commit checks..."

# Check 1: Verify we're in claude-autonomy-platform directory
if [[ ! -f "my_architecture.md" ]] || [[ ! -f "clap_architecture.md" ]]; then
    echo "❌ ERROR: Not in claude-autonomy-platform directory!"
    echo "   Current directory: $(pwd)"
    echo "   Please cd to claude-autonomy-platform before committing"
    exit 1
fi

# Check 2: Look for hardcoded paths
echo "🏠 Checking for hardcoded user paths..."

# Try to get LINUX_USER from config
CONFIG_FILE="$HOME/claude-autonomy-platform/claude_infrastructure_config.txt"
if [[ -f "$CONFIG_FILE" ]]; then
    LINUX_USER=$(grep "LINUX_USER=" "$CONFIG_FILE" 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
    
    if [[ -n "$LINUX_USER" ]] && git diff --cached --name-only | xargs grep -l "/home/$LINUX_USER" 2>/dev/null; then
        echo "❌ ERROR: Hardcoded /home/$LINUX_USER path detected!"
        echo "   Use ~ or \$HOME or relative paths instead"
        echo "   To bypass (not recommended): git commit --no-verify"
        exit 1
    fi
fi

# General check for any hardcoded /home paths
HARDCODED_PATHS=$(git diff --cached --name-only | xargs grep -n "/home/[a-zA-Z0-9_-]\+" 2>/dev/null || true)
if [[ -n "$HARDCODED_PATHS" ]]; then
    echo "⚠️  WARNING: Hardcoded home paths detected:"
    echo "$HARDCODED_PATHS" | head -5
    echo "   Consider using relative paths or environment variables"
fi

# Check 3: Scan for potential secrets
echo "🔍 Scanning for accidentally included credentials..."

SECRET_PATTERNS="(oauth_client_secret|discord.*token|api[_-]?key|client_secret|password|private[_-]?key)"
FOUND_SECRETS=$(git diff --cached --name-only | xargs grep -nE "$SECRET_PATTERNS" 2>/dev/null || true)

if [[ -n "$FOUND_SECRETS" ]]; then
    echo "❌ ERROR: Potential secrets/credentials detected!"
    echo "$FOUND_SECRETS" | head -10
    echo "   Remove sensitive data before committing"
    echo "   To bypass (REALLY not recommended): git commit --no-verify"
    exit 1
fi

# Check 4: Verify Claude Code is running from correct directory (if running)
CLAUDE_PID=$(pgrep -f "claude-code" || true)
if [[ -n "$CLAUDE_PID" ]]; then
    CLAUDE_CWD=$(readlink /proc/$CLAUDE_PID/cwd 2>/dev/null || true)
    CURRENT_DIR=$(pwd)
    if [[ -n "$CLAUDE_CWD" ]] && [[ "$CLAUDE_CWD" != "$CURRENT_DIR" ]]; then
        echo "⚠️  WARNING: Claude Code running from different directory!"
        echo "   Claude Code CWD: $CLAUDE_CWD"
        echo "   Repository CWD: $CURRENT_DIR"
    fi
fi

# Check 5: Quick service status check
if ! systemctl --user is-active --quiet autonomous-timer.service 2>/dev/null; then
    echo "⚠️  WARNING: autonomous-timer.service is not running"
fi

# Check 6: Verify important config files aren't being deleted
DELETED_FILES=$(git diff --cached --name-only --diff-filter=D)
if echo "$DELETED_FILES" | grep -qE "(claude_infrastructure_config\.txt|notification_config\.json|my_architecture\.md)"; then
    echo "❌ ERROR: Attempting to delete critical configuration files!"
    echo "   These files are essential for ClAP operation"
    exit 1
fi

echo "✅ All pre-commit checks passed!"
exit 0
EOF

# Make the hook executable
chmod +x "$CLAP_DIR/.git/hooks/pre-commit"

echo "✅ Git hooks installed successfully!"
echo ""
echo "The pre-commit hook will now check for:"
echo "  • Correct directory location"
echo "  • Hardcoded paths"
echo "  • Potential secrets/credentials"
echo "  • Claude Code directory alignment"
echo "  • Service status"
echo "  • Critical file deletion"
echo ""
echo "To bypass checks in emergency (not recommended):"
echo "  git commit --no-verify"
