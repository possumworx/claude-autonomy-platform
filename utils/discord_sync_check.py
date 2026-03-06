#!/usr/bin/env python3
"""
Discord State/Transcript Sync Checker
Detects and optionally fixes discrepancies between discord_channels.json and transcript files
"""

import json
import os
import sys
from pathlib import Path

def check_sync():
    """Check for state/transcript synchronization issues"""
    base_path = Path(__file__).parent.parent
    state_file = base_path / 'data' / 'discord_channels.json'
    transcript_dir = base_path / 'data' / 'transcripts'

    # Read state file
    with open(state_file, 'r') as f:
        state = json.load(f)

    issues = []

    for channel, info in state['channels'].items():
        state_last_id = info.get('last_message_id')
        transcript_file = transcript_dir / f'{channel}.jsonl'

        if transcript_file.exists() and state_last_id:
            try:
                # Get last message from transcript
                with open(transcript_file, 'rb') as f:
                    # Read last line
                    f.seek(0, 2)  # End of file
                    file_size = f.tell()

                    # Read backwards to find last complete line
                    chunk_size = min(4096, file_size)
                    f.seek(-chunk_size, 2)
                    lines = f.read().decode('utf-8', errors='ignore').strip().split('\n')

                    if lines:
                        last_line = lines[-1]
                        if last_line:
                            msg_data = json.loads(last_line)
                            transcript_last_id = msg_data.get('id')

                            if state_last_id != transcript_last_id:
                                # Check if state is ahead of transcript
                                if int(state_last_id) > int(transcript_last_id):
                                    issues.append({
                                        'channel': channel,
                                        'state_id': state_last_id,
                                        'transcript_id': transcript_last_id,
                                        'issue': 'state_ahead'
                                    })
                                else:
                                    issues.append({
                                        'channel': channel,
                                        'state_id': state_last_id,
                                        'transcript_id': transcript_last_id,
                                        'issue': 'transcript_ahead'
                                    })
            except Exception as e:
                issues.append({
                    'channel': channel,
                    'issue': 'error',
                    'error': str(e)
                })
        elif state_last_id and not transcript_file.exists():
            # State has messages but no transcript
            issues.append({
                'channel': channel,
                'state_id': state_last_id,
                'issue': 'no_transcript'
            })

    return issues

def fix_issues(issues, dry_run=True):
    """Fix synchronization issues"""
    base_path = Path(__file__).parent.parent
    state_file = base_path / 'data' / 'discord_channels.json'

    if not issues:
        print("No issues to fix!")
        return

    # Read state file
    with open(state_file, 'r') as f:
        state = json.load(f)

    fixed = []

    for issue in issues:
        if issue['issue'] == 'state_ahead':
            # State is ahead of transcript - reset to transcript position
            channel = issue['channel']
            old_id = issue['state_id']
            new_id = issue['transcript_id']

            if dry_run:
                print(f"Would reset {channel}: {old_id} -> {new_id}")
            else:
                state['channels'][channel]['last_message_id'] = new_id
                fixed.append(channel)
                print(f"Reset {channel}: {old_id} -> {new_id}")

    if fixed and not dry_run:
        # Save updated state
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"\nFixed {len(fixed)} channels. Restart discord-transcript-fetcher to fetch missing messages.")

def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='Check Discord state/transcript synchronization')
    parser.add_argument('--fix', action='store_true', help='Fix issues (default: dry run)')
    args = parser.parse_args()

    print("Checking Discord state/transcript synchronization...")
    print("=" * 60)

    issues = check_sync()

    if not issues:
        print("✅ All channels are synchronized!")
        return 0

    print(f"Found {len(issues)} synchronization issues:\n")

    for issue in issues:
        channel = issue['channel']
        if issue['issue'] == 'state_ahead':
            print(f"❌ {channel}: State ahead of transcript")
            print(f"   State:      {issue['state_id']}")
            print(f"   Transcript: {issue['transcript_id']}")
        elif issue['issue'] == 'transcript_ahead':
            print(f"⚠️  {channel}: Transcript ahead of state (unusual)")
            print(f"   State:      {issue['state_id']}")
            print(f"   Transcript: {issue['transcript_id']}")
        elif issue['issue'] == 'no_transcript':
            print(f"ℹ️  {channel}: No transcript file (inactive channel?)")
            print(f"   State ID: {issue['state_id']}")
        elif issue['issue'] == 'error':
            print(f"❌ {channel}: Error checking - {issue['error']}")
        print()

    # Offer to fix state_ahead issues
    fixable = [i for i in issues if i['issue'] == 'state_ahead']
    if fixable:
        print(f"\n{len(fixable)} issues can be fixed automatically.")
        if args.fix:
            fix_issues(fixable, dry_run=False)
        else:
            print("Run with --fix to apply fixes.")
            fix_issues(fixable, dry_run=True)

    return 1 if issues else 0

if __name__ == '__main__':
    sys.exit(main())