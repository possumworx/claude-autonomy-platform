#!/bin/bash
# Test script for all Linear commands
# Tests basic functionality of each command

# Change to Linear directory
cd ~/claude-autonomy-platform/linear

echo "=== Testing Linear Commands ==="
echo

# Test 1: List projects
echo "1. Testing 'projects' command..."
./projects
echo

# Test 2: Show todo (assigned issues)
echo "2. Testing 'todo' command..."
./todo
echo

# Test 3: Search issues
echo "3. Testing 'search-issues' command..."
./search-issues "test"
echo

# Test 4: Test project-specific commands (using clap as example)
echo "4. Testing project command 'clap'..."
./clap
echo

# Test 5: List all commands
echo "5. Testing 'list-commands'..."
./list-commands | grep -E "(add|todo|projects|search-issues|update-status|clap)"
echo

echo "=== Tests Complete ==="
echo "Note: 'add' and 'update-status' commands not tested as they modify data"
echo "To test add: add \"Test issue title\" or add \"Test\" --project clap"
echo "To test update-status: update-status ISSUE-123 \"in-progress\""