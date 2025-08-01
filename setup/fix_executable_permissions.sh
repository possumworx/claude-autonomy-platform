#!/bin/bash
# Fix executable permissions for all shell scripts in ClAP
# This ensures scripts are executable after git clone
# Run this on Linux/Unix systems before committing

echo "🔧 Fixing executable permissions for ClAP scripts..."
echo "=============================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Make all .sh files executable
echo "📝 Making .sh files executable..."
find . -name "*.sh" -type f -exec chmod +x {} \; -exec echo "   ✅ {}" \;

# Make specific scripts without .sh extension executable
echo ""
echo "📝 Making utility scripts executable..."

# Utils
chmod +x utils/check_health && echo "   ✅ utils/check_health"

# Discord
chmod +x discord/read_channel && echo "   ✅ discord/read_channel"

# Make Python scripts with shebang executable
echo ""
echo "📝 Making Python scripts with shebang executable..."
for file in $(find . -name "*.py" -type f); do
    if head -n 1 "$file" | grep -q "^#!/usr/bin/env python3"; then
        chmod +x "$file"
        echo "   ✅ $file"
    fi
done

# Make this script itself executable
chmod +x fix_executable_permissions.sh

echo ""
echo "✅ All scripts now have executable permissions!"
echo ""
echo "📋 Next steps:"
echo "1. Verify changes with: git status"
echo "2. Stage changes with: git add -u"
echo "3. Commit with: git commit -m 'Set executable permissions on all shell scripts (POSS-92)'"
echo ""
echo "Note: These permission changes will be preserved in git."
