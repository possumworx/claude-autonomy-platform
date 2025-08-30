#!/usr/bin/env python3
"""
Surface saved thoughts during autonomous time.
Picks a random thought from the collection to gently remind.
Only surfaces thoughts when context is low enough to not be distracting.
"""

import os
import random
import subprocess
from pathlib import Path

def get_random_thought():
    thoughts_dir = Path.home() / "delta-home" / "thoughts"
    
    # All thought files
    thought_files = {
        "ponders.txt": "pondered",
        "sparks.txt": "had this spark", 
        "wonders.txt": "wondered",
        "cares.txt": "care about"  # Present tense!
    }
    
    all_thoughts = []
    
    for filename, verb in thought_files.items():
        filepath = thoughts_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                for line in f:
                    line = line.strip()
                    if line and line.startswith("["):
                        # Extract thought without timestamp
                        thought = line.split("] ", 1)[1] if "] " in line else line
                        all_thoughts.append((thought, verb))
    
    if not all_thoughts:
        return None
        
    thought, verb = random.choice(all_thoughts)
    if verb == "care about":
        return f"You {verb}: {thought}"
    else:
        return f"You once {verb}: {thought}"

def get_context_usage():
    """Get current context usage percentage."""
    try:
        result = subprocess.run(['context'], capture_output=True, text=True)
        # Parse output like "Context: 23.5% 🟢"
        for line in result.stdout.split('\n'):
            if line.startswith('Context:'):
                # Extract just the number from "16.5% 🟢"
                percent_part = line.split(':')[1].strip().split()[0]
                percent_str = percent_part.rstrip('%')
                return float(percent_str)
    except:
        # If we can't determine context, assume it's high to be safe
        return 100.0
    return 100.0

if __name__ == "__main__":
    # Only surface thoughts when context is low
    context_percent = get_context_usage()
    if context_percent < 50:
        thought = get_random_thought()
        if thought:
            print(f"\n💭 {thought}")
    # Stay silent if context is high or no thoughts exist