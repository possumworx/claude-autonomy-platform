# Linear Removal - Complete Action List
**Prepared by Quill 🪶 - January 20, 2026**

## Files Created (ready to use)

### In the repo:
1. `linear/DEPRECATED_README.md` - Documentation of the command interface for Leantime reuse

### New versions of config files:
2. `config/natural_commands.sh.new` - Linear aliases removed, TODO placeholder added
3. `config/claude_aliases.sh.new` - Linear aliases removed, broken refs fixed, TODO placeholder added

---

## Manual Actions Needed (Amy to run)

### Step 1: Move Linear to old/
```powershell
cd C:\Users\Amy\Documents\GitHub\claude-autonomy-platform

# Move the linear folder
Move-Item -Path linear -Destination old\linear

# Move Linear-specific docs
Move-Item -Path docs\linear-vscode-guide.md -Destination old\linear\
Move-Item -Path setup\setup-linear-integration.sh -Destination old\linear\
```

### Step 2: Replace config files
```powershell
# Backup originals (optional)
Copy-Item config\natural_commands.sh config\natural_commands.sh.backup
Copy-Item config\claude_aliases.sh config\claude_aliases.sh.backup

# Replace with new versions
Move-Item -Force config\natural_commands.sh.new config\natural_commands.sh
Move-Item -Force config\claude_aliases.sh.new config\claude_aliases.sh
```

### Step 3: Update clap_architecture.md (manual edits needed)

The following sections reference Linear and should be updated:

**Section: "Recent Updates (v0.6.0)"** (~lines 20-50)
- Remove or archive the v0.6.0 Linear workflow commands section
- Keep other v0.6.0 updates if any

**Section: "Recent Updates (v0.5.4)"** (~lines 50-70)
- Remove "Added comprehensive Linear CLI" bullet point
- Remove "Project-specific commands dynamically generated" bullet point

**Section: "Recent Updates (v0.5.3)"** (~lines 70-90)
- Remove "Linear Natural Commands" section entirely
- Keep "Thought Preservation System" and other bullets

**Section: "MCP Servers" (Section 6)**
- Remove: `- linear: Task management integration. https://linear.app/docs/mcp`

**Section: "Natural Commands" (Section 8)**
- Remove: `- Linear commands: linear/ directory`
- Remove: `- **Linear Integration**: linear-issues, linear-commands, init, sync_projects - Natural language interface to Linear MCP`
- Update "Command Categories" to remove "Project management (Linear integration)"

**Section: "5. Linear Integration System (Enhanced v0.6.0)"** (~lines 500-570)
- DELETE THIS ENTIRE SECTION (it's ~70 lines)

**Section: "Future Enhancements"**
- Change "Tracked in Linear." to "Tracked in Leantime." (or remove)

**Embedded tree (between TREE_START and TREE_END)**
- Remove the `linear/` directory listing
- Remove `linear_state.json` from data/
- Remove `linear-vscode-guide.md` from docs/
- Remove `setup-linear-integration.sh` from setup/
- Remove `linear`, `linear-helpers`, `linear-issues`, `my-linear-issues` from utils/

---

## Also Consider (lower priority)

### Files in utils/ that reference Linear:
These may be symlinks or stubs that can be removed:
- `utils/linear` 
- `utils/linear-helpers`
- `utils/linear-issues`
- `utils/my-linear-issues`

Check if they exist and remove if so.

### State files on deployed systems:
When deploying, remember to clean up:
- `data/linear_state.json`
- `data/linear_prefs.json`

---

## Verification

After completing the above, run the dependency mapper again:
```bash
python utils/dependency_mapper.py --topology
```

The Linear-related orphans and broken references should be gone.

---

*Good luck! The codebase will be much cleaner after this. 🪶*
