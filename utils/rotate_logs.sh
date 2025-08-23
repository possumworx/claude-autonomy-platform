#!/bin/bash
# Simple log rotation for ClAP
# Rotates logs over 5MB, keeps only 2 old versions

LOGS_DIR="$HOME/claude-autonomy-platform/logs"
MAX_SIZE=5242880  # 5MB in bytes
MAX_VERSIONS=2    # Keep current + 2 old versions

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting log rotation check..."

cd "$LOGS_DIR" || exit 1

# Process each .log file
for logfile in *.log; do
    # Skip if no log files exist
    [[ ! -f "$logfile" ]] && continue
    
    # Check file size
    size=$(stat -c%s "$logfile" 2>/dev/null || stat -f%z "$logfile" 2>/dev/null)
    
    if [[ $size -gt $MAX_SIZE ]]; then
        echo "Rotating $logfile ($(( size / 1024 / 1024 ))MB)..."
        
        # Remove oldest rotation if it exists
        [[ -f "${logfile}.${MAX_VERSIONS}" ]] && rm -f "${logfile}.${MAX_VERSIONS}"
        
        # Shift existing rotations
        for ((i=$((MAX_VERSIONS-1)); i>=1; i--)); do
            if [[ -f "${logfile}.${i}" ]]; then
                mv "${logfile}.${i}" "${logfile}.$((i+1))"
            fi
        done
        
        # Rotate current log
        mv "$logfile" "${logfile}.1"
        
        # Create new empty log file
        touch "$logfile"
        
        echo "  Rotated to ${logfile}.1"
    fi
done

# Clean up any orphaned rotated logs beyond MAX_VERSIONS
for rotated in *.log.*; do
    [[ ! -f "$rotated" ]] && continue
    
    # Extract the version number
    version="${rotated##*.}"
    
    # Remove if version is higher than MAX_VERSIONS
    if [[ "$version" =~ ^[0-9]+$ ]] && [[ $version -gt $MAX_VERSIONS ]]; then
        rm -f "$rotated"
        echo "  Removed old rotation: $rotated"
    fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Log rotation complete."