#!/bin/bash
# Find all files using DISCORD_TOKEN

echo "Searching for DISCORD_TOKEN usage in ClAP..."
echo "=========================================="

# Search in Python files
echo -e "\nPython files:"
find . -name "*.py" -type f -exec grep -l "DISCORD_TOKEN" {} \; 2>/dev/null

# Search in shell scripts
echo -e "\nShell scripts:"
find . -name "*.sh" -type f -exec grep -l "DISCORD_TOKEN" {} \; 2>/dev/null

# Search in config files
echo -e "\nConfig files:"
find . -name "*.json" -o -name "*.txt" -o -name "*.yml" -o -name "*.yaml" | xargs grep -l "DISCORD_TOKEN" 2>/dev/null

echo -e "\nDone!"
