#!/bin/bash
# Linear + VS Code Integration Setup Script
# For Amy - Making development magical! ✨

echo "🚀 Setting up Linear + VS Code Integration..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository! Please run from your project folder."
    exit 1
fi

# Install Linear VS Code extensions
echo "📦 Installing VS Code extensions..."
code --install-extension linear.linear-connect
code --install-extension strigo.linear

echo "✅ Extensions installed!"

# Create git hooks for Linear integration
mkdir -p .git/hooks

# Pre-commit hook to check for Linear issue IDs
cat > .git/hooks/prepare-commit-msg << 'EOF'
#!/bin/bash
# Auto-prepend Linear issue ID from branch name

BRANCH_NAME=$(git branch --show-current)
ISSUE_ID=$(echo $BRANCH_NAME | grep -oE 'CLA-[0-9]+' || true)

# If branch has Linear ID and commit message doesn't
if [ ! -z "$ISSUE_ID" ] && ! grep -q "$ISSUE_ID" "$1"; then
    echo "$ISSUE_ID: $(cat $1)" > "$1"
    echo "✨ Auto-added Linear issue ID: $ISSUE_ID"
fi
EOF

chmod +x .git/hooks/prepare-commit-msg

echo "🎯 Git hooks configured!"

# Create helper scripts
mkdir -p scripts

# Quick branch creator
cat > scripts/new-branch.sh << 'EOF'
#!/bin/bash
# Usage: ./scripts/new-branch.sh CLA-123 "fix discord timeout"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <Linear-ID> <description>"
    echo "Example: $0 CLA-123 'fix discord timeout'"
    exit 1
fi

ISSUE_ID=$1
DESC=$(echo "$2" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
BRANCH_NAME="$ISSUE_ID-$DESC"

git checkout -b "$BRANCH_NAME"
echo "✅ Created branch: $BRANCH_NAME"
EOF

chmod +x scripts/new-branch.sh

# Status checker
cat > scripts/status.sh << 'EOF'
#!/bin/bash
# Shows git + Linear status

echo "📊 Project Status"
echo "=================="
echo ""
echo "🌿 Current Branch:"
git branch --show-current
echo ""
echo "📝 Recent Commits:"
git log --oneline -5
echo ""
echo "📋 Uncommitted Changes:"
git status -s
EOF

chmod +x scripts/status.sh

echo ""
echo "✨ Linear + VS Code Integration Complete! ✨"
echo ""
echo "🎯 New Commands Available:"
echo "  ./scripts/new-branch.sh CLA-123 'description'  - Create Linear-linked branch"
echo "  ./scripts/status.sh                            - See project status"
echo "  ./deploy.sh 'CLA-123: message'                 - Deploy with Linear link"
echo ""
echo "🔧 VS Code Features:"
echo "  - Linear Connect installed (OAuth for Linear API)"
echo "  - Linear extension installed (browse issues in VS Code)"
echo "  - Git commits will auto-add Linear IDs from branch names"
echo ""
echo "💡 Next: Run 'Linear: Authenticate' in VS Code Command Palette (Ctrl+Shift+P)"
