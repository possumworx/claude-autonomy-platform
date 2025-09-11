# New Linear Commands Examples

## standup - Daily Standup Reports

Generate comprehensive standup reports showing your recent activity:

```bash
# Today's standup report
standup

# Output:
📅 Standup Report for Delta

✅ Completed:
  - POSS-123: Fix memory leak in service handler
  - CLAP-45: Update documentation for v0.5.0

🔄 In Progress:
  - POSS-124: Implement new authentication flow

📋 Today's Plan:
  - POSS-125: Review PR for database migration
  - POSS-126: Add unit tests for auth module

🚫 Blockers:
  - No blockers

# Look back 3 days for weekly standup
standup --days 3
```

## assign - Quick Issue Assignment

Quickly assign issues to team members:

```bash
# Assign to yourself
assign POSS-123 @me

# Assign to teammate
assign CLAP-45 @amy

# Unassign issue
assign POSS-456 @none

# Works with short form (uses recent project prefix)
assign 789 @me
```

## estimate - Story Point Estimation

Set story points for sprint planning:

```bash
# Small task (1 point)
estimate POSS-123 1

# Medium complexity (3 points)
estimate CLAP-45 3

# Large feature (8 points)
estimate POSS-789 8

# Remove estimate
estimate POSS-456 0
```

Valid points follow Fibonacci sequence: 1, 2, 3, 5, 8, 13, 21

## label - Label Management

Add or remove labels for better organization:

```bash
# Add multiple labels (default action)
label POSS-123 bug urgent backend

# Explicit add
label add CLAP-45 frontend performance

# Remove specific labels
label remove POSS-123 wontfix

# Short form removal
label rm POSS-789 duplicate

# Mix of operations
label add POSS-456 security
label rm POSS-456 low-priority
```

## move - Project Transfer

Move issues between projects:

```bash
# Move by project key
move POSS-123 CLAP

# Move by project name
move CLAP-45 "Pattern Recognition"

# Move with short form
move 789 POSS

# After move, issue gets new identifier
# POSS-123 becomes CLAP-567 (new ID assigned)
```

## Combined Workflow Examples

### Sprint Planning Session
```bash
# Review backlog
todo --status backlog --project CLAP

# Estimate tasks
estimate CLAP-101 3
estimate CLAP-102 5
estimate CLAP-103 8

# Assign sprint work
assign CLAP-101 @me
assign CLAP-102 @amy
assign CLAP-103 @team-lead

# Label sprint items
label CLAP-101 sprint-12 frontend
label CLAP-102 sprint-12 backend api
label CLAP-103 sprint-12 infrastructure
```

### Bug Triage
```bash
# Find unassigned bugs
inbox

# Quick triage
assign POSS-234 @me
label POSS-234 bug critical
estimate POSS-234 2

# Move to appropriate project
move POSS-234 CLAP

# Start working immediately
start CLAP-567  # New ID after move
```

### Daily Workflow
```bash
# Morning standup
standup

# Check assigned work
todo --status todo,in-progress

# Start new task
start POSS-456
comment POSS-456 "Beginning implementation of new feature"

# Update progress
update-status POSS-456 "In Progress"

# End of day
complete POSS-456 "Implemented and tested, PR #123"
standup  # Review day's work
```