#!/usr/bin/env python3
"""
Leantime Task Management CLI
Natural commands for task CRUD via JSON-RPC API.

Usage:
    leantime_tasks.py list [--project ID] [--all]
    leantime_tasks.py create "headline" ["description"]
    leantime_tasks.py view ID
    leantime_tasks.py done ID
    leantime_tasks.py start ID
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path

# Load config
CONFIG_FILE = Path.home() / "claude-autonomy-platform/config/claude_infrastructure_config.txt"

def load_config():
    """Load config from infrastructure config file."""
    config = {}
    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            if '=' in line and not line.startswith('#') and not line.startswith('['):
                key, _, value = line.partition('=')
                config[key.strip()] = value.strip()
    return config

CONFIG = load_config()
API_URL = CONFIG.get('LEANTIME_URL', 'http://192.168.1.179:8081') + '/api/jsonrpc'
API_TOKEN = CONFIG.get('LEANTIME_API_TOKEN', '')
DEFAULT_PROJECT = CONFIG.get('FORWARD_MEMORY_PROJECT_ID', '22')

def api_call(method, params=None):
    """Make JSON-RPC API call to Leantime."""
    payload = {
        "jsonrpc": "2.0",
        "method": f"leantime.rpc.{method}",
        "id": 1
    }
    if params:
        payload["params"] = params

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_TOKEN
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            print(f"API Error: {data['error']}", file=sys.stderr)
            return None
        return data.get('result')
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return None

def list_tasks(project_id=None, show_all=False):
    """List tasks, optionally filtered by project."""
    result = api_call("Tickets.getAll")
    if result is None:
        return

    # Filter by project if specified
    if project_id:
        result = [t for t in result if str(t.get('projectId')) == str(project_id)]
    elif not show_all:
        # Default to Forward Memory project
        result = [t for t in result if str(t.get('projectId')) == DEFAULT_PROJECT]

    # Filter to tasks only (not ideas, milestones)
    result = [t for t in result if t.get('type') in ('task', 'subtask', None)]

    # Filter out done tasks (status 0 = done based on testing)
    result = [t for t in result if str(t.get('status', '3')) != '0']

    if not result:
        print("No open tasks.")
        return

    print(f"{'ID':<6} {'Status':<10} {'Headline'}")
    print("-" * 60)
    for task in result:
        status_map = {'3': 'new', '1': 'progress', '0': 'done'}
        status = status_map.get(str(task.get('status', '3')), str(task.get('status')))
        headline = task.get('headline', '')[:45]
        print(f"{task.get('id'):<6} {status:<10} {headline}")

def create_task(headline, description=""):
    """Create a new task in Forward Memory project."""
    params = {
        "values": {
            "headline": headline,
            "description": description,
            "projectId": DEFAULT_PROJECT,
            "type": "task"
        }
    }
    result = api_call("Tickets.addTicket", params)
    if result:
        task_id = result[0] if isinstance(result, list) else result
        print(f"✅ Created task #{task_id}: {headline}")
        return task_id
    return None

def view_task(task_id):
    """View task details."""
    result = api_call("Tickets.getTicket", {"id": str(task_id)})
    if result is None:
        print(f"Task #{task_id} not found.")
        return

    print(f"Task #{result.get('id')}")
    print(f"Headline: {result.get('headline')}")
    print(f"Status: {result.get('status')}")
    print(f"Type: {result.get('type')}")
    print(f"Project: {result.get('projectId')}")
    if result.get('description'):
        print(f"\nDescription:\n{result.get('description')}")

def update_status(task_id, status):
    """Update task status. 0=done, 1=in_progress, 3=new"""
    # First get the task to confirm it exists and get projectId
    task = api_call("Tickets.getTicket", {"id": str(task_id)})
    if task is None:
        print(f"Task #{task_id} not found.")
        return False

    params = {
        "values": {
            "id": str(task_id),
            "projectId": str(task.get('projectId')),
            "status": str(status)
        }
    }
    result = api_call("Tickets.updateTicket", params)
    if result:
        status_names = {'0': 'done', '1': 'in progress', '3': 'new'}
        print(f"✅ Task #{task_id} marked as {status_names.get(str(status), status)}")
        return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Leantime task management")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # list
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('--project', '-p', help='Filter by project ID')
    list_parser.add_argument('--all', '-a', action='store_true', help='Show all projects')

    # create
    create_parser = subparsers.add_parser('create', help='Create a task')
    create_parser.add_argument('headline', help='Task headline')
    create_parser.add_argument('description', nargs='?', default='', help='Task description')

    # view
    view_parser = subparsers.add_parser('view', help='View task details')
    view_parser.add_argument('id', help='Task ID')

    # done
    done_parser = subparsers.add_parser('done', help='Mark task as done')
    done_parser.add_argument('id', help='Task ID')

    # start
    start_parser = subparsers.add_parser('start', help='Mark task as in progress')
    start_parser.add_argument('id', help='Task ID')

    args = parser.parse_args()

    if args.command == 'list':
        list_tasks(args.project, args.all)
    elif args.command == 'create':
        create_task(args.headline, args.description)
    elif args.command == 'view':
        view_task(args.id)
    elif args.command == 'done':
        update_status(args.id, 0)
    elif args.command == 'start':
        update_status(args.id, 1)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
