# GitHub CLI Authentication for Claude

For helping Claude set up their git CLI account they will need an access token from https://github.com/settings/tokens. Best done with human help for now.

## Steps:

Run `gh auth login`. 

1. Pick github.com [enter]
2. Pick HTTPS [enter]
3. Authenticate Git with your GitHub credentials? (Y/n) [y] [enter]
4. How would you like to authenticate? Pick 'paste an auth token' [down] [enter]
5. Paste the token: [paste] [enter]

## Notes:

- The token needs at least `repo` scope for creating PRs
- Personal Access Tokens (Classic) work well for this purpose
- Once authenticated, Claude can use `gh` commands for PR creation and management
- Check authentication status with: `gh auth status`

## Alternative Approaches Attempted:

1. **Web browser flow**: Requires graphical browser access which can be challenging on headless systems
2. **NoMachine + browser**: GPU/graphics issues prevented browsers from working properly
3. **Device flow with lynx**: Text browser couldn't complete the OAuth flow properly

The direct token approach is the most reliable method for now.

---
*Last updated: August 2025*