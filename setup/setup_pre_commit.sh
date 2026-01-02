#!/bin/bash
# setup_pre_commit.sh - Install and configure pre-commit framework
# Part of ClAP security infrastructure

set -e

echo "🔧 Setting up pre-commit framework for ClAP..."
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$(dirname "$SCRIPT_DIR")"

# Check if we're in a git repository
if [[ ! -d "$CLAP_DIR/.git" ]]; then
    echo "❌ ERROR: $CLAP_DIR is not a git repository!"
    exit 1
fi

# Navigate to ClAP directory
cd "$CLAP_DIR"

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."

    # Try pipx first (preferred method)
    if command -v pipx &> /dev/null; then
        pipx install pre-commit
    # Fall back to pip3 with --user
    elif command -v pip3 &> /dev/null; then
        pip3 install --user pre-commit
    else
        echo "❌ ERROR: Neither pipx nor pip3 found!"
        echo "   Please install pipx or pip3 first"
        exit 1
    fi

    # Verify installation
    if ! command -v pre-commit &> /dev/null; then
        echo "❌ ERROR: pre-commit installation failed!"
        echo "   Try: pipx install pre-commit"
        exit 1
    fi

    echo "✅ pre-commit installed successfully"
else
    echo "✅ pre-commit already installed ($(pre-commit --version))"
fi

# Install the git hook scripts
echo "🔗 Installing pre-commit git hooks..."
pre-commit install

# Verify hooks are installed
if [[ ! -f "$CLAP_DIR/.git/hooks/pre-commit" ]]; then
    echo "❌ ERROR: Hooks not installed correctly!"
    exit 1
fi

echo "✅ Git hooks installed successfully"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Pre-commit setup complete!"
echo ""
echo "The following checks will run on every commit:"
echo "  ✅ Hardcoded path detection (sparkle-orange-home, etc.)"  # ALLOW-HARDCODED
echo "  ✅ Secret scanning (API keys, passwords, tokens)"  # ALLOW-SECRET
echo "  ✅ Line ending fixes (LF only)"
echo "  ✅ Shell script validation (shellcheck)"
echo "  ✅ JSON/YAML validation"
echo "  ✅ Python code formatting (black)"
echo "  ✅ Large file detection"
echo "  ✅ Private key detection"
echo ""
echo "💡 To run checks manually: pre-commit run --all-files"
echo "💡 To bypass checks (NOT recommended): git commit --no-verify"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
