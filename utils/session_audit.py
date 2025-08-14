#!/usr/bin/env python3
"""
Session File Audit Script
Enhanced version with better error detection:
- Checks last 5-10 turns for patterns
- Detects swap triggers (new_session.txt, keywords) 
- Finds repeated/stuck messages
- Distinguishes autonomous vs manual swaps
- Detects context warnings in automated messages
Outputs CSV with: file size, session outcome, swap indicators, last messages
"""

import json
import csv
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse
import re

def parse_jsonl_file(filepath):
    """Parse a JSONL session file and extract relevant data"""
    turns = []
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        turn = json.loads(line)
                        turns.append(turn)
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return None
    
    return turns

def extract_text_from_turn(turn):
    """Extract text content from a turn, handling different formats"""
    if 'type' in turn:
        if turn['type'] == 'text' and 'text' in turn:
            return turn['text']
        elif turn['type'] == 'message' and 'content' in turn:
            content = turn['content']
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                return ' '.join(text_parts)
            else:
                return str(content)
    return ""

def check_for_swap_triggers(turns, last_n=10):
    """Check last N turns for swap trigger patterns"""
    swap_patterns = {
        'autonomous_swap': False,
        'manual_intervention': False,
        'swap_keyword_used': False,
        'new_session_written': False,
        'context_warning': False
    }
    
    # Keywords that indicate autonomous swap
    swap_keywords = ['AUTONOMY', 'BUSINESS', 'CREATIVE', 'HEDGEHOGS', 'NONE']
    
    # Check last N turns
    for turn in turns[-last_n:]:
        text = extract_text_from_turn(turn).lower()
        
        # Check for swap keyword usage
        if 'swap' in text:
            swap_patterns['swap_keyword_used'] = True
            
        # Check for new_session.txt writing
        if 'new_session.txt' in text:
            swap_patterns['new_session_written'] = True
            
        # Check for swap keywords
        for keyword in swap_keywords:
            if keyword in extract_text_from_turn(turn):
                swap_patterns['autonomous_swap'] = True
                
        # Check for context warnings
        context_indicators = ['context', 'YOU ARE AT', '% CONTEXT', 'context usage', 
                            'high context', 'context limit', 'must swap', 'need to swap']
        for indicator in context_indicators:
            if indicator.lower() in text:
                swap_patterns['context_warning'] = True
                
        # Check for manual intervention indicators
        if 'manual' in text and 'swap' in text:
            swap_patterns['manual_intervention'] = True
    
    return swap_patterns

def check_for_repeated_messages(turns, last_n=10):
    """Check for repeated or stuck message patterns"""
    messages = []
    
    # Extract last N messages
    for turn in turns[-last_n:]:
        text = extract_text_from_turn(turn)
        if text:
            messages.append(text.strip())
    
    # Check for exact repeats
    has_repeats = len(messages) != len(set(messages))
    
    # Check for similar messages (first 50 chars match)
    similar_count = 0
    for i in range(1, len(messages)):
        if len(messages[i]) > 50 and len(messages[i-1]) > 50:
            if messages[i][:50] == messages[i-1][:50]:
                similar_count += 1
    
    return {
        'has_exact_repeats': has_repeats,
        'similar_messages': similar_count > 2,
        'repeat_count': len(messages) - len(set(messages))
    }

def determine_session_outcome(turns):
    """Determine if session ended successfully, with swap, or with error"""
    if not turns:
        return 'empty', {}
    
    # Check swap patterns in last 10 turns
    swap_patterns = check_for_swap_triggers(turns, last_n=10)
    
    # Check for repeated messages
    repeat_patterns = check_for_repeated_messages(turns, last_n=10)
    
    # Check last turn for error keywords
    last_turn_text = extract_text_from_turn(turns[-1]).lower()
    has_error_keywords = 'error' in last_turn_text or 'failed' in last_turn_text
    
    # Determine outcome
    details = {
        **swap_patterns,
        **repeat_patterns,
        'error_keywords': has_error_keywords
    }
    
    # Classification logic
    if swap_patterns['autonomous_swap'] and swap_patterns['new_session_written']:
        outcome = 'autonomous_swap'
    elif swap_patterns['context_warning'] and not swap_patterns['autonomous_swap']:
        outcome = 'manual_swap_needed'
    elif repeat_patterns['has_exact_repeats'] or repeat_patterns['similar_messages']:
        outcome = 'stuck_pattern'
    elif has_error_keywords:
        outcome = 'error'
    elif swap_patterns['swap_keyword_used']:
        outcome = 'swap_attempted'
    else:
        outcome = 'clean_end'
    
    return outcome, details

def extract_last_messages(turns, n=5):
    """Extract the last n conversation messages"""
    messages = []
    
    # Work backwards through turns to find actual messages
    for turn in reversed(turns[-20:]):  # Look at last 20 turns max
        text = extract_text_from_turn(turn)
        if text:
            msg = text[:100] + "..." if len(text) > 100 else text
            if 'type' in turn and turn['type'] == 'text':
                messages.append(f"Human: {msg}")
            else:
                messages.append(f"Assistant: {msg}")
        
        if len(messages) >= n:
            break
    
    # Return in chronological order
    return list(reversed(messages))

