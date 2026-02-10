#!/bin/bash
# Test script for check_quota - run this from an external terminal
# NOT from within Claude's session

echo "Testing check_quota tool..."
echo "This must be run from an EXTERNAL terminal, not from Claude!"
echo ""

# Test basic usage
echo "=== Test 1: Basic output ==="
~/claude-autonomy-platform/utils/check_quota
echo ""

# Test JSON output
echo "=== Test 2: JSON output ==="
~/claude-autonomy-platform/utils/check_quota --json
echo ""

# Test threshold check
echo "=== Test 3: Threshold check (exit code) ==="
if ~/claude-autonomy-platform/utils/check_quota --threshold; then
    echo "✅ All quotas under 80%"
else
    echo "⚠️  One or more quotas exceed 80%"
fi

echo ""
echo "Test complete!"