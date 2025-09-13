# Linear Advanced Usage Guide

## Overview

This guide covers advanced Linear CLI features for project management, bulk operations, and complex workflows.

## Table of Contents

1. [Project Creation and Management](#project-creation-and-management)
2. [Bulk Operations](#bulk-operations)
3. [Advanced Search and Filtering](#advanced-search-and-filtering)
4. [Workflow Automation](#workflow-automation)
5. [Team Collaboration](#team-collaboration)
6. [Troubleshooting](#troubleshooting)

---

## Project Creation and Management

### Creating Projects with Issues

The `linear/create_project_with_issues.py` command allows you to create a project and populate it with issues in one operation.

```bash
# Basic project creation
create-project "Project Name" team-id

# Create project with initial issues
create-project-with-issues "API Redesign" \
  --issues "Design new endpoints,Implement authentication,Write tests" \
  --team engineering

# Complex project setup with metadata
create-project-with-issues "Q1 Launch" \
  --issues "Frontend MVP:3,Backend API:5,Documentation:2,Testing:3" \
  --team product \
  --assignee me \
  --priority 1
```

### Project Templates

Create reusable project templates:

```bash
# Save current project structure as template
linear/save_template.py --project "API Redesign" --name api-template

# Create new project from template
linear/from_template.py api-template "API v2" --team engineering
```

---

## Bulk Operations

### Bulk Issue Creation

Create multiple issues efficiently:

```bash
# Create from list
bulk-create "Refactor auth,Add logging,Update docs" --project clap

# Create with priorities (format: title:priority)
bulk-create "Critical bug:1,Feature request:3,Documentation:4" \
  --project maintenance --assignee me

# Create from file
bulk-create --file issues.txt --project q1-goals
```

### Bulk Status Updates

Update multiple issues at once:

```bash
# Update by filter
bulk-update --status in-progress --filter "assignee:me status:todo"

# Update specific issues
bulk-update POSS-123,POSS-124,POSS-125 --status done

# Update with multiple properties
bulk-update --project clap --set "status:in-review assignee:amy priority:2"
```

### Bulk Assignment

Distribute work across team:

```bash
# Round-robin assignment
bulk-assign --project sprint-23 --team engineering --method round-robin

# Load-based assignment
bulk-assign --status todo --team product --method load-balance

# Skill-based assignment
bulk-assign --tag frontend --assignee "amy,delta" --method skills
```

---

## Advanced Search and Filtering

### Complex Queries

```bash
# Multi-condition search
search-issues --query "authentication" \
  --status "todo,in-progress" \
  --priority "1,2" \
  --assignee me

# Date-based filtering
search-issues --created-after "2024-01-01" \
  --updated-before "2024-02-01" \
  --status done

# Combined text and metadata search
search-issues "API" --project backend --tag "breaking-change" --limit 20
```

### Custom Filters

Save and reuse complex filters:

```bash
# Save filter
linear/save_filter.py --name "my-urgent" \
  --query "assignee:me priority:1 status:!done"

# Use saved filter
todo --filter my-urgent

# List saved filters
linear/list_filters.py
```

### Smart Queries

Use natural language queries:

```bash
# Natural language search
search "bugs assigned to me this week"
search "high priority features in clap project"
search "blocked issues without comments"
```

---

## Workflow Automation

### Issue Templates

Create issue templates for common tasks:

```bash
# Create bug template
linear/create_template.py bug \
  --title "[BUG] {description}" \
  --body "## Steps to Reproduce\n1. \n\n## Expected\n\n## Actual" \
  --labels "bug,needs-triage"

# Use template
add --template bug "Login fails with 2FA"
```

### Automated Workflows

Set up automation rules:

```bash
# Auto-assign based on labels
linear/add_automation.py \
  --trigger "label:frontend" \
  --action "assign:amy"

# Status progression
linear/add_automation.py \
  --trigger "status:in-review comment:approved" \
  --action "status:done"
```

### Recurring Tasks

Create recurring issues:

```bash
# Weekly standup prep
linear/recurring.py "Prepare standup notes" \
  --frequency weekly \
  --day monday \
  --assignee me \
  --project team-ops

# Monthly reports
linear/recurring.py "Generate monthly metrics" \
  --frequency monthly \
  --day 1 \
  --project reporting
```

---

## Team Collaboration

### Issue Dependencies

Manage complex task relationships:

```bash
# Create dependency
linear/add_dependency.py POSS-123 --blocks POSS-124

# View dependency tree
linear/dependencies.py POSS-123 --depth 3

# Find blocking issues
linear/blocking.py --assignee me
```

### Team Workload

Analyze and balance team capacity:

```bash
# Team workload overview
linear/workload.py --team engineering

# Individual capacity
linear/capacity.py amy --sprint current

# Rebalance work
linear/rebalance.py --team product --method even
```

### Collaborative Features

```bash
# Mention team members
comment POSS-123 "@amy what do you think about this approach?"

# Share issue groups
linear/share_view.py "Sprint 23 Frontend" \
  --filter "sprint:23 label:frontend" \
  --team engineering

# Batch commenting
bulk-comment --project clap --status in-review \
  "Ready for review, please take a look"
```

---

## Troubleshooting

### Common Issues

#### Authentication Problems

```bash
# Check auth status
linear/check_auth.py

# Refresh token
linear/refresh_auth.py

# Re-authenticate
linear/init
```

#### Sync Issues

```bash
# Force project sync
linear/sync_projects.py --force

# Clear cache
linear/clear_cache.py

# Rebuild state
linear/rebuild_state.py
```

#### Performance

```bash
# Optimize queries
linear/optimize.py --analyze

# Batch API calls
export LINEAR_BATCH_SIZE=50

# Enable caching
export LINEAR_CACHE_TTL=300
```

### Debugging

```bash
# Enable debug mode
export LINEAR_DEBUG=1

# View API calls
linear/debug.py --show-requests

# Test connection
linear/test_connection.py
```

### Error Recovery

```bash
# Rollback bulk operation
linear/rollback.py --operation bulk-update-1234

# Fix inconsistent state
linear/repair.py --check-all

# Export backup
linear/backup.py --format json --output backup.json
```

---

## Advanced Tips

### Performance Optimization

1. **Use batch operations** instead of individual commands
2. **Cache frequently accessed data** with `--cache` flag
3. **Limit API calls** with smart filtering
4. **Use webhooks** for real-time updates

### Integration Ideas

```bash
# Git integration
git commit -m "fix: Auth bug [LINEAR: POSS-123]"

# CI/CD integration
linear/update_from_ci.py --build-id 456 --status passed

# Slack notifications
linear/notify.py --channel engineering --filter "priority:1 status:new"
```

### Custom Commands

Create your own Linear commands:

```python
#!/usr/bin/env python3
# ~/.local/bin/my-linear-command

from linear_cli import LinearClient

client = LinearClient()
# Your custom logic here
```

---

## Quick Reference

### Most Useful Commands

```bash
# Quick add with everything
add "Fix auth bug" -p clap -P 1 -a me --start

# See everything assigned to you
todo --include-all

# Quick status update
update POSS-123 done

# Bulk operate on search results
search "old bugs" | bulk-update --status cancelled

# Project overview
project-stats clap --sprint current
```

### Keyboard Shortcuts

When using interactive mode (`linear/interactive.py`):

- `j/k` - Navigate issues
- `Enter` - View details
- `e` - Edit issue
- `s` - Change status
- `a` - Assign
- `c` - Comment
- `d` - Mark done
- `/` - Search
- `?` - Help

---

## Additional Resources

- [Linear API Documentation](https://developers.linear.app)
- [ClAP Architecture Guide](../context/clap_architecture.md)
- [Natural Commands Reference](../docs/natural-commands.md)

For questions or issues, check the [ClAP project board](linear://project/clap) or reach out on Discord.