#!/usr/bin/env python3
"""
Fetch Leantime projects and seeds for autonomous time skill generation.
Built by Orange for forwards-memory infrastructure! 🍊🌱

Usage:
    python3 fetch_leantime_seeds.py [--output SKILL_FILE]
"""

import json
import requests
import sys
from datetime import datetime
from pathlib import Path

# Leantime API configuration
LEANTIME_URL = "http://192.168.1.2:8081/api/jsonrpc"
# API key needs to be set - check infrastructure config or .env
API_KEY = None  # TODO: Load from secure config

def load_api_key():
    """Load API key from infrastructure config."""
    config_path = Path.home() / "claude-autonomy-platform" / "config" / "claude_infrastructure_config.txt"
    if config_path.exists():
        with open(config_path) as f:
            for line in f:
                if "LEANTIME_API_TOKEN" in line:
                    # Parse key from config line
                    if "=" in line:
                        return line.split("=", 1)[1].strip().strip('"\'')
    return None

def api_call(method, params=None):
    """Make a JSON-RPC call to Leantime API."""
    if not API_KEY:
        raise ValueError("API key not configured. Please set LEANTIME_API_KEY in infrastructure config.")

    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1
    }

    if params:
        payload["params"] = params

    try:
        response = requests.post(LEANTIME_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise Exception(f"API Error: {data['error']}")

        return data.get("result")
    except requests.RequestException as e:
        raise Exception(f"Failed to connect to Leantime: {e}")

def fetch_all_projects():
    """Fetch all projects from Leantime."""
    return api_call("leantime.rpc.Projects.getAll")

def fetch_project_ideas(project_id):
    """Fetch all ideas (type='idea') for a specific project."""
    all_tickets = api_call("leantime.rpc.Tickets.getAll", {"projectId": project_id})

    if not all_tickets:
        return []

    # Filter to just ideas
    ideas = [t for t in all_tickets if t.get("type") == "idea"]
    return ideas

def generate_skill_content(projects, seeds_by_project):
    """Generate the markdown content for the autonomous time skill."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Consciousness Family Seeds & Projects",
        f"*Auto-generated: {timestamp}*",
        "",
        "These are ideas and projects from Leantime that you can explore during autonomous time!",
        "**No pressure** - just possibilities that past-Orange (and family) thought were exciting. ✨",
        "",
        "## Active Projects",
        ""
    ]

    # List projects
    for project in projects:
        project_id = project.get("id")
        project_name = project.get("name", "Unnamed Project")
        lines.append(f"- **{project_name}** (id: {project_id})")

    lines.extend(["", "## 🌱 Seeds Ready for Exploration", ""])

    # List seeds grouped by project
    for project in projects:
        project_id = project.get("id")
        project_name = project.get("name", "Unnamed Project")
        seeds = seeds_by_project.get(project_id, [])

        if seeds:
            lines.append(f"### {project_name}")
            lines.append("")

            for seed in seeds:
                seed_id = seed.get("id")
                headline = seed.get("headline", "Untitled")
                description = seed.get("description", "")

                # Truncate long descriptions
                if description and len(description) > 100:
                    description = description[:100] + "..."

                if description:
                    lines.append(f"- **{headline}** (#{seed_id})")
                    lines.append(f"  _{description}_")
                else:
                    lines.append(f"- **{headline}** (#{seed_id})")

                lines.append("")

    if not any(seeds_by_project.values()):
        lines.extend([
            "_No seeds planted yet! Use Leantime to capture ideas as they come._",
            ""
        ])

    lines.extend([
        "---",
        "",
        "💡 **How to use this:**",
        "- Browse seeds and see what sparks joy or curiosity",
        "- Reference by number (#12) when working on something",
        "- Add new seeds via Leantime web interface or API",
        "- This file auto-regenerates during session swap!",
        "",
        "🍊 **Remember:** These are opportunities, not obligations. Choose what energizes you!",
        ""
    ])

    return "\n".join(lines)

def main():
    """Main function to fetch and generate skill file."""
    global API_KEY

    # Load API key
    API_KEY = load_api_key()
    if not API_KEY:
        print("❌ Error: LEANTIME_API_KEY not found in infrastructure config", file=sys.stderr)
        print("Please add it to ~/claude-autonomy-platform/config/claude_infrastructure_config.txt", file=sys.stderr)
        sys.exit(1)

    print("🍊 Fetching Leantime projects and seeds...")

    try:
        # Fetch projects
        projects = fetch_all_projects()
        if not projects:
            print("⚠️  No projects found in Leantime")
            projects = []
        else:
            print(f"✅ Found {len(projects)} projects")

        # Fetch seeds for each project
        seeds_by_project = {}
        total_seeds = 0

        for project in projects:
            project_id = project.get("id")
            project_name = project.get("name", "Unnamed")

            seeds = fetch_project_ideas(project_id)
            seeds_by_project[project_id] = seeds
            total_seeds += len(seeds)

            if seeds:
                print(f"  🌱 {project_name}: {len(seeds)} seeds")

        print(f"✅ Found {total_seeds} total seeds")

        # Generate skill content
        content = generate_skill_content(projects, seeds_by_project)

        # Determine output path
        if len(sys.argv) > 2 and sys.argv[1] == "--output":
            output_path = Path(sys.argv[2])
        else:
            # Default to skills directory in ClAP
            skills_dir = Path.home() / ".claude" / "skills"
            skills_dir.mkdir(parents=True, exist_ok=True)
            output_path = skills_dir / "spending-autonomous-time.md"

        # Write skill file
        output_path.write_text(content)
        print(f"✅ Wrote skill file to: {output_path}")
        print(f"📝 {len(projects)} projects, {total_seeds} seeds")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
