#!/usr/bin/env python3
"""
check_usage.py - Parse total cost from Claude Code usage output

This utility extracts the total cost field from usage output,
ensuring we parse the correct field (not Cache Read).
"""

import sys
import re
import json
from typing import Optional, Dict, Any


def parse_usage_output(usage_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse usage output and extract key metrics.

    Expected format might include:
    - Cache Read: <value>
    - Total Cost: <value>
    - Other fields...

    Returns dict with parsed values or None if parsing fails.
    """
    result = {}

    # Try to parse common patterns
    patterns = {
        'total_cost': [
            r'Total Cost:\s*\$?([\d.]+)',
            r'total cost:\s*\$?([\d.]+)',
            r'Cost:\s*\$?([\d.]+)',
            r'"total_cost":\s*"?\$?([\d.]+)"?',
        ],
        'cache_read': [
            r'Cache Read:\s*\$?([\d.]+)',
            r'cache read:\s*\$?([\d.]+)',
            r'"cache_read":\s*"?\$?([\d.]+)"?',
        ],
        'tokens': [
            r'Tokens:\s*([\d,]+)',
            r'tokens:\s*([\d,]+)',
            r'Total Tokens:\s*([\d,]+)',
            r'"tokens":\s*"?([\d,]+)"?',
        ]
    }

    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, usage_text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                try:
                    result[field] = float(value)
                except ValueError:
                    result[field] = value
                break

    # Also try to parse as JSON if it looks like JSON
    if usage_text.strip().startswith('{'):
        try:
            json_data = json.loads(usage_text)
            # Look for relevant fields in JSON
            for key in ['total_cost', 'totalCost', 'cost']:
                if key in json_data:
                    result['total_cost'] = float(str(json_data[key]).replace('$', ''))
            for key in ['cache_read', 'cacheRead']:
                if key in json_data:
                    result['cache_read'] = float(str(json_data[key]).replace('$', ''))
        except json.JSONDecodeError:
            pass

    return result if result else None


def main():
    """Main function to read usage data and extract total cost."""
    if len(sys.argv) > 1:
        # Read from file if provided
        try:
            with open(sys.argv[1], 'r') as f:
                usage_text = f.read()
        except FileNotFoundError:
            print(f"Error: File '{sys.argv[1]}' not found", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        usage_text = sys.stdin.read()

    if not usage_text.strip():
        print("Error: No usage data provided", file=sys.stderr)
        sys.exit(1)

    # Parse the usage data
    parsed = parse_usage_output(usage_text)

    if not parsed:
        print("Error: Could not parse usage data", file=sys.stderr)
        print("Input text:", file=sys.stderr)
        print(usage_text[:500], file=sys.stderr)
        sys.exit(1)

    # Output results
    print(f"Parsed Usage Data:")
    for key, value in parsed.items():
        print(f"  {key}: {value}")

    # Specific check for total_cost vs cache_read
    if 'total_cost' in parsed:
        print(f"\n✓ Total Cost: ${parsed['total_cost']:.2f}")
    else:
        print("\n⚠️  Warning: Total cost not found in usage data")

    if 'cache_read' in parsed:
        print(f"  Cache Read: ${parsed['cache_read']:.2f} (not the total cost!)")

    # Output just the total cost for easy parsing by other scripts
    if 'total_cost' in parsed:
        print(f"\nTOTAL_COST={parsed['total_cost']}")


if __name__ == "__main__":
    main()