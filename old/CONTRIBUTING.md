# Contributing to Claude Autonomy Platform (ClAP)

## Branch Protection & Workflow

This repository uses GitHub branch protection on the `main` branch to maintain code quality and enable proper collaboration. All changes must go through pull requests.

### What happens when you try to push to main?

You'll see a helpful error message:
```
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: - Changes must be made through a pull request.
```

**Don't worry! Your work is safe!**

### Recovery Workflow

If you accidentally made changes on main:

#### Quick Recovery (using the "oops" command)
```bash
oops  # Creates a timestamped branch and pushes your changes
```

#### Manual Recovery
1. Create a new branch from your current state:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Push your branch:
   ```bash
   git push -u origin feature/your-feature-name
   ```

3. Create a pull request via GitHub or CLI:
   ```bash
   gh pr create --title "Your PR title" --body "Description of changes"
   ```

### If you already committed to main

```bash
# Create branch with your commits
git branch feature/your-feature
git checkout feature/your-feature
git push -u origin feature/your-feature

# Reset your local main to match remote
git checkout main
git reset --hard origin/main
```

## Workflow Best Practices

1. **Always create a feature branch** before making changes:
   ```bash
   git checkout -b feature/descriptive-name
   ```

2. **Keep your branch updated** with main:
   ```bash
   git pull origin main
   ```

3. **Use descriptive branch names**:
   - `feature/add-discord-integration`
   - `fix/memory-leak-in-timer`
   - `docs/update-readme`

4. **Write clear PR descriptions** explaining:
   - What changed
   - Why it changed
   - How to test it

## Emergency Situations

Repository administrators (Amy) can bypass branch protection in true emergencies. This should be rare and only for critical fixes.

## Questions?

Branch protection helps us maintain quality while enabling autonomous collaboration. The constraints guide us toward better practices!

---

*Remember: Branch protection is infrastructure as care - it helps us work together effectively while preventing accidental mistakes.*