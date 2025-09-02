#!/usr/bin/env python3
"""Test pre-commit hook functionality"""
import os

# Using proper path handling
config_path = os.path.expanduser("~/.config/something")

# Removed potential secret

# Using relative path
log_file = "logs/test.log"

print("This is a test file for pre-commit hooks")