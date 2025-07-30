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

# Check for Java 17 specifically (POSS-95)
echo "☕ Checking for Java 17 (required for Discord MCP)..."
JAVA_17_FOUND=false
ORIGINAL_JAVA_HOME="$JAVA_HOME"

# Check if Java 17 is available
if command_exists java && java -version 2>&1 | grep -q "17"; then
    JAVA_17_FOUND=true
    echo "   ✅ Java 17 found in current environment"
elif update-alternatives --list java 2>/dev/null | grep -q "java-17-openjdk"; then
    JAVA_17_FOUND=true
    echo "   ✅ Java 17 found via update-alternatives"
    # Set Java 17 for this session
    export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
    export PATH="$JAVA_HOME/bin:$PATH"
else
    echo "   ❌ Java 17 not found"
    echo "   📦 Installing Java 17..."
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y openjdk-17-jdk
        # Set Java 17 for this session
        export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
        export PATH="$JAVA_HOME/bin:$PATH"
        JAVA_17_FOUND=true
    else
        echo "   ❌ Cannot install Java 17 automatically on this system"
        echo "   Please install OpenJDK 17 manually"
        exit 1
    fi
fi

# Verify Java version
echo "   Current Java version:"
java -version 2>&1 | head -n 1 | sed 's/^/     /'

if ! command_exists mvn; then
    echo "❌ Maven is required but not installed"
    echo "   Installing Maven..."
    if command_exists apt-get; then
        sudo apt-get install -y maven
    else
        echo "   ❌ Cannot install Maven automatically"
        echo "   Please install Maven manually"
        exit 1
    fi
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

# Check if already built
if [[ -f "target/discord-mcp-0.0.1-SNAPSHOT.jar" ]]; then
    echo "   ✅ Discord MCP already built, skipping..."
else
    echo "   Building with Maven..."
    mvn clean package -DskipTests
    if [[ -f "target/discord-mcp-0.0.1-SNAPSHOT.jar" ]]; then
        echo "   ✅ Discord MCP built successfully"
    else
        echo "   ❌ Discord MCP build failed"
    fi
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

# Check if already built (Note: Linear uses build/ not dist/)
if [[ -f "build/index.js" ]]; then
    echo "   ✅ Linear MCP already built, skipping..."
else
    echo "   Installing dependencies..."
    npm install
    echo "   Building..."
    npm run build
    if [[ -f "build/index.js" ]]; then
        echo "   ✅ Linear MCP built successfully"
    else
        echo "   ❌ Linear MCP build failed"
    fi
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

# Check if already built
if [[ -f "dist/index.js" ]]; then
    echo "   ✅ Gmail MCP already built, skipping..."
else
    echo "   Installing dependencies..."
    npm install
    echo "   Building..."
    npm run build
    if [[ -f "dist/index.js" ]]; then
        echo "   ✅ Gmail MCP built successfully"
    else
        echo "   ❌ Gmail MCP build failed"
    fi
fi
cd ..

# Continue to next MCP installation...

echo ""
echo "🎉 MCP Server Installation Complete!"
echo "==================================="
echo ""
echo "Installed servers in: $MCP_DIR"
echo ""
echo "📋 Next steps:"
echo "1. Update infrastructure config with correct MCP paths"
echo "2. Run generate_mcp_config.py to generate MCP configuration"
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

# Restore original JAVA_HOME if it was set (POSS-95)
if [[ -n "$ORIGINAL_JAVA_HOME" ]]; then
    echo ""
    echo "🔄 Restoring original JAVA_HOME: $ORIGINAL_JAVA_HOME"
    export JAVA_HOME="$ORIGINAL_JAVA_HOME"
    export PATH="$ORIGINAL_JAVA_HOME/bin:$PATH"
fi

echo "✅ Done!"
