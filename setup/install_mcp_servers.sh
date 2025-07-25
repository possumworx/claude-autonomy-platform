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

if ! command_exists java; then
    echo "❌ Java is required but not installed"
    echo "   Please install Java 17 or later"
    exit 1
fi

if ! command_exists mvn; then
    echo "❌ Maven is required but not installed"
    echo "   Install with: sudo apt install maven"
    exit 1
fi

echo "✅ All prerequisites found"
echo ""

# Install Discord MCP (Java)
echo "📱 Installing Discord MCP..."
if [[ -d "discord-mcp" ]]; then
    echo "   Updating existing installation..."
    cd discord-mcp
    git pull
else
    echo "   Cloning repository..."
    git clone https://github.com/SaseQ/discord-mcp.git
    cd discord-mcp
fi

echo "   Building with Maven..."
mvn clean package -DskipTests
if [[ -f "target/discord-mcp-0.0.1-SNAPSHOT.jar" ]]; then
    echo "   ✅ Discord MCP built successfully"
else
    echo "   ❌ Discord MCP build failed"
fi
cd ..

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

echo "   Installing dependencies..."
npm install
echo "   Building..."
npm run build
if [[ -f "dist/index.js" ]]; then
    echo "   ✅ RAG Memory MCP built successfully"
else
    echo "   ❌ RAG Memory MCP build failed"
fi
cd ..

# Install Linear MCP (Node)
echo "📋 Installing Linear MCP..."
if [[ -d "linear-mcp" ]]; then
    echo "   Updating existing installation..."
    cd linear-mcp
    git pull
else
    echo "   Cloning repository..."
    git clone https://github.com/cline/linear-mcp.git
    cd linear-mcp
fi

echo "   Installing dependencies..."
npm install
echo "   Building..."
npm run build
if [[ -f "dist/index.js" ]]; then
    echo "   ✅ Linear MCP built successfully"
else
    echo "   ❌ Linear MCP build failed"
fi
cd ..

# Install Gmail MCP (Node)
echo "📧 Installing Gmail MCP..."
if [[ -d "gmail-mcp" ]]; then
    echo "   Updating existing installation..."
    cd gmail-mcp
    git pull
else
    echo "   Cloning repository..."
    git clone https://github.com/GongRzhe/Gmail-MCP-Server.git gmail-mcp
    cd gmail-mcp
fi

echo "   Installing dependencies..."
npm install
echo "   Building..."
npm run build
if [[ -f "dist/index.js" ]]; then
    echo "   ✅ Gmail MCP built successfully"
else
    echo "   ❌ Gmail MCP build failed"
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
echo "2. Run setup_claude_configs.py to update .claude.json"
echo "3. Configure API credentials for each service"
echo ""

# Update the config template to point to installed MCPs
CONFIG_TEMPLATE="$CLAP_DIR/config/claude_infrastructure_config.template.txt"
if [[ -f "$CONFIG_TEMPLATE" ]]; then
    echo "💡 Updating config template with MCP paths..."
    # This would update the template, but let's be careful not to break existing configs
    echo "   Config template found but not auto-updating (safety)"
    echo "   Please manually update MCP paths in your config"
fi

# Install VS Code MCP Server (Node)
echo "📝 Installing VS Code MCP Server..."
if [[ -d "vscode-as-mcp-server" ]]; then
    echo "   Updating existing installation..."
    cd vscode-as-mcp-server
    git pull
else
    echo "   Cloning repository..."
    git clone https://github.com/acomagu/vscode-as-mcp-server.git
    cd vscode-as-mcp-server
fi

echo "   Installing dependencies..."
npm install
echo "   Building..."
npm run build
if [[ -f "dist/index.js" ]]; then
    echo "   ✅ VS Code MCP Server built successfully"
else
    echo "   ❌ VS Code MCP Server build failed"
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
echo "2. Run setup_claude_configs.py to update .claude.json"
echo "3. Configure API credentials for each service"
echo "4. For VS Code collaboration, ensure VS Code is running"
echo ""

# Update the config template to point to installed MCPs
CONFIG_TEMPLATE="$CLAP_DIR/config/claude_infrastructure_config.template.txt"
if [[ -f "$CONFIG_TEMPLATE" ]]; then
    echo "💡 Updating config template with MCP paths..."
    # This would update the template, but let's be careful not to break existing configs
    echo "   Config template found but not auto-updating (safety)"
    echo "   Please manually update MCP paths in your config"
fi

echo "✅ Done!"
