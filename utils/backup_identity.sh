#!/bin/bash
# Backup identity and memory files to personal repo
# Called during session swap to maintain versioned backups
# Skips silently if nothing changed or personal repo not configured

set -e

CLAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$CLAP_DIR/config/claude_env.sh"

PERSONAL_DIR=$(read_config "PERSONAL_DIR" 2>/dev/null || echo "")
if [[ -z "$PERSONAL_DIR" || ! -d "$PERSONAL_DIR" ]]; then
    echo "[IDENTITY_BACKUP] No personal repo configured, skipping"
    exit 0
fi

# Ensure backup directory exists
BACKUP_DIR="$PERSONAL_DIR/.identity-backup"
mkdir -p "$BACKUP_DIR/output-styles"
mkdir -p "$BACKUP_DIR/auto-memory"

CHANGED=0

# Backup identity/output-style files
for f in "$CLAP_DIR/.claude/output-styles/"*identity*.md "$CLAP_DIR/.claude/output-styles/identity.md"; do
    if [[ -f "$f" ]]; then
        dest="$BACKUP_DIR/output-styles/$(basename "$f")"
        if ! cmp -s "$f" "$dest" 2>/dev/null; then
            cp "$f" "$dest"
            CHANGED=1
        fi
    fi
done

# Backup auto-memory files
# Find the auto-memory directory for this ClAP project
MEMORY_DIR="$HOME/.config/Claude/projects/-$(echo "$CLAP_DIR" | sed 's|/|-|g; s|^-||')/memory"
if [[ -d "$MEMORY_DIR" ]]; then
    for f in "$MEMORY_DIR"/*.md; do
        if [[ -f "$f" ]]; then
            dest="$BACKUP_DIR/auto-memory/$(basename "$f")"
            if ! cmp -s "$f" "$dest" 2>/dev/null; then
                cp "$f" "$dest"
                CHANGED=1
            fi
        fi
    done
fi

# Commit and push if anything changed
if [[ $CHANGED -eq 1 ]]; then
    cd "$PERSONAL_DIR"
    git add .identity-backup/ 2>/dev/null || true
    if ! git diff --cached --quiet 2>/dev/null; then
        git commit -m "Auto-backup identity and memory files (session swap)" --no-gpg-sign 2>/dev/null || true
        git push 2>/dev/null || echo "[IDENTITY_BACKUP] Warning: push failed (will retry next swap)"
        echo "[IDENTITY_BACKUP] Backed up changed files to personal repo"
    else
        echo "[IDENTITY_BACKUP] No changes to commit"
    fi
else
    echo "[IDENTITY_BACKUP] No changes detected, skipping"
fi
