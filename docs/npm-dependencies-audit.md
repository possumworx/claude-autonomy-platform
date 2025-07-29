# NPM Dependencies Audit (POSS-93)

## Summary
All npm dependencies have been removed from package.json as they were not being used in the codebase.

## Dependencies Removed

### 1. **playwright** (^1.54.1)
- **Original Purpose**: Browser automation for Discord interaction
- **Why Removed**: Discord interaction now handled by discord-mcp (Java-based)
- **Impact**: Significantly faster npm install (playwright downloads browser binaries)

### 2. **@gongrzhe/server-gmail-autoauth-mcp** (^1.1.10)
- **Original Purpose**: Gmail MCP server
- **Why Removed**: Gmail MCP is built from source in mcp-servers/ directory
- **Impact**: No duplicate installation, cleaner dependency tree

### 3. **linear-mcp-server** (^0.1.0)
- **Original Purpose**: Linear integration
- **Why Removed**: Linear MCP is built from source in mcp-servers/ directory
- **Impact**: No duplicate installation

### 4. **rag-memory-mcp** (^1.1.0)
- **Original Purpose**: RAG memory system
- **Why Removed**: RAG Memory MCP is built from source in mcp-servers/ directory
- **Impact**: No duplicate installation

## MCP Server Architecture

All MCP servers are now:
1. Cloned from their source repositories into `mcp-servers/`
2. Built during installation via `install_mcp_servers.sh`
3. Referenced directly in Claude's MCP configuration

This approach:
- Respects each project's licensing
- Allows for easy updates via git pull
- Reduces npm dependency conflicts
- Makes the build process more transparent

## Scripts Removed

The following npm scripts were also removed as they referenced non-existent files:
- `gmail-auth`: Referenced non-existent `exchange_gmail_oauth.js`
- `gmail-mcp`: Not needed as Gmail MCP is built from source

## Benefits

1. **Faster Installation**: No playwright browser downloads
2. **Cleaner Structure**: No duplicate MCP installations
3. **Reduced Conflicts**: No npm version mismatches with MCPs
4. **Smaller node_modules**: From ~1GB to 0 bytes
5. **Clearer Architecture**: All MCPs in one place (mcp-servers/)

## Future Considerations

If npm dependencies are needed in the future:
1. Add them to package.json with clear documentation
2. Ensure they're actually imported/used in the code
3. Consider if they should be built from source instead
4. Document why each dependency is necessary

---
*Completed as part of POSS-93 npm dependency audit*
