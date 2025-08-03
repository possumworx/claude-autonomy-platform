#!/bin/bash
# Install fixed git hooks for ClAP repository
# Fixes POSS-168: Pre-commit hook incorrectly looks for files

echo "📝 Installing fixed git hooks..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$(dirname "$SCRIPT_DIR")"

# Create the pre-commit hook
cat > "$CLAP_DIR/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# ClAP Pre-commit Hook - Safety checks before allowing commits

echo "🚀 Running ClAP pre-commit checks..."

# Check 1: Verify we're in claude-autonomy-platform directory
# Look for files that actually exist at the root level
if [[ ! -f "CLAUDE.md" ]] || [[ ! -d "setup" ]] || [[ ! -f "package.json" ]]; then
    echo "❌ ERROR: Not in claude-autonomy-platform directory!"
    echo "   Current directory: $(pwd)"
    echo "   Please cd to claude-autonomy-platform before committing"
    exit 1
fi

# Check 2: Look for hardcoded paths
echo "🏠 Checking for hardcoded user paths..."

# Try to get LINUX_USER from config
CONFIG_FILE="$HOME/claude-autonomy-platform/config/claude_infrastructure_config.txt"
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
if git diff --cached --name-only | xargs grep -lE "/home/[a-zA-Z0-9_-]+" 2>/dev/null | grep -v ".md$"; then
    echo "⚠️  WARNING: Possible hardcoded /home paths detected"
    echo "   Please review your changes and use relative paths where possible"
fi

# Check 3: Look for common credential patterns
echo "🔍 Scanning for accidentally included credentials..."

# Define patterns to check
declare -a PATTERNS=(
    "DISCORD_TOKEN="
    "LINEAR_API_KEY="
    "GITHUB_TOKEN="
    "ghp_"  # GitHub personal access token prefix
    "ghs_"  # GitHub server token prefix
    "password.*=.*['\"]"
    "secret.*=.*['\"]"
    "api[_-]?key.*=.*['\"]"
)

FOUND_SECRETS=false
for pattern in "${PATTERNS[@]}"; do
    if git diff --cached --name-only | xargs grep -liE "$pattern" 2>/dev/null; then
        echo "❌ ERROR: Possible credential detected (pattern: $pattern)"
        FOUND_SECRETS=true
    fi
done

if [[ "$FOUND_SECRETS" == "true" ]]; then
    echo "   Please remove credentials from your commit"
    echo "   To bypass (REALLY not recommended): git commit --no-verify"
    exit 1
fi

echo "✅ All pre-commit checks passed!"
EOF

# Make the hook executable
chmod +x "$CLAP_DIR/.git/hooks/pre-commit"

echo "✅ Git hooks installed successfully!"
echo ""
echo "The pre-commit hook will now:"
echo "  - Verify you're in the claude-autonomy-platform directory"
echo "  - Check for hardcoded paths"
echo "  - Scan for accidentally included credentials"