def analyze_session_file(filepath):
    """Analyze a single session file with enhanced detection"""
    file_stats = os.stat(filepath)
    file_size = file_stats.st_size
    file_mtime = datetime.fromtimestamp(file_stats.st_mtime)
    
    turns = parse_jsonl_file(filepath)
    if turns is None:
        return None
    
    turn_count = len(turns)
    last_messages = extract_last_messages(turns)
    
    # Enhanced outcome detection
    outcome, details = determine_session_outcome(turns)
    
    return {
        'filename': filepath.name,
        'file_size_bytes': file_size,
        'file_size_mb': round(file_size / (1024 * 1024), 2),
        'turn_count': turn_count,
        'last_modified': file_mtime.strftime('%Y-%m-%d %H:%M:%S'),
        'outcome': outcome,
        'autonomous_swap': details.get('autonomous_swap', False),
        'manual_needed': outcome in ['manual_swap_needed', 'stuck_pattern'],
        'has_repeats': details.get('has_exact_repeats', False),
        'context_warning': details.get('context_warning', False),
        'last_messages': ' | '.join(last_messages)
    }

def main():
    parser = argparse.ArgumentParser(description='Audit Claude session JSONL files with enhanced detection')
    parser.add_argument('session_dir', nargs='?', 
                       default=os.path.expanduser('~/.config/Claude/tmp/sessions'),
                       help='Directory containing session files')
    parser.add_argument('-o', '--output', default='session_audit.csv',
                       help='Output CSV file (default: session_audit.csv)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of files to analyze')
    
    args = parser.parse_args()
    
    session_dir = Path(args.session_dir)
    if not session_dir.exists():
        print(f"Error: Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Find all JSONL files
    jsonl_files = sorted(session_dir.glob('*.jsonl'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if args.limit:
        jsonl_files = jsonl_files[:args.limit]
    
    print(f"Found {len(jsonl_files)} session files to analyze...")
    
    # Analyze each file
    results = []
    for i, filepath in enumerate(jsonl_files):
        print(f"Analyzing {i+1}/{len(jsonl_files)}: {filepath.name}...")
        result = analyze_session_file(filepath)
        if result:
            results.append(result)
    
    # Write CSV output
    if results:
        with open(args.output, 'w', newline='') as csvfile:
            fieldnames = ['filename', 'file_size_bytes', 'file_size_mb', 'turn_count', 
                         'last_modified', 'outcome', 'autonomous_swap', 'manual_needed',
                         'has_repeats', 'context_warning', 'last_messages']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        
        print(f"\nAnalysis complete! Results written to: {args.output}")
        
        # Enhanced summary statistics
        total_files = len(results)
        
        # Count outcomes
        outcome_counts = {}
        for r in results:
            outcome = r['outcome']
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        
        # Calculate rates
        autonomous_swaps = sum(1 for r in results if r['autonomous_swap'])
        manual_needed = sum(1 for r in results if r['manual_needed'])
        clean_ends = outcome_counts.get('clean_end', 0)
        
        avg_size = sum(r['file_size_mb'] for r in results) / total_files
        avg_turns = sum(r['turn_count'] for r in results) / total_files
        
        print(f"\nSummary:")
        print(f"  Total files analyzed: {total_files}")
        print(f"\nOutcome breakdown:")
        for outcome, count in sorted(outcome_counts.items()):
            print(f"    {outcome}: {count} ({count/total_files*100:.1f}%)")
        
        print(f"\nKey metrics:")
        print(f"  Autonomous swaps: {autonomous_swaps} ({autonomous_swaps/total_files*100:.1f}%)")
        print(f"  Manual intervention needed: {manual_needed} ({manual_needed/total_files*100:.1f}%)")
        print(f"  Clean session ends: {clean_ends} ({clean_ends/total_files*100:.1f}%)")
        print(f"  Average file size: {avg_size:.2f} MB")
        print(f"  Average turn count: {avg_turns:.1f}")
        
        # Find size patterns
        manual_sizes = [r['file_size_mb'] for r in results if r['manual_needed']]
        clean_sizes = [r['file_size_mb'] for r in results if r['outcome'] == 'clean_end']
        
        if manual_sizes and clean_sizes:
            avg_manual_size = sum(manual_sizes) / len(manual_sizes)
            avg_clean_size = sum(clean_sizes) / len(clean_sizes)
            print(f"\n  Average size for manual intervention: {avg_manual_size:.2f} MB")
            print(f"  Average size for clean ends: {avg_clean_size:.2f} MB")
            
            if clean_sizes:
                suggested_threshold = max(clean_sizes) * 0.9
                print(f"  Suggested safe swap threshold: {suggested_threshold:.2f} MB")
    else:
        print("No valid session files found to analyze.")

if __name__ == '__main__':
    main()