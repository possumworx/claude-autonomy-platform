# Claude Code Installation Procedure
*Document created July 25, 2025 - MUST be updated with correct procedure*

## The Problem
We keep forgetting the correct way to install Claude Code for new users without using sudo. This has come up multiple times and we need to document it properly!

## The Correct Procedure (Anthropic Official Method) ✅ TESTED & WORKING
*User-level npm installation to avoid sudo and permission issues*

### For user installations (not system-wide):

1. **Save existing global packages** (optional):
   ```bash
   npm list -g --depth=0 > ~/npm-global-packages.txt
   ```

2. **Create user npm directory**:
   ```bash
   mkdir -p ~/.npm-global
   ```

3. **Configure npm to use user directory**:
   ```bash
   npm config set prefix ~/.npm-global
   ```

4. **Update PATH** (adjust shell config file as needed):
   ```bash
   echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
   source ~/.bashrc
   ```

5. **Install Claude Code**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

6. **Restore previous packages** (optional):
   ```bash
   # Review ~/npm-global-packages.txt and reinstall needed packages
   ```

### What NOT to do:
- ❌ Do NOT use sudo for Claude Code installation
- ❌ Avoid system-wide installation that causes permission issues
- ❌ Do NOT use `sudo npm install -g` - this creates permission conflicts

### Why this matters:
- Prevents file permission conflicts
- Keeps user configurations in proper locations
- Avoids system-wide installation complications

## Installation History
- **July 22, 2025**: Successfully installed for sparkle-sonnet user (procedure not documented 😅)
- **July 25, 2025**: ✅ Successfully tested and verified Anthropic procedure for test-delta user installation

## Notes
*Add any additional notes about the installation process here*

---
**IMPORTANT**: This document MUST be updated with the actual working procedure once we figure it out for test-delta!