#!/bin/bash
# ClAP Line Endings Cleanup Script
# Run this script on Linux to clean up any Windows CRLF line endings in the repository
# This is particularly useful after cloning from Windows or importing files from Windows

set -e

echo "🔧 ClAP Line Endings Cleanup"
echo "============================"
echo ""

# Get the script directory (should be utils/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the repository root (parent of utils/)
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

echo "📁 Repository: $REPO_ROOT"
echo ""

# Check if any files have CRLF endings
echo "🔍 Checking for Windows CRLF line endings..."
CRLF_FILES=$(find . -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.txt" -o -name "*.md" -o -name "*.conf" -o -name "*.service" -o -name "*.yaml" -o -name "*.yml" | xargs grep -l $'\r' 2>/dev/null || true)

if [[ -z "$CRLF_FILES" ]]; then
    echo "✅ No Windows line endings found - repository is clean!"
    exit 0
fi

echo "🔄 Found files with Windows line endings:"
echo "$CRLF_FILES" | sed 's/^/   /'
echo ""

echo "🔧 Converting CRLF to LF endings..."

# Convert line endings for all text files
find . \( -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.txt" -o -name "*.md" -o -name "*.conf" -o -name "*.service" -o -name "*.yaml" -o -name "*.yml" \) -exec sed -i 's/\r$//' {} \;

# Also fix any executable files that might not have extensions
find . -type f -executable -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./target/*" -not -path "./build/*" -exec sed -i 's/\r$//' {} \; 2>/dev/null || true

echo "✅ Line endings converted to Unix format"
echo ""

# Verify the fix
echo "🔍 Verifying conversion..."
REMAINING_CRLF=$(find . -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.txt" -o -name "*.md" -o -name "*.conf" -o -name "*.service" -o -name "*.yaml" -o -name "*.yml" | xargs grep -l $'\r' 2>/dev/null || true)

if [[ -z "$REMAINING_CRLF" ]]; then
    echo "✅ All line endings successfully converted!"
    echo ""
    echo "💡 Next steps:"
    echo "   1. Review changes: git diff"
    echo "   2. Commit changes: git add -A && git commit -m 'Fix line endings (Windows → Unix)'"
    echo "   3. Push changes: git push"
    echo ""
    echo "🎯 Future prevention: .gitattributes file will prevent this issue going forward"
else
    echo "⚠️  Some files still have CRLF endings:"
    echo "$REMAINING_CRLF" | sed 's/^/   /'
    echo ""
    echo "💡 You may need to manually check these files"
fi