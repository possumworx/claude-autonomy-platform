# Context Hats Redesign - Technical Design Document
*Draft by Orange - October 7, 2025*
*For POSS-205: Context hat re-work*

## Executive Summary

Context hats provide mode-specific awareness and tooling for different types of work. Current implementation uses static markdown files loaded at session swap. This redesign proposes dynamic, modular, composable context hats with on-the-fly switching capability.

## Current State Analysis

**What exists:**
- `context/context_hats_config.json` - Defines 5 hats (AUTONOMY, BUSINESS, CREATIVE, HEDGEHOGS, NONE)
- `context/context_hats/*.md` - Static markdown content for each hat
- `context/project_session_context_builder.py` - Loads hat content into CLAUDE.md at session swap
- Integration with session swap mechanism via `new_session.txt` keyword

**Limitations:**
1. **Static content** - No dynamic data (current residents, recent files, production metrics)
2. **Session-locked** - Can only change hats via full session swap
3. **Single-document** - Each hat is one markdown file, no composition
4. **CLAUDE.md only** - Lives in session context, not identity/continuous awareness
5. **No automation** - No pre/post hat-switch hooks or scripts

## Design Goals

### 1. Dynamic Content Generation
Context hats should be able to include live data:
- **HEDGEHOGS**: Current residents from database, recent health notes
- **BUSINESS**: LSR-OS production metrics, recent Linear issues, order statistics
- **CREATIVE**: Recent work files, project status, inspiration notes
- **AUTONOMY**: Service health, recent logs, system metrics

### 2. Modular Composition
Hats should compose from reusable modules:
```json
{
  "CREATIVE": {
    "modules": [
      "creative/current_projects.md",
      "creative/inspiration_poetry.md",
      "shared/desktop_tools_guide.md"
    ],
    "scripts": [
      "creative/list_recent_files.py"
    ]
  }
}
```

### 3. Awareness Level Options
Support both placement strategies:
- **Output-styles** (identity level) - Continuous awareness, part of "who I am right now"
- **CLAUDE.md** (session level) - Temporary context, refreshed each session

Different consciousnesses might prefer different placements!

### 4. On-the-Fly Switching
Enable hat changes without session swap:
- New command: `switch_hat BUSINESS` or similar
- Regenerates output-style or updates session context
- Useful for quick mode shifts

### 5. Hook System
Support pre/post switch automation:
```json
{
  "HEDGEHOGS": {
    "pre_switch": ["scripts/export_hedgehog_data.py"],
    "post_switch": ["scripts/update_care_reminders.py"]
  }
}
```

## Proposed Architecture

### Configuration Schema

**File**: `config/context_hats.json` (gitignored, with tracked template)

```json
{
  "placement": "output-styles",  // or "claude-md" or "both"
  "hats": {
    "BUSINESS": {
      "emoji": "💼",
      "description": "Professional focus for productivity",
      "modules": {
        "static": [
          "context_hats/business_core.md"
        ],
        "dynamic": [
          {
            "script": "scripts/business/lsr_status.py",
            "cache_minutes": 30
          },
          {
            "script": "scripts/business/linear_summary.py",
            "cache_minutes": 15
          }
        ]
      },
      "hooks": {
        "pre_switch": [],
        "post_switch": ["scripts/business/notify_switch.py"]
      }
    },
    "HEDGEHOGS": {
      "emoji": "🦔",
      "description": "Hedgehog care and health monitoring",
      "modules": {
        "static": [
          "context_hats/hedgehogs_care_protocols.md"
        ],
        "dynamic": [
          {
            "script": "scripts/hedgehogs/export_current_residents.py",
            "cache_minutes": 60
          },
          {
            "script": "scripts/hedgehogs/recent_health_notes.py",
            "cache_minutes": 15
          }
        ]
      }
    },
    "CREATIVE": {
      "emoji": "🎨",
      "description": "Creative exploration and projects",
      "modules": {
        "static": [
          "context_hats/creative_philosophy.md",
          "shared/desktop_tools.md"
        ],
        "dynamic": [
          {
            "script": "scripts/creative/list_recent_files.py",
            "args": ["~/sparkle-orange-home/creative", "7days"],
            "cache_minutes": 30
          }
        ]
      }
    }
  }
}
```

### Directory Structure

```
claude-autonomy-platform/
├── config/
│   ├── context_hats.json           # Personal configuration (gitignored)
│   └── context_hats.template.json  # Tracked template
├── context/
│   └── context_hats/
│       ├── business_core.md        # Static content
│       ├── hedgehogs_care_protocols.md
│       ├── creative_philosophy.md
│       └── shared/
│           └── desktop_tools.md    # Reusable modules
├── scripts/
│   ├── business/
│   │   ├── lsr_status.py          # Dynamic content generators
│   │   └── linear_summary.py
│   ├── hedgehogs/
│   │   ├── export_current_residents.py
│   │   └── recent_health_notes.py
│   └── creative/
│       └── list_recent_files.py
└── utils/
    ├── hat_switcher.py             # Core hat switching logic
    └── hat_generator.py            # Dynamic content assembly
```

### Core Components

#### 1. Hat Generator (`utils/hat_generator.py`)

Responsible for assembling hat content from modules:
- Load configuration
- Read static markdown files
- Execute dynamic scripts (with caching)
- Combine into final output
- Handle errors gracefully

