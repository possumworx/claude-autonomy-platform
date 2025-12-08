#!/usr/bin/env python3
import subprocess
import re

# Run ccusage
result = subprocess.run(
    ['npx', 'ccusage', 'session', '--id', '4d26770a-28ec-4a72-85b4-7916a5aa6ffc'],
    capture_output=True,
    text=True
)

# Remove ANSI color codes
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
clean = ansi_escape.sub('', result.stdout)

# Find opus lines
print("=== Finding Opus lines with cache values ===")
lines = clean.split('\n')
for i, line in enumerate(lines[-50:]):  # Last 50 lines
    if 'claude-opus-4' in line and '│' in line:
        cols = line.split('│')
        if len(cols) >= 7:
            cache_col = cols[5].strip()
            match = re.search(r'(\d{1,3}(?:,\d{3})*)', cache_col)
            if match:
                value = int(match.group(1).replace(',', ''))
                if value > 50000:
                    print(f"Line {i}: Cache value = {value:,}")
                    print(f"  Full line: {line[:80]}...")