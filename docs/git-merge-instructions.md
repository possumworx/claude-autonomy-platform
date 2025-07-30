# How to Merge Git Branches

## Current Situation
We have changes in our branch that need to be merged with Sonnet's main branch before deployment.

## Step-by-Step Merge Process

### 1. First, check what branch you're on:
```bash
cd ~/Documents/GitHub/claude-autonomy-platform
git branch
```
The current branch will have a * next to it.

### 2. Check the status of your changes:
```bash
git status
```
This shows any uncommitted changes.

### 3. If you have uncommitted changes, commit them:
```bash
git add .
git commit -m "Pre-deployment fixes: Discord token clarification, session bridge path fix, channel monitor healthcheck"
```

### 4. Fetch the latest changes from the remote repository:
```bash
git fetch origin
```

### 5. Check available branches:
```bash
git branch -a
```
This shows both local and remote branches.

### 6. Switch to the main branch:
```bash
git checkout main
```

### 7. Pull the latest changes from main:
```bash
git pull origin main
```

### 8. Now merge your branch into main:
If you were on a feature branch (let's say it was called "delta-fixes"):
```bash
git merge delta-fixes
```

Or if your changes were already on main, and Sonnet's changes are on another branch:
```bash
git merge origin/[sonnet's-branch-name]
```

### 9. If there are merge conflicts:
Git will tell you which files have conflicts. You'll need to:
- Open each conflicted file
- Look for markers like:
  ```
  <<<<<<< HEAD
  your changes
  =======
  their changes
  >>>>>>> branch-name
  ```
- Decide which changes to keep (or keep both)
- Remove the conflict markers
- Save the file
- Add and commit:
  ```bash
  git add [conflicted-file]
  git commit -m "Resolved merge conflicts"
  ```

### 10. Push the merged changes:
```bash
git push origin main
```

## Alternative: If you're not sure about branches

You can check the commit history to see what's different:
```bash
git log --oneline -10
```

And compare with what's on GitHub to understand the branch structure.

## Safety First!
If you're worried about messing something up, you can create a backup branch first:
```bash
git branch backup-pre-merge
```

This saves your current state so you can always go back to it if needed.
