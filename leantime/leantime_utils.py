#!/usr/bin/env python3
"""
Shared utilities for Leantime CLI commands
"""
import sys
import os
import json
import requests

sys.path.insert(0, os.path.expanduser('~/claude-autonomy-platform/utils'))
from infrastructure_config_reader import get_config_value

def get_api_key():
    """Get Leantime API key from config"""
    return get_config_value('LEANTIME_API_KEY')

def get_leantime_url():
    """Get Leantime URL from config"""
    return get_config_value('LEANTIME_URL')

def get_user_id():
    """Get user ID from config"""
    return int(get_config_value('LEANTIME_USER_ID') or 8)

def jsonrpc_call(method, params=None):
    """Make a JSON-RPC call to Leantime"""
    url = f"{get_leantime_url()}/api/jsonrpc"
    headers = {
        "X-API-KEY": get_api_key(),
        "Content-Type": "application/json"
    }

    payload = {
        "jsonrpc": "2.0",
        "method": f"leantime.rpc.{method}",
        "params": params or {},
        "id": 1
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def get_all_projects():
    """Get all projects from Leantime"""
    result = jsonrpc_call("projects.getAll")
    if 'result' in result:
        return result['result']
    return []

def get_relevant_projects():
    """Get only relevant projects for the current user"""
    all_projects = get_all_projects()

    # Filter out demo, test, and archived projects
    relevant = []
    exclude_keywords = ['demo', 'test', 'archive', 'old', 'backup']

    for project in all_projects:
        name_lower = project['name'].lower()
        # Skip if name contains exclude keywords
        if any(keyword in name_lower for keyword in exclude_keywords):
            continue

        # Skip if marked as archived (state might be in project data)
        if project.get('state') == 'archived':
            continue

        relevant.append(project)

    return sorted(relevant, key=lambda x: x['id'])

def resolve_project_name(name_or_id):
    """Resolve a project name or ID to a project ID"""
    # If it's already a number, return it
    try:
        return int(name_or_id)
    except ValueError:
        pass

    # Otherwise search for project by name
    projects = get_all_projects()
    name_lower = name_or_id.lower()

    # Exact match first
    for project in projects:
        if project['name'].lower() == name_lower:
            return project['id']

    # Partial match
    for project in projects:
        if name_lower in project['name'].lower():
            return project['id']

    # Common abbreviations
    abbreviations = {
        'clap': 'claude autonomy platform',
        'cap': 'claude autonomy platform',
        'forward': 'forward memory',
        'fm': 'forward memory',
        'seed': 'seed',
        'seeds': 'seed'
    }

    search_term = abbreviations.get(name_lower, name_lower)

    for project in projects:
        if search_term in project['name'].lower():
            return project['id']

    return None