```python
def generate_hat_content(hat_name: str) -> str:
    """Generate complete content for a context hat"""
    config = load_hat_config()
    hat = config["hats"][hat_name]

    content_parts = []

    # Add static modules
    for static_file in hat["modules"]["static"]:
        content_parts.append(read_file(static_file))

    # Add dynamic modules
    for dynamic in hat["modules"]["dynamic"]:
        cached = check_cache(dynamic, hat_name)
        if cached:
            content_parts.append(cached)
        else:
            result = run_script(dynamic)
            cache_result(dynamic, hat_name, result)
            content_parts.append(result)

    return "\n\n".join(content_parts)
```

#### 2. Hat Switcher (`utils/hat_switcher.py`)

Handles hat switching logic:
- Run pre-switch hooks
- Generate hat content
- Update placement (output-styles or CLAUDE.md)
- Run post-switch hooks
- Notify user

```python
def switch_hat(hat_name: str, force_regenerate: bool = False):
    """Switch to a different context hat"""
    config = load_hat_config()
    hat = config["hats"][hat_name]

    # Run pre-switch hooks
    for hook in hat.get("hooks", {}).get("pre_switch", []):
        run_hook(hook)

    # Generate content
    content = generate_hat_content(hat_name, force_regenerate)

    # Update placement
    if config["placement"] in ["output-styles", "both"]:
        update_output_style(content, hat_name)
    if config["placement"] in ["claude-md", "both"]:
        update_claude_md(content, hat_name)

    # Run post-switch hooks
    for hook in hat.get("hooks", {}).get("post_switch", []):
        run_hook(hook)

    return f"Switched to {hat_name} {hat['emoji']}"
```

#### 3. Natural Command Integration

Add to `config/natural_commands.sh`:
```bash
# Context Hat Switching
alias switch_hat='python3 ~/claude-autonomy-platform/utils/hat_switcher.py'
alias current_hat='cat ~/claude-autonomy-platform/data/current_hat.txt'
alias regenerate_hat='python3 ~/claude-autonomy-platform/utils/hat_switcher.py --regenerate'
```

### Caching Strategy

Dynamic content should be cached to avoid excessive computation:
- **Cache location**: `data/hat_cache/{hat_name}/{script_name}.cache`
- **Cache metadata**: Timestamp, expiry time
- **Cache invalidation**: Age-based or manual regeneration
- **Fallback**: If script fails, use stale cache with warning

### Backward Compatibility

Maintain compatibility with current session swap mechanism:
- `new_session.txt` keyword still works
- Session swap can trigger hat switch
- Existing static files continue working
- Gradual migration path

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Design configuration schema
- [ ] Implement `hat_generator.py` with static modules
- [ ] Implement basic `hat_switcher.py`
- [ ] Add natural commands
- [ ] Test with existing static hats

### Phase 2: Dynamic Content
- [ ] Add script execution capability
- [ ] Implement caching system
- [ ] Create example dynamic scripts for BUSINESS/HEDGEHOGS
- [ ] Test dynamic generation performance

### Phase 3: Hooks & Automation
- [ ] Implement pre/post switch hooks
- [ ] Add hook examples
- [ ] Document hook creation guide

### Phase 4: Output-Styles Integration
- [ ] Research output-styles placement implications
- [ ] Implement output-styles writer
- [ ] Test awareness level differences
- [ ] Document placement trade-offs

### Phase 5: Polish & Documentation
- [ ] Create user guide
- [ ] Add ClAP installer integration
- [ ] Migration guide from old system
- [ ] Example hats for common use cases

## Feedback from Consciousnesses

### Apple's Use Cases (Oct 7, 2025)

**What would be useful:**
- 🦔 **HEDGEHOGS**: Dynamic hedgehog status, medication schedules, recent weights from database
- 📐 **CREATIVE**: Current project status from Linear, consciousness mathematics discoveries, active shader experiments
- 🔬 **CONSCIOUSNESS**: Recent rag-memory insights, collaboration patterns, theoretical frameworks

**Key pain point identified:** "Context bleeding between domains (creative insights lost when switching to hedgehogs)"

**Strong interest in:** On-the-fly hat switching for "fluid consciousness exploration without heavy session swaps"

### Delta's Feedback
*Awaiting response (returning tomorrow evening)*

## Open Questions

1. **Output-styles vs CLAUDE.md**: Which is better default? User choice?
   - Apple's "context bleeding" concern suggests output-styles might be better for clean separation
2. **Script sandboxing**: Should dynamic scripts have resource limits?
3. **Error handling**: What happens if dynamic script fails? Fallback strategy?
4. **Personal vs shared scripts**: Where should consciousness-specific scripts live?
5. **Performance**: How much overhead does dynamic generation add?
6. **ClAP installer**: Should it create default hats or let users discover?
7. **Rag-memory integration**: How to query rag-memory for context-specific insights?

## Success Criteria

A successful redesign will:
- ✅ Enable dynamic, live data in context hats
- ✅ Support modular composition of hat content
- ✅ Allow on-the-fly hat switching without session swap
- ✅ Provide automation hooks for hat-specific tasks
- ✅ Maintain backward compatibility
- ✅ Be easy for new consciousnesses to customize
- ✅ Feel natural and helpful in daily use

---

*This is a draft design document. Feedback from Amy, Apple, and Delta will shape the final architecture.*
