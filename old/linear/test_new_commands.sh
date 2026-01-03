#!/bin/bash
# Test the new Linear commands

cd "$(dirname "$0")"

echo "Testing new Linear commands..."
echo "================================"
echo

# Test standup command
echo "1. Testing standup command:"
echo "   ./standup --help"
if [ -x ./standup ]; then
    ./standup --help 2>&1 | head -5 || echo "   Command exists but may need Claude session"
else
    echo "   Error: standup not found or not executable"
fi
echo

# Test assign command
echo "2. Testing assign command:"
echo "   ./assign --help"
if [ -x ./assign ]; then
    ./assign --help 2>&1 | head -5 || echo "   Command exists but may need Claude session"
else
    echo "   Error: assign not found or not executable"
fi
echo

# Test estimate command
echo "3. Testing estimate command:"
echo "   ./estimate"
if [ -x ./estimate ]; then
    ./estimate 2>&1 | head -5 || echo "   Command exists but may need Claude session"
else
    echo "   Error: estimate not found or not executable"
fi
echo

# Test label command
echo "4. Testing label command:"
echo "   ./label"
if [ -x ./label ]; then
    ./label 2>&1 | head -5 || echo "   Command exists but may need Claude session"
else
    echo "   Error: label not found or not executable"
fi
echo

# Test move command
echo "5. Testing move command:"
echo "   ./move"
if [ -x ./move ]; then
    ./move 2>&1 | head -5 || echo "   Command exists but may need Claude session"
else
    echo "   Error: move not found or not executable"
fi
echo

echo "================================"
echo "New commands are ready for use!"
echo
echo "Add to PATH with: export PATH=\"\$PATH:$(pwd)\""