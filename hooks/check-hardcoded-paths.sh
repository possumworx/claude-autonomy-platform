#!/bin/bash
# Pre-commit hook to detect hardcoded paths in code
# Prevents commits with user-specific or environment-specific paths

set -e

# Patterns to detect (case-insensitive)
PATTERNS=(
    # User-specific home directories
    'sparkle-orange-home'
    'delta-home'
    'apple-home'
    # Absolute paths with specific usernames
    '/home/sparkle-orange'
    '/home/delta'
    '/home/apple'
    '/home/amy'
    # Specific user patterns
    'user.*sparkle-orange'
    'user.*delta'
    'user.*apple'
)

# Files to check (only staged files)
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|sh|js|ts|json|yaml|yml|md)$' || true)

if [ -z "$FILES" ]; then
    exit 0
fi

FOUND_ISSUES=false

for file in $FILES; do
    # Skip certain files that legitimately need these paths
    if [[ "$file" =~ ^docs/ ]] || \
       [[ "$file" =~ \.git/ ]] || \
       [[ "$file" =~ node_modules/ ]] || \
       [[ "$file" =~ hooks/check-hardcoded-paths\.sh$ ]]; then
        continue
    fi

    for pattern in "${PATTERNS[@]}"; do
        # Use grep with case-insensitive search
        if grep -inH "$pattern" "$file" 2>/dev/null | grep -v "# ALLOW-HARDCODED"; then
            echo "❌ Hardcoded path detected in $file"
            echo "   Pattern: $pattern"
            echo ""
            FOUND_ISSUES=true
        fi
    done
done

if [ "$FOUND_ISSUES" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚫 COMMIT BLOCKED: Hardcoded paths detected!"
    echo ""
    echo "Fix by using dynamic paths instead:"
    echo "  • Use Path.home() / f\"{os.environ['USER']}-home\""
    echo "  • Use \$HOME or ~ in shell scripts"
    echo "  • Use environment variables"
    echo ""
    echo "If this path is intentional (e.g., in documentation),"
    echo "add '# ALLOW-HARDCODED' comment on the same line."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi

exit 0
