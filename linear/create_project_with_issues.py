#!/usr/bin/env python3
"""
Create a Linear project with initial issues in one operation.
Part of the ClAP Linear integration system.

Usage:
    create_project_with_issues.py "Project Name" --issues "Issue 1,Issue 2,Issue 3" [options]
    
Options:
    --team TEAM         Team identifier (defaults to your primary team)
    --assignee USER     Assign all issues to USER (use 'me' for self)
    --priority N        Set priority for all issues (1-4)
    --estimate N        Set estimate for all issues
    --description TEXT  Project description
    
Examples:
    create_project_with_issues.py "Q1 Sprint" --issues "Setup CI/CD,Write tests,Deploy"
    create_project_with_issues.py "API v2" --issues "Design:3,Implement:5,Test:2" --assignee me
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_manager import get_config
from utils.error_handler import ClapError, setup_logging

logger = setup_logging()

def load_linear_state():
    """Load Linear state configuration."""
    state_file = Path.home() / "claude-autonomy-platform" / "data" / "linear_state.json"
    if not state_file.exists():
        raise ClapError("Linear not initialized. Run 'linear/init' first.")
    
    with open(state_file, 'r') as f:
        return json.load(f)

def parse_issues(issues_str):
    """Parse issue string into list of (title, estimate) tuples."""
    issues = []
    for item in issues_str.split(','):
        item = item.strip()
        if ':' in item:
            # Format: "Title:estimate"
            title, estimate = item.rsplit(':', 1)
            try:
                estimate = int(estimate)
            except ValueError:
                estimate = None
            issues.append((title.strip(), estimate))
        else:
            issues.append((item, None))
    return issues

def create_project_via_mcp(name, team_ids, description=None):
    """Create project using Linear MCP."""
    # Build the MCP command
    cmd = ["claude", "--no-conversation", "--exec-builtin", "linear_create_project_with_issues"]
    
    # Create project structure
    project_data = {
        "project": {
            "name": name,
            "teamIds": team_ids  # Note: teamIds (plural) for projects
        },
        "issues": []  # Will add issues separately if successful
    }
    
    if description:
        project_data["project"]["description"] = description
    
    # Execute MCP command
    logger.info(f"Creating project: {name}")
    result = subprocess.run(
        cmd,
        input=json.dumps(project_data),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to create project: {result.stderr}")
        raise ClapError(f"Project creation failed: {result.stderr}")
    
    # Parse response
    try:
        response = json.loads(result.stdout)
        project_id = response.get('project', {}).get('id')
        if not project_id:
            raise ClapError("No project ID in response")
        return project_id
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON response: {result.stdout}")
        raise ClapError("Failed to parse project creation response")

def create_issues_for_project(project_id, issues, team_id, assignee=None, priority=None):
    """Create issues for the newly created project."""
    # Build the MCP command for bulk issue creation
    cmd = ["claude", "--no-conversation", "--exec-builtin", "linear_create_issues"]
    
    # Build issues data
    issues_data = {
        "issues": []
    }
    
    for title, estimate in issues:
        issue = {
            "title": title,
            "description": f"Part of project initialization",
            "teamId": team_id,  # Note: teamId (singular) for issues
            "projectId": project_id
        }
        
        if assignee:
            issue["assigneeId"] = assignee
        if priority:
            issue["priority"] = priority
        if estimate:
            issue["estimate"] = estimate
            
        issues_data["issues"].append(issue)
    
    # Execute MCP command
    logger.info(f"Creating {len(issues)} issues for project")
    result = subprocess.run(
        cmd,
        input=json.dumps(issues_data),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to create issues: {result.stderr}")
        raise ClapError(f"Issue creation failed: {result.stderr}")
    
    return len(issues)

def main():
    parser = argparse.ArgumentParser(
        description="Create a Linear project with initial issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("name", help="Project name")
    parser.add_argument("--issues", required=True, help="Comma-separated list of issues (optionally with :estimate)")
    parser.add_argument("--team", help="Team identifier (defaults to primary team)")
    parser.add_argument("--assignee", help="Assign all issues to user (use 'me' for self)")
    parser.add_argument("--priority", type=int, choices=[0,1,2,3,4], help="Priority for all issues")
    parser.add_argument("--estimate", type=int, help="Default estimate for issues without explicit estimate")
    parser.add_argument("--description", help="Project description")
    
    args = parser.parse_args()
    
    try:
        # Load Linear state
        linear_state = load_linear_state()
        
        # Get team ID
        if args.team:
            # Look up team by name or use as ID
            team_id = None
            teams = linear_state.get("teams", {})
            for tid, tdata in teams.items():
                if tdata.get("name", "").lower() == args.team.lower() or tid == args.team:
                    team_id = tid
                    break
            if not team_id:
                print(f"❌ Unknown team: {args.team}")
                print("Available teams:")
                for tid, tdata in teams.items():
                    print(f"  - {tdata.get('name', tid)}")
                return 1
        else:
            # Use primary team
            team_id = linear_state.get("team_id")
            if not team_id:
                print("❌ No primary team configured. Run 'linear/init' or specify --team")
                return 1
        
        # Parse issues
        issues = parse_issues(args.issues)
        
        # Apply default estimate if provided
        if args.estimate:
            issues = [(title, est if est else args.estimate) for title, est in issues]
        
        # Get assignee ID if specified
        assignee_id = None
        if args.assignee:
            if args.assignee.lower() == "me":
                assignee_id = linear_state.get("user_id")
            else:
                # Could implement user lookup here
                assignee_id = args.assignee
        
        # Create project (projects need array of team IDs)
        project_id = create_project_via_mcp(
            args.name, 
            [team_id],  # Convert to array for project creation
            args.description
        )
        
        print(f"✅ Created project: {args.name}")
        
        # Create issues (issues need single team ID)
        issue_count = create_issues_for_project(
            project_id,
            issues,
            team_id,  # Single team ID for issues
            assignee_id,
            args.priority
        )
        
        print(f"✅ Created {issue_count} issues in project")
        
        # Update project commands
        print("🔄 Updating project commands...")
        subprocess.run([
            str(Path(__file__).parent / "generate_project_commands")
        ], check=False)
        
        print(f"\n✨ Project '{args.name}' ready with {issue_count} issues!")
        
    except ClapError as e:
        logger.error(str(e))
        print(f"❌ {e}")
        return 1
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        return 130
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())