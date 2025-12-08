#!/bin/bash
# Check current Claude session context using ccusage

echo "🔍 Current Session Context Check"
echo "================================"

# Get current session ID from latest symlink
SESSION_ID=$(readlink ~/.config/Claude/debug/latest 2>/dev/null | xargs basename | cut -d'.' -f1)

if [ -z "$SESSION_ID" ]; then
    echo "❌ Could not find current session ID"
    exit 1
fi

echo "📋 Session ID: $SESSION_ID"
echo ""

# Get token usage for current session
echo "💬 Token Usage:"
npx ccusage session --id "$SESSION_ID" 2>/dev/null | grep -E "(Total|Tokens|Cost)" | head -3

echo ""
echo "📊 Summary:"
echo "- Session ID: $SESSION_ID"
echo "- Check time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "⚠️  Note: Token counts may lag behind actual usage"
echo "⚠️  Note: Costs shown are API pricing, not subscription limits"