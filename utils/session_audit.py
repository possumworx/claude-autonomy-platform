#!/usr/bin/env python3
"""
Session File Audit Script
Analyzes JSONL session files to help monitor context usage patterns
Outputs CSV with: file size, last 5 lines of chat, conversation turn count
"""

import json
import csv
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse

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

def extract_last_messages(turns, n=5):
    """Extract the last n conversation messages"""
    messages = []
    
    # Work backwards through turns to find actual messages
    for turn in reversed(turns[-20:]):  # Look at last 20 turns max
        if 'type' in turn:
            if turn['type'] == 'text' and 'text' in turn:
                # Human message
                msg = turn['text'][:100] + "..." if len(turn['text']) > 100 else turn['text']
                messages.append(f"Human: {msg}")
            elif turn['type'] == 'message' and 'content' in turn:
                # Assistant message - handle both string and list content
                content = turn['content']
                if isinstance(content, list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                    msg = ' '.join(text_parts)
                else:
                    msg = str(content)
                
                msg = msg[:100] + "..." if len(msg) > 100 else msg
                messages.append(f"Assistant: {msg}")
        
        if len(messages) >= n:
            break
    
    # Return in chronological order
    return list(reversed(messages))

def analyze_session_file(filepath):
    """Analyze a single session file"""
    file_stats = os.stat(filepath)
    file_size = file_stats.st_size
    file_mtime = datetime.fromtimestamp(file_stats.st_mtime)
    
    turns = parse_jsonl_file(filepath)
    if turns is None:
        return None
    
    turn_count = len(turns)
    last_messages = extract_last_messages(turns)
    
    # Check if session ended with error
    ended_with_error = False
    if turns:
        last_turn = turns[-1]
        if 'error' in str(last_turn).lower() or 'context' in str(last_turn).lower():
            ended_with_error = True
    
    return {
        'filename': filepath.name,
        'file_size_bytes': file_size,
        'file_size_mb': round(file_size / (1024 * 1024), 2),
        'turn_count': turn_count,
        'last_modified': file_mtime.strftime('%Y-%m-%d %H:%M:%S'),
        'last_messages': ' | '.join(last_messages),
        'ended_with_error': ended_with_error
    }

def main():
    parser = argparse.ArgumentParser(description='Audit Claude session JSONL files')
    parser.add_argument('session_dir', nargs='?', 
                       default=os.path.expanduser('~/.config/Claude/tmp/sessions'),
                       help='Directory containing session files (default: ~/.config/Claude/tmp/sessions)')
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
                         'last_modified', 'ended_with_error', 'last_messages']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        
        print(f"\nAnalysis complete! Results written to: {args.output}")
        
        # Print summary statistics
        total_files = len(results)
        error_files = sum(1 for r in results if r['ended_with_error'])
        avg_size = sum(r['file_size_mb'] for r in results) / total_files
        avg_turns = sum(r['turn_count'] for r in results) / total_files
        
        print(f"\nSummary:")
        print(f"  Total files analyzed: {total_files}")
        print(f"  Files ending with error: {error_files}")
        print(f"  Average file size: {avg_size:.2f} MB")
        print(f"  Average turn count: {avg_turns:.1f}")
        
        # Find size threshold for errors
        error_sizes = [r['file_size_mb'] for r in results if r['ended_with_error']]
        success_sizes = [r['file_size_mb'] for r in results if not r['ended_with_error']]
        
        if error_sizes and success_sizes:
            min_error_size = min(error_sizes)
            max_success_size = max(success_sizes)
            print(f"\n  Smallest file with error: {min_error_size:.2f} MB")
            print(f"  Largest successful file: {max_success_size:.2f} MB")
            
            if max_success_size < min_error_size:
                print(f"  Suggested safe threshold: {max_success_size * 0.9:.2f} MB")
    else:
        print("No valid session files found to analyze.")

if __name__ == '__main__':
    main()