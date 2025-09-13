#!/bin/bash
# Setup personal Linear commands that work outside Claude sessions

# Create wrapper scripts that can be used directly
cat > ~/bin/new-project << 'EOF'
#!/bin/bash
# Create a new Linear project
echo "create-project \"$@\"" | Claude -p
EOF

cat > ~/bin/new-issue << 'EOF'
#!/bin/bash
# Create a new Linear issue
echo "create-issue \"$@\"" | Claude -p
EOF

cat > ~/bin/bulk-issues << 'EOF'
#!/bin/bash
# Create multiple Linear issues
echo "bulk-create $@" | Claude -p
EOF

# Make them executable
chmod +x ~/bin/new-project
chmod +x ~/bin/new-issue
chmod +x ~/bin/bulk-issues

echo "✅ Created personal Linear commands:"
echo "  - new-project: Create a Linear project"
echo "  - new-issue: Create a Linear issue"
echo "  - bulk-issues: Create multiple issues"
echo ""
echo "These work outside Claude sessions by invoking Claude automatically."