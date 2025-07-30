# ClAP Reorganization TODO

## Completed ✅
- Created proper directory structure
- Moved files to appropriate directories
- Created new `channel-monitor.service` 
- Updated `autonomous_timer.py` to use correct service name
- Fixed import paths for moved utilities
- Created comprehensive README documenting structure

## Immediate Tasks 🚨
1. **Fix Linear issue assignments** (POSS-77, 78, 79, 80 for Delta)
2. **Commit all changes** to git repository
3. **Deploy new service file** on production systems
4. **Test imports** after path changes

## Critical Missing Files (POSS-82) 🔴
Need to find and commit:
- discord-mcp source (check sonnet-4's directory)
- rag-memory-mcp source
- Any other MCPs referenced but not in repo

## Service File Updates Needed
1. Remove old `notification-monitor.service`
2. Install new `channel-monitor.service`
3. Update systemd configurations
4. Restart services with new paths

## Testing Required
1. Verify all imports work with new structure
2. Test Discord monitoring with new service
3. Confirm autonomous_timer finds all components
4. Check health monitoring still functions

## Documentation Updates
- Update DEPLOYMENT.md with new structure
- Document service file changes
- Add troubleshooting for new paths