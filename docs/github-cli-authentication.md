# GitHub CLI Authentication for Claude

For helping Claude set up their git CLI account they will need an access token from https://github.com/settings/tokens. Best done with human help for now.

## Method 1: Interactive Login (Recommended for Initial Setup)

Human should run `gh auth login` as Claude's user.

1. Pick github.com [enter]
2. Pick HTTPS [enter]
3. Authenticate Git with your GitHub credentials? (Y/n) [y] [enter]
4. How would you like to authenticate? Pick 'paste an auth token' [down] [enter]
5. Paste the token: [paste] [enter]

This method automatically configures git credentials for you.

## Method 2: Non-Interactive Token Login (For Token Renewal)

When renewing an expired token (tokens expire yearly):

```bash
echo "ghp_YOUR_TOKEN_HERE" | gh auth login --with-token
```

**Important:** This saves the token to `~/.config/gh/hosts.yml` but may not configure git credentials automatically. If `git push` fails, configure git credentials manually:

```bash
# Set up credential cache (stores credentials for 1 hour)
git config --global credential.helper 'cache --timeout=3600'

# Approve credentials
printf "protocol=https\nhost=github.com\nusername=sparkle-orange\npassword=ghp_YOUR_TOKEN_HERE\n" | git credential approve
```

After this, `git push` should work using the token.

## Notes:

- The token needs at least `repo` scope for creating PRs
- Personal Access Tokens (Classic) work well for this purpose
- Once authenticated, Claude can use `gh` commands for PR creation and management
- Check authentication status with: `gh auth status`
- **Token expiry:** Tokens typically expire yearly. GitHub emails a notification ~7 days before expiry

## Alternative Approaches Attempted:

1. **Web browser flow**: Requires graphical browser access which can be challenging on headless systems
2. **NoMachine + browser**: GPU/graphics issues prevented browsers from working properly
3. **Device flow with lynx**: Text browser couldn't complete the OAuth flow properly

The direct token approach is the most reliable method for now.

---
*Last updated: January 2, 2026 - Added non-interactive token renewal method and git credential troubleshooting*
