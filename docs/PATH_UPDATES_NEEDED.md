# Path Changes Required After Reorganization

## File Movements That Require Code Updates

### Data Files (moved to /data/)
- `channel_state.json` - used by:
  - `discord/channel_monitor_simple.py`
  - `discord/channel_state.py`
  - `discord/read_channel`
  - `core/autonomous_timer.py`
  
- `last_seen_message_id.txt` - used by:
  - `core/autonomous_timer.py`

### Config Files (moved to /config/)
- `claude.env` - used by:
  - All systemd service files
  
### Utility Files (moved to /utils/)
- `claude_paths.py` - imported by:
  - `core/autonomous_timer.py` ✅ (already fixed)
  - Others?
  
- `infrastructure_config_reader.py` - imported by:
  - `core/autonomous_timer.py` ✅ (already fixed)
  - Others?

### Service Files (moved to /services/)
- All `.service` files - referenced by:
  - Setup scripts
  - Documentation

## Scripts That Need Path Updates

### High Priority (Core Functionality)
1. `discord/channel_monitor_simple.py` - Update paths to data/channel_state.json
2. `discord/channel_state.py` - Update paths to data/channel_state.json
3. `discord/read_channel` - Update paths to data/channel_state.json
4. `core/autonomous_timer.py` - Update paths to data files
5. All service files - Update paths to moved scripts

### Medium Priority (Setup/Utils)
1. `setup/setup_clap_deployment.sh` - Update all paths
2. `utils/claude_services.sh` - Update service paths
3. `utils/healthcheck_status.py` - Update import paths

### Low Priority (Documentation)
1. Update all documentation with new paths
2. Update README with new structure

## Testing Required
After making these changes:
1. Test Discord monitoring still works
2. Test autonomous timer finds all files
3. Test all services start correctly
4. Test health checks work
5. Test read_channel command works