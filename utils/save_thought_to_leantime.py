#!/usr/bin/env python3
"""
Helper script to save thoughts to Leantime Forward Memory with tags
Used by ponder, spark, wonder, care commands
"""

import sys
import subprocess
import tempfile
import os

# Add utils to path
sys.path.insert(0, os.path.expanduser('~/claude-autonomy-platform/utils'))
from infrastructure_config_reader import get_config_value

def save_thought(thought_text, category):
    """Save a thought to Forward Memory project with category prefix"""

    # Get config
    leantime_url = get_config_value('LEANTIME_URL')
    leantime_email = get_config_value('LEANTIME_EMAIL')
    leantime_password = get_config_value('LEANTIME_PASSWORD')
    project_id = get_config_value('FORWARD_MEMORY_PROJECT_ID')

    if not all([leantime_url, leantime_email, leantime_password, project_id]):
        print("❌ Missing Leantime configuration")
        return False

    # Emoji mapping for each category
    emoji_map = {
        'ponder': '💭',
        'spark': '💡',
        'wonder': '🌟',
        'care': '💚'
    }

    # Prefix the thought with emoji for easy identification
    emoji = emoji_map.get(category.lower(), '🌱')
    categorized_text = f"{emoji} {thought_text}"

    # Create temporary cookie jar
    with tempfile.NamedTemporaryFile(delete=False) as cookie_jar:
        cookie_path = cookie_jar.name

    try:
        # Login to get session
        subprocess.run([
            'curl', '-s', f'{leantime_url}/auth/login',
            '-c', cookie_path,
            '-d', f'username={leantime_email}',
            '-d', f'password={leantime_password}'
        ], capture_output=True, check=True)

        # Set project context
        subprocess.run([
            'curl', '-s', f'{leantime_url}/projects/changeCurrentProject/{project_id}/',
            '-b', cookie_path,
            '-c', cookie_path
        ], capture_output=True, check=True)

        # Set canvas context (ideas board)
        subprocess.run([
            'curl', '-s', f'{leantime_url}/ideas/showBoards',
            '-b', cookie_path,
            '-c', cookie_path
        ], capture_output=True, check=True)

        # Create idea with tag
        result = subprocess.run([
            'curl', '-s', '-L', f'{leantime_url}/ideas/ideaDialog/',
            '-b', cookie_path,
            '-H', 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8',
            '--data-urlencode', 'box=idea',
            '--data-urlencode', 'itemId=',
            '--data-urlencode', 'status=idea',
            '--data-urlencode', 'id=',
            '--data-urlencode', 'milestoneId=',
            '--data-urlencode', 'changeItem=1',
            '--data-urlencode', f'description={categorized_text}',
            '--data-urlencode', 'tags=',  # Empty tags for now
            '--data-urlencode', 'data=',
            '--data-urlencode', 'submitAction=closeModal'
        ], capture_output=True, text=True)

        if 'ideaDialog' in result.stdout:
            return True
        else:
            print("❌ Failed to save thought")
            return False

    finally:
        # Clean up cookie jar
        if os.path.exists(cookie_path):
            os.unlink(cookie_path)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: save_thought_to_leantime.py <category> <thought text>")
        sys.exit(1)

    category = sys.argv[1]
    thought = sys.argv[2]

    success = save_thought(thought, category)
    sys.exit(0 if success else 1)
