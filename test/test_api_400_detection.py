#!/usr/bin/env python3
"""Test script for API 400 error detection"""

import sys
import re
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from core.autonomous_timer import detect_api_errors

# Test cases for API 400 errors
test_cases = [
    # API 400 error in pink text
    ("[35mAPI error: 400 Bad Request[0m", True),
    ("[95mError: 400 error occurred[0m", True),
    ("[35mBad request error detected[0m", True),
    
    # API 500 error (should not match as 400)
    ("[35mAPI error: 500 Internal Server Error[0m", False),
    
    # Regular text (should not match)
    ("Normal console output", False),
    
    # Other API errors
    ("[35mAPI error: 404 Not Found[0m", False),
]

print("Testing API 400 error detection...")
print("-" * 50)

for test_input, should_detect_400 in test_cases:
    result = detect_api_errors(test_input)
    
    is_400 = result and result.get("error_type") == "api_400_error"
    passed = is_400 == should_detect_400
    
    print(f"Input: {test_input[:50]}...")
    print(f"Expected 400: {should_detect_400}, Got 400: {is_400}")
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    if result:
        print(f"Detected: {result['error_type']} - {result['details']}")
    print("-" * 50)