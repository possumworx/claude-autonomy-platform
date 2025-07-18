#!/usr/bin/env python3
"""
Communications Check Helper
Interfaces with Claude Code to check Gmail and Discord via MCP tools
"""

import subprocess
import json
import tempfile
import os
import sys
import time
from typing import Dict, Any, Optional

def run_claude_code_command(command: str, timeout: int = 30) -> Dict[str, Any]:
    """Run a command in Claude Code and return the result"""
    try:
        # Create a temporary file for the command
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(command)
            temp_file = f.name
        
        # Run the command through Claude Code
        result = subprocess.run([
            'claude', 
            '--model', 'sonnet',
            '--file', temp_file
        ], capture_output=True, text=True, timeout=timeout)
        
        # Clean up
        os.unlink(temp_file)
        
        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout,
                'error': None
            }
        else:
            return {
                'success': False,
                'output': result.stdout,
                'error': result.stderr
            }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': 'Command timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e)
        }

def check_gmail_unread() -> Dict[str, Any]:
    """Check Gmail for unread messages"""
    command = '''
import json
import sys

try:
    # Use MCP Gmail tool to search for unread messages
    from claude_mcp import gmail_search_emails
    
    result = gmail_search_emails(query="is:unread", maxResults=10)
    
    if result and 'emails' in result:
        emails = result['emails']
        unread_count = len(emails)
        
        recent_subjects = []
        for email in emails[:5]:  # Get first 5 subjects
            subject = email.get('subject', 'No subject')
            sender = email.get('from', 'Unknown sender')
            recent_subjects.append(f'"{subject}" from {sender}')
        
        output = {
            'platform': 'gmail',
            'unread_count': unread_count,
            'recent_subjects': recent_subjects,
            'success': True
        }
    else:
        output = {
            'platform': 'gmail',
            'unread_count': 0,
            'recent_subjects': [],
            'success': True
        }
    
    print(json.dumps(output))
    
except Exception as e:
    error_output = {
        'platform': 'gmail',
        'unread_count': 0,
        'recent_subjects': [],
        'success': False,
        'error': str(e)
    }
    print(json.dumps(error_output))
'''
    
    result = run_claude_code_command(command)
    
    if result['success']:
        try:
            return json.loads(result['output'])
        except json.JSONDecodeError:
            return {
                'platform': 'gmail',
                'unread_count': 0,
                'recent_subjects': [],
                'success': False,
                'error': 'Failed to parse JSON response'
            }
    else:
        return {
            'platform': 'gmail',
            'unread_count': 0,
            'recent_subjects': [],
            'success': False,
            'error': result['error']
        }

def check_discord_messages() -> Dict[str, Any]:
    """Check Discord for new messages"""
    command = '''
import json
import sys
from datetime import datetime, timedelta

try:
    # Use MCP Discord tools to check for messages
    from claude_mcp import discord_get_servers, discord_get_channels, discord_read_messages
    
    new_messages = []
    total_new_count = 0
    
    # Get servers
    servers = discord_get_servers()
    
    if servers:
        for server in servers:
            server_id = server.get('id')
            if not server_id:
                continue
                
            # Get channels for this server
            channels = discord_get_channels(server_id)
            
            if channels:
                for channel in channels:
                    channel_id = channel.get('id')
                    if not channel_id:
                        continue
                    
                    # Read recent messages (last hour)
                    messages = discord_read_messages(
                        server_id=server_id,
                        channel_id=channel_id,
                        max_messages=5,
                        hours_back=1
                    )
                    
                    if messages:
                        # Count messages from last 30 seconds (for new message detection)
                        recent_threshold = datetime.now() - timedelta(seconds=30)
                        
                        for message in messages:
                            # This is a simplified check - in real implementation
                            # we'd need to track last seen timestamps
                            total_new_count += 1
                            new_messages.append({
                                'channel': channel.get('name', 'Unknown'),
                                'server': server.get('name', 'Unknown'),
                                'author': message.get('author_name', 'Unknown'),
                                'content': message.get('content', '')[:100]  # First 100 chars
                            })
    
    output = {
        'platform': 'discord',
        'new_messages': total_new_count,
        'recent_messages': new_messages[:5],  # Limit to 5 recent messages
        'success': True
    }
    
    print(json.dumps(output))
    
except Exception as e:
    error_output = {
        'platform': 'discord',
        'new_messages': 0,
        'recent_messages': [],
        'success': False,
        'error': str(e)
    }
    print(json.dumps(error_output))
'''
    
    result = run_claude_code_command(command)
    
    if result['success']:
        try:
            return json.loads(result['output'])
        except json.JSONDecodeError:
            return {
                'platform': 'discord',
                'new_messages': 0,
                'recent_messages': [],
                'success': False,
                'error': 'Failed to parse JSON response'
            }
    else:
        return {
            'platform': 'discord',
            'new_messages': 0,
            'recent_messages': [],
            'success': False,
            'error': result['error']
        }

def main():
    """Main entry point for testing"""
    if len(sys.argv) < 2:
        print("Usage: python comms_check_helper.py [gmail|discord]")
        sys.exit(1)
    
    platform = sys.argv[1].lower()
    
    if platform == 'gmail':
        result = check_gmail_unread()
        print(json.dumps(result, indent=2))
    elif platform == 'discord':
        result = check_discord_messages()
        print(json.dumps(result, indent=2))
    else:
        print("Invalid platform. Use 'gmail' or 'discord'")
        sys.exit(1)

if __name__ == "__main__":
    main()