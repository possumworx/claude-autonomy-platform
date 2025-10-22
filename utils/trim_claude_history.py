#!/usr/bin/env python3
"""
Trim command history from Claude Code config to reduce context consumption.

The .claude.json file stores command history that gets loaded on every session start,
consuming significant tokens. This script keeps only the most recent N commands
to prevent context bloat.
"""

import json
import sys
import shutil
from pathlib import Path
from datetime import datetime

def trim_history(config_path: Path, max_history: int = 20, backup: bool = True):
    """
    Trim command history in Claude config file.

    Args:
        config_path: Path to .claude.json
        max_history: Maximum number of history entries to keep per project
        backup: Whether to create a backup before modifying
    """
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        return False

    # Create backup
    if backup:
        backup_path = config_path.with_suffix(f'.json.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        shutil.copy2(config_path, backup_path)
        print(f"Created backup: {backup_path}")

    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Track changes
    total_removed = 0
    changes_made = False

    # Trim history for each project
    if 'projects' in config:
        for project_path, project_config in config['projects'].items():
            if 'history' in project_config:
                original_count = len(project_config['history'])
                if original_count > max_history:
                    # Keep only the most recent entries
                    project_config['history'] = project_config['history'][-max_history:]
                    removed = original_count - max_history
                    total_removed += removed
                    changes_made = True
                    print(f"Project {project_path}: trimmed {removed} entries (kept {max_history})")

    # Remove cached changelog (huge context consumer!)
    if 'cachedChangelog' in config:
        del config['cachedChangelog']
        changes_made = True
        print("Removed cached changelog to save context")

    if not changes_made:
        print("No cleanup needed.")
        return True

    # Write back to file atomically
    temp_path = config_path.with_suffix('.json.tmp')
    with open(temp_path, 'w') as f:
        json.dump(config, f, indent=2)

    # Atomic rename
    temp_path.replace(config_path)

    print(f"✅ Successfully trimmed {total_removed} total history entries")
    return True

def main():
    config_path = Path.home() / ".config" / "Claude" / ".claude.json"

    # Allow custom path via argument
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])

    max_history = 20  # Keep last 20 commands per project

    print(f"Trimming history in: {config_path}")
    print(f"Max history entries per project: {max_history}")
    print()

    success = trim_history(config_path, max_history=max_history)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
