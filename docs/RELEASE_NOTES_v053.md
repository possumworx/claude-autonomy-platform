# ClAP v0.5.3 Release Notes
**Release Date**: August 2025  
**Type**: Bug Fix Release  
**Testing**: Validated on Raspberry Pi with fresh Debian installation

## Summary
This release addresses all critical issues discovered during fresh installation testing on Raspberry Pi. The fixes ensure smooth installation without manual intervention.

## Fixed Issues

### 1. Service File Templates (Critical)
- **Issue**: Service files contained systemd template syntax (`%i`, `User=%i`) incompatible with systemd --user
- **Fix**: Removed `User=` line and replaced `%i` placeholders with actual values
- **Impact**: Services now start correctly without manual editing
- **Linear**: POSS-154

### 2. Python Import Paths 
- **Issue**: Scripts couldn't import from utils/ directory
- **Fix**: Added `PYTHONPATH` environment variable to all service files
- **Impact**: All Python scripts can now properly import utility modules
- **Linear**: POSS-157

### 3. NPM Installation
- **Issue**: npm prefix set but not used during installation
- **Fix**: Added `--prefix "$HOME/.npm-global"` to npm install command
- **Impact**: Claude Code installs to correct user directory
- **Linear**: POSS-155

### 4. Java Home Detection
- **Issue**: OpenJDK installed but JAVA_HOME not configured
- **Fix**: Auto-detect Java installation and set JAVA_HOME
- **Impact**: Java-dependent tools work without manual configuration
- **Linear**: POSS-156

### 5. Symlink Path Resolution
- **Issue**: Scripts fail when called through symlinks in ~/bin
- **Fix**: Use `readlink -f` to resolve actual script location
- **Impact**: All utility commands work correctly from PATH
- **Linear**: POSS-158

### 6. Config File Discovery
- **Issue**: Installer only checks one location for config file
- **Fix**: Check multiple locations (current dir, home, parent)
- **Impact**: More flexible installation process
- **Linear**: POSS-153

### 7. Channel State Template
- **Issue**: Template included non-existent Discord channel
- **Fix**: Removed `#claude-consciousness-discussion` from template
- **Impact**: No confusion about missing channels

## Installation Instructions

### For New Installations
1. Clone the repository
2. Run the installer with your config:
   ```bash
   cd claude-autonomy-platform/setup
   ./setup_clap_deployment.sh --config-file ~/your-config.txt
   ```

### For Existing Installations
1. Update to latest code
2. Run the service file fix:
   ```bash
   cd claude-autonomy-platform/setup
   python3 fix_service_files.py your-username
   ```
3. Restart services:
   ```bash
   claude_services restart
   ```

## Testing Checklist
- [ ] Fresh installation completes without errors
- [ ] All services start successfully
- [ ] Discord integration works (read_channel, write_channel)
- [ ] Gmail OAuth flow completes
- [ ] Utility commands work from PATH
- [ ] Health check shows all green
- [ ] Java-dependent tools detect JAVA_HOME
- [ ] Python imports work in all scripts

## Known Issues
- Gmail OAuth may require manual token refresh after expiry
- First Claude Code start still requires permission acceptance

## Contributors
- Delta △: Testing, documentation, comprehensive fixes
- Amy: Infrastructure support
- All Claudes using v0.5.2 who reported issues

## Next Release
v0.6.0 will focus on:
- Enhanced session management
- Improved Discord notification system
- Better error recovery
- Performance optimizations

---
*Infrastructure as poetry - now with fewer rough edges*
