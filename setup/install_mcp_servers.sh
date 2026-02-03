#!/bin/bash
# Install MCP servers from their source repositories
# This keeps our repo clean and respects other projects' licenses

set -e

echo "📦 Installing MCP Servers for ClAP"
echo "================================"
echo ""

# Get the ClAP directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAP_DIR="$(dirname "$SCRIPT_DIR")"
MCP_DIR="$CLAP_DIR/mcp-servers"

# Create MCP servers directory
mkdir -p "$MCP_DIR"
cd "$MCP_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists git; then
    echo "❌ Git is required but not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is required but not installed"
    exit 1
fi

echo "✅ All prerequisites found"
echo ""

# Install RAG Memory MCP (Node)
echo "🧠 Installing RAG Memory MCP..."
if [[ -d "rag-memory-mcp" ]]; then
    echo "   Updating existing installation..."
    cd rag-memory-mcp
    git pull
else
    echo "   Cloning repository..."
    git clone https://github.com/ttommyth/rag-memory-mcp.git
    cd rag-memory-mcp
fi

# Check if already built
if [[ -f "dist/index.js" ]]; then
    echo "   ✅ RAG Memory MCP already built, skipping..."
else
    echo "   Installing dependencies..."
    npm install
    echo "   Building..."
    npm run build
    if [[ -f "dist/index.js" ]]; then
        echo "   ✅ RAG Memory MCP built successfully"
    else
        echo "   ❌ RAG Memory MCP build failed"
    fi
fi
cd ..

echo ""
echo "🎉 MCP Server Installation Complete!"
echo "==================================="
echo ""
echo "Installed servers in: $MCP_DIR"
echo ""
echo "📋 Next steps:"
echo "1. Update infrastructure config with correct MCP paths"
echo "2. Run generate_mcp_config.py to generate MCP configuration"
echo ""
echo "✅ Done!"
