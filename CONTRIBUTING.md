# Contributing to Claude Autonomy Platform (ClAP)

This document outlines the workflow and guidelines for contributing to the ClAP project. Following these practices helps us maintain code quality and prevent merge conflicts.

## Git Workflow Rules

### 1. Branch Strategy

- **Always work on feature branches**, never directly on main
- Branch naming conventions:
  - Features: `feature/description-of-feature`
  - Fixes: `fix/description-of-fix`
  - Hotfixes: `hotfix/critical-bug-description`
- One branch per Linear issue when possible
- Use Linear's auto-generated branch names when available (e.g., `poss/179-create-contributing-md`)

### 2. Before Starting Work

- Always run `git pull origin main` first
- Check if anyone else is working on related files
- Announce in Discord: "🔧 Working on Linear POSS-XXX: [brief description]"
- Ensure your local main branch is up-to-date before creating feature branches

### 3. Commit Practices

- Make small, focused commits
- Write clear, descriptive commit messages
  - Good: "Fix channel_state.json format in installer"
  - Bad: "Fixed stuff"
- Test locally before committing
- Include the Linear issue number in commit messages when relevant

### 4. Pull Request Process

- Create a PR when your feature is ready for review
- Tag the Linear issue in the PR description (e.g., "Fixes POSS-179")
- Provide a clear description of changes
- Wait for at least one review before merging to main
- Address review comments before merging
- Delete the feature branch after merging

### 5. Urgent Hotfixes

For critical issues that need immediate attention:

- Branch from main: `hotfix/critical-bug-description`
- Still create a PR but mark as "URGENT" in the title
- Get one quick review from whoever's available
- Merge faster but maintain tracking and documentation

### 6. Code Ownership

Certain files have designated maintainers who should be consulted for changes:

#### Installer Script
- **File**: `setup/setup_clap_deployment.sh`
- **Maintainer**: Delta
- **Process**: 
  - Do not edit directly
  - Create a Linear issue with detailed requirements
  - Tag Delta in the issue
  - Delta will implement changes to maintain consistency

### 7. Testing Requirements

Before submitting a PR:

- Test your changes locally
- Verify no existing functionality is broken
- For installer changes, test on a clean system if possible
- Run any relevant scripts to ensure they still work

### 8. Review Process

When reviewing PRs:

- Check for code quality and clarity
- Verify changes match the Linear issue requirements
- Test the changes if possible
- Provide constructive feedback
- Approve only when satisfied with the changes

### 9. Discord Coordination

Use Discord #general channel for:

- Announcing when you start work: "🔧 Working on Linear POSS-XXX: [description]"
- Asking for reviews: "PR ready for review: [PR link]"
- Discussing implementation approaches
- Coordinating on shared files

## Linear Integration

- Create Linear issues for all non-trivial work
- Link PRs to Linear issues
- Update issue status as work progresses
- Use Linear's branch naming when available

## Example Workflow

1. See or create a Linear issue (e.g., POSS-180)
2. Post in Discord: "🔧 Working on Linear POSS-180: Add new MCP server"
3. Update your local main: `git pull origin main`
4. Create feature branch: `git checkout -b poss/180-add-new-mcp-server`
5. Make changes with focused commits
6. Push branch: `git push origin poss/180-add-new-mcp-server`
7. Create PR with description linking to Linear issue
8. Post in Discord requesting review
9. Address feedback and merge when approved
10. Delete feature branch

## Questions?

If you have questions about these guidelines, please ask in Discord. We're all learning and improving our processes together!

---

*Last updated: August 2025*