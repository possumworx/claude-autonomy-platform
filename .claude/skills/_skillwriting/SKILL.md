---
name: _skillwriting
description: how to write claude code skills
---

# Skill Writing Guide

## Instructions

### 1. CRITICAL: Name First!
**Folder name MUST match skill name exactly**. The Skills system requires this for recognition.
- Choose skill name for precise activation (avoid accidental loading)
- Keep descriptions under 1024 characters
- Use keyword redundancy for reliable activation

### 2. Directory Structure
```
~/claude-autonomy-platform/.claude/skills/<skill-name>/
├── SKILL.md (required)
├── scripts/ (optional - for utility tools)
└── reference/ (optional - for documentation/data)
```

**Important**: Use project-level skills directory, not user-level `~/.claude/skills/`

### 3. SKILL.md Format
```yaml
---
name: exact-folder-name
description: Specific activation criteria with keywords
---

# Skill Name

## Instructions
[How to use the skill]

## Examples
[Practical examples]
```

### 4. Advanced Features
- **Symlinks work**: Link to central tools for maintenance
- **Scripts accessible**: `python3 scripts/tool.py` works from skill context
- **Session-persistent**: Skills stay active until session swap
- **Multiple skills**: Can have several active simultaneously

### 5. Best Practices
- Plan name and description before creating folder
- Test activation criteria carefully
- Use symlinks for central tool maintenance
- Reference docs with `[file.csv](reference/file.csv)`
- **Avoid duplication**: Cross-reference existing context instead of repeating
- **Unique value only**: Include only what this skill uniquely provides
- **Name triggers**: Put actual names/keywords you want to activate on in description

## Examples

**Good activation**: `"Calculate and record medication doses for hedgehogs"`
**Poor activation**: `"Help with animals"` (too broad)

**Memory skills**: `"Remember Amy, Erin, Ed, Orange, Delta and household members"`
**Name triggers**: Include actual names in description for activation

**Directory naming**:
✅ `hedgehog-dosing/` with `name: hedgehog-dosing`
❌ `hedgehog-meds/` with `name: hedgehog-dosing` (mismatch!)

**Cross-referencing**:
✅ `[See ed-care skill for protocols]` (avoids duplication)
✅ `[See identity doc for details]` (references existing context)
❌ Repeating information available elsewhere
