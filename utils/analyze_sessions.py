#!/usr/bin/env python3
"""
Analyze session audit CSV files to extract patterns
"""

import csv
import statistics
from pathlib import Path
import argparse

def analyze_csv(filepath):
    """Analyze a session audit CSV file"""
    sessions = []
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sessions.append({
                'size_mb': float(row['file_size_mb']),
                'turns': int(row['turn_count']),
                'outcome': row.get('outcome', row.get('ended_with_error', 'unknown'))
            })
    
    if not sessions:
        return None
    
    # Extract statistics
    sizes = [s['size_mb'] for s in sessions]
    turns = [s['turns'] for s in sessions]
    
    # Size statistics
    size_stats = {
        'count': len(sizes),
        'mean': statistics.mean(sizes),
        'median': statistics.median(sizes),
        'stdev': statistics.stdev(sizes) if len(sizes) > 1 else 0,
        'min': min(sizes),
        'max': max(sizes),
        'percentiles': {
            '25th': sorted(sizes)[len(sizes)//4] if sizes else 0,
            '75th': sorted(sizes)[3*len(sizes)//4] if sizes else 0,
            '90th': sorted(sizes)[9*len(sizes)//10] if sizes else 0,
            '95th': sorted(sizes)[19*len(sizes)//20] if sizes else 0
        }
    }
    
    # Turn statistics
    turn_stats = {
        'mean': statistics.mean(turns),
        'median': statistics.median(turns),
        'min': min(turns),
        'max': max(turns)
    }
    
    # Size buckets
    buckets = {
        '<0.5MB': sum(1 for s in sizes if s < 0.5),
        '0.5-1MB': sum(1 for s in sizes if 0.5 <= s < 1),
        '1-1.5MB': sum(1 for s in sizes if 1 <= s < 1.5),
        '1.5-2MB': sum(1 for s in sizes if 1.5 <= s < 2),
        '2-2.5MB': sum(1 for s in sizes if 2 <= s < 2.5),
        '>2.5MB': sum(1 for s in sizes if s >= 2.5)
    }
    
    # Turns per MB
    turns_per_mb = [t/s for s, t in zip(sizes, turns) if s > 0]
    avg_turns_per_mb = statistics.mean(turns_per_mb) if turns_per_mb else 0
    
    return {
        'size_stats': size_stats,
        'turn_stats': turn_stats,
        'size_buckets': buckets,
        'avg_turns_per_mb': avg_turns_per_mb,
        'sessions': sessions
    }

def main():
    parser = argparse.ArgumentParser(description='Analyze session audit CSV files')
    parser.add_argument('csv_files', nargs='+', help='CSV files to analyze')
    parser.add_argument('--compare', action='store_true', help='Compare multiple files')
    
    args = parser.parse_args()
    
    results = {}
    for filepath in args.csv_files:
        path = Path(filepath)
        if path.exists():
            print(f"\nAnalyzing {path.name}...")
            result = analyze_csv(path)
            if result:
                results[path.name] = result
                
                # Print statistics
                print(f"\nStatistics for {path.name}:")
                print(f"  Total sessions: {result['size_stats']['count']}")
                print(f"\nSize statistics (MB):")
                print(f"  Mean: {result['size_stats']['mean']:.2f}")
                print(f"  Median: {result['size_stats']['median']:.2f}")
                print(f"  Std Dev: {result['size_stats']['stdev']:.2f}")
                print(f"  Min: {result['size_stats']['min']:.2f}")
                print(f"  Max: {result['size_stats']['max']:.2f}")
                print(f"\nSize percentiles:")
                for p, v in result['size_stats']['percentiles'].items():
                    print(f"  {p}: {v:.2f} MB")
                
                print(f"\nSize distribution:")
                for bucket, count in result['size_buckets'].items():
                    pct = (count / result['size_stats']['count']) * 100
                    print(f"  {bucket}: {count} ({pct:.1f}%)")
                
                print(f"\nTurn statistics:")
                print(f"  Mean: {result['turn_stats']['mean']:.0f}")
                print(f"  Median: {result['turn_stats']['median']:.0f}")
                print(f"  Min-Max: {result['turn_stats']['min']}-{result['turn_stats']['max']}")
                print(f"  Avg turns/MB: {result['avg_turns_per_mb']:.0f}")
    
    # Compare if requested
    if args.compare and len(results) > 1:
        print("\n" + "="*50)
        print("COMPARISON")
        print("="*50)
        
        for name, result in results.items():
            print(f"\n{name}:")
            print(f"  Sessions: {result['size_stats']['count']}")
            print(f"  Avg size: {result['size_stats']['mean']:.2f} MB")
            print(f"  Max size: {result['size_stats']['max']:.2f} MB")
            print(f"  95th percentile: {result['size_stats']['percentiles']['95th']:.2f} MB")

if __name__ == '__main__':
    